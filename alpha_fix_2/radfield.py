from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import cv2
import numpy as np

from alpha_fix.samples import SampleRegion, build_sample_mask
from .config import AlphaFix2Config

@dataclass(slots=True)
class RadiationSeed:
    region: SampleRegion
    role: Literal["background", "keep"]
    mean_lab: np.ndarray        # shape (3,)
    variance_lab: np.ndarray    # shape (3,)
    sigma_d: float
    sigma_c: float
    confidence: float

@dataclass(slots=True)
class RadiationState:
    b_field: np.ndarray         # shape (H, W)
    k_field: np.ndarray         # shape (H, W)
    alpha_base: np.ndarray      # shape (H, W)
    frame1_lab: np.ndarray      # shape (H, W, 3)
    seeds: list[RadiationSeed]
    gamma: float
    tau_delta: float
    lambda_t: float


def compute_sample_radiation(frame_bgr: np.ndarray, config: AlphaFix2Config) -> tuple[np.ndarray, np.ndarray]:
    """Returns (b_field, k_field) radiating from the sample regions."""
    height, width = frame_bgr.shape[:2]
    lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    
    b_field = np.zeros((height, width), dtype=np.float32)
    k_field = np.zeros((height, width), dtype=np.float32)
    
    for region in config.sample_regions:
        mask = build_sample_mask((height, width), (region,), region.kind)
        mask_bool = mask > 0.5
        if not np.any(mask_bool):
            continue
            
        pixels_lab = lab[mask_bool]
        mean_lab = np.mean(pixels_lab, axis=0)
        
        dist_img = (mask > 0.5).astype(np.uint8)
        d_s = cv2.distanceTransform(1 - dist_img, cv2.DIST_L2, 3)
        delta_c = np.linalg.norm(lab - mean_lab, axis=-1)
        
        f_s = np.exp(-(d_s**2) / (2 * max(config.srf_sigma_d, 1e-6)**2)) * np.exp(-(delta_c**2) / (2 * max(config.srf_sigma_c, 1e-6)**2))
        f_s = f_s.astype(np.float32)
        
        if region.kind == "background":
            b_field = np.maximum(b_field, f_s)
        else:
            k_field = np.maximum(k_field, f_s)
            
    return b_field, k_field


def init_radiation_state(frame_bgr: np.ndarray, config: AlphaFix2Config) -> RadiationState:
    height, width = frame_bgr.shape[:2]
    lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    
    seeds: list[RadiationSeed] = []
    
    for region in config.sample_regions:
        mask = build_sample_mask((height, width), (region,), region.kind)
        mask_bool = mask > 0.5
        if not np.any(mask_bool):
            continue
            
        pixels_lab = lab[mask_bool]
        mean_lab = np.mean(pixels_lab, axis=0)
        var_lab = np.var(pixels_lab, axis=0)
        
        seed = RadiationSeed(
            region=region,
            role=region.kind, # "background" or "keep"
            mean_lab=mean_lab,
            variance_lab=var_lab,
            sigma_d=config.srf_sigma_d,
            sigma_c=config.srf_sigma_c,
            confidence=1.0,
        )
        seeds.append(seed)
        
    state = RadiationState(
        b_field=np.zeros((height, width), dtype=np.float32),
        k_field=np.zeros((height, width), dtype=np.float32),
        alpha_base=np.zeros((height, width), dtype=np.float32),
        frame1_lab=lab.copy(),
        seeds=seeds,
        gamma=config.srf_gamma,
        tau_delta=config.srf_tau_delta,
        lambda_t=config.srf_lambda_t,
    )
    
    return _compute_fields(lab, state, config)

def update_radiation_state(frame_bgr: np.ndarray, state: RadiationState, config: AlphaFix2Config) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    height, width = frame_bgr.shape[:2]
    lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    
    # Phase 2: Temporal Update (not strictly needed for Phase 1, but structure is here)
    # For phase 1, we just recompute or rely on single frame. 
    # But let's do full single frame recompute for now if it's not a sequence?
    # Actually, the spec says "reuse frame-1 alpha everywhere that change is below threshold"
    
    diff = np.linalg.norm(lab - state.frame1_lab, axis=-1)
    change_mask = diff > state.tau_delta
    
    if not np.any(change_mask):
        return state.alpha_base, _build_debug_views(state)
        
    # Recompute fields only where changed? The document says:
    # "recompute local field influence using the original seed color memories"
    # To keep it simple and mathematically identical to the spec, we can just compute the new spatial field for the whole frame,
    # then blend using change_mask.
    
    new_state = RadiationState(
        b_field=np.zeros((height, width), dtype=np.float32),
        k_field=np.zeros((height, width), dtype=np.float32),
        alpha_base=np.zeros((height, width), dtype=np.float32),
        frame1_lab=state.frame1_lab,
        seeds=state.seeds,
        gamma=state.gamma,
        tau_delta=state.tau_delta,
        lambda_t=state.lambda_t,
    )
    
    new_state = _compute_fields(lab, new_state, config)
    
    # Blend
    alpha_t = state.alpha_base.copy()
    # To prevent blur/ghosting of the background behind moving characters,
    # the alpha is updated immediately (drawn at every frame) for changed pixels.
    alpha_t[change_mask] = new_state.alpha_base[change_mask]
    
    # We update the state's fields for debug views
    state.b_field = new_state.b_field
    state.k_field = new_state.k_field
    state.alpha_base = alpha_t
    
    return alpha_t, _build_debug_views(state)

def _compute_fields(lab: np.ndarray, state: RadiationState, config: AlphaFix2Config) -> RadiationState:
    height, width = lab.shape[:2]
    
    b_field = np.zeros((height, width), dtype=np.float32)
    k_field = np.zeros((height, width), dtype=np.float32)
    
    for seed in state.seeds:
        mask = build_sample_mask((height, width), (seed.region,), seed.role)
        # distanceTransform needs a binary uint8 image.
        # d_out (background): distance OUTWARD from the seed boundary.
        # Inside the seed, distance is 0. Outside, distance increases.
        # So we want the distance to the mask.
        
        # For both background and keep, we measure distance OUTWARD from the seed boundary.
        # Inside the seed, distance is 0. Outside, distance increases.
        dist_img = (mask > 0.5).astype(np.uint8)
        d_s = cv2.distanceTransform(1 - dist_img, cv2.DIST_L2, 3)
            
        delta_c = np.linalg.norm(lab - seed.mean_lab, axis=-1)
        
        f_s = np.exp(-(d_s**2) / (2 * max(seed.sigma_d, 1e-6)**2)) * np.exp(-(delta_c**2) / (2 * max(seed.sigma_c, 1e-6)**2))
        f_s = f_s.astype(np.float32) * seed.confidence
        
        if seed.role == "background":
            b_field = np.maximum(b_field, f_s)
        else:
            k_field = np.maximum(k_field, f_s)
            
    # Alpha derivation
    eps = 1e-4
    if len([s for s in state.seeds if s.role == "keep"]) == 0:
        alpha_base = 1.0 - np.power(b_field, state.gamma)
    elif len([s for s in state.seeds if s.role == "background"]) == 0:
        alpha_base = np.power(k_field, state.gamma)
    else:
        alpha_base = np.power((k_field + eps) / (k_field + b_field + eps), state.gamma)
        
    alpha_base = np.clip(alpha_base, 0.0, 1.0)
    
    # Edge-aware sharpening (optional Phase 1)
    # gray = lab[:,:,0] / 255.0 # LAB L channel is 0-255 in OpenCV uint8, but we are float32. L is 0-100 usually.
    # lap = np.abs(cv2.Laplacian(lab[:,:,0], cv2.CV_32F))
    # ...
    
    state.b_field = b_field
    state.k_field = k_field
    state.alpha_base = alpha_base
    return state

def _build_debug_views(state: RadiationState) -> dict[str, np.ndarray]:
    # Field Map: Red = background-dominated, Green = keep-dominated, Yellow = contested
    h, w = state.alpha_base.shape
    field_map = np.zeros((h, w, 3), dtype=np.float32)
    field_map[:,:,2] = state.b_field # Red (Background)
    field_map[:,:,1] = state.k_field # Green (Keep)
    
    return {
        "b_field": state.b_field,
        "k_field": state.k_field,
        "field_map": field_map,
    }
