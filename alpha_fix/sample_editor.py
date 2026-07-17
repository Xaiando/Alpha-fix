from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

from .samples import SampleRegion, SampleShape, draw_sample_overlays


class SampleEditorDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        frame_bgr: np.ndarray,
        sample_regions: list[SampleRegion],
    ) -> None:
        super().__init__(parent)
        self.title("Guided Samples")
        self.transient(parent)
        self.grab_set()
        self.geometry("1280x860")
        self.minsize(980, 720)

        self.result: list[SampleRegion] | None = None
        self._frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        self._sample_regions = [region.normalized() for region in sample_regions]
        self._display_width, self._display_height = self._fit_display_size(self._frame_rgb.shape[1], self._frame_rgb.shape[0])
        self._photo: ImageTk.PhotoImage | None = None
        self._drag_start: tuple[int, int] | None = None
        self._preview_item: int | None = None
        self._image_item: int | None = None

        self.kind_var = tk.StringVar(value="background")
        self.shape_var = tk.StringVar(value="rectangle")
        self.summary_var = tk.StringVar()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container = ttk.Frame(self, padding=16)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=0)
        container.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            container,
            width=self._display_width,
            height=self._display_height,
            background="#1f1f1f",
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        side = ttk.Frame(container)
        side.grid(row=0, column=1, sticky="ns")
        side.columnconfigure(0, weight=1)

        ttk.Label(side, text="Sample Kind").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            side,
            textvariable=self.kind_var,
            values=("background", "keep"),
            state="readonly",
            width=18,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 12))

        ttk.Label(side, text="Shape").grid(row=2, column=0, sticky="w")
        ttk.Combobox(
            side,
            textvariable=self.shape_var,
            values=("rectangle", "ellipse"),
            state="readonly",
            width=18,
        ).grid(row=3, column=0, sticky="ew", pady=(4, 12))

        ttk.Label(
            side,
            text="Drag on the frame to create a region. Background regions are red, keep regions are green.",
            wraplength=240,
        ).grid(row=4, column=0, sticky="w", pady=(0, 12))

        self.region_list = tk.Listbox(side, width=36, height=18)
        self.region_list.grid(row=5, column=0, sticky="ew")

        ttk.Label(side, textvariable=self.summary_var, wraplength=240).grid(
            row=6,
            column=0,
            sticky="w",
            pady=(8, 12),
        )

        ttk.Button(side, text="Delete Selected", command=self._delete_selected).grid(
            row=7,
            column=0,
            sticky="ew",
            pady=(0, 8),
        )
        ttk.Button(side, text="Clear All", command=self._clear_all).grid(
            row=8,
            column=0,
            sticky="ew",
            pady=(0, 8),
        )
        ttk.Button(side, text="Done", command=self._finish).grid(
            row=9,
            column=0,
            sticky="ew",
            pady=(16, 8),
        )
        ttk.Button(side, text="Cancel", command=self._cancel).grid(
            row=10,
            column=0,
            sticky="ew",
        )

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._refresh()

    @staticmethod
    def _fit_display_size(width: int, height: int) -> tuple[int, int]:
        max_width = 900
        max_height = 720
        scale = min(max_width / max(width, 1), max_height / max(height, 1), 1.0)
        return max(1, int(round(width * scale))), max(1, int(round(height * scale)))

    def _refresh(self) -> None:
        image = draw_sample_overlays(self._frame_rgb.copy(), tuple(self._sample_regions))
        pil_image = Image.fromarray(image)
        pil_image = pil_image.resize((self._display_width, self._display_height), Image.Resampling.LANCZOS)
        self._photo = ImageTk.PhotoImage(pil_image)

        self.canvas.delete("all")
        self._image_item = self.canvas.create_image(0, 0, anchor="nw", image=self._photo)
        self._sync_region_list()

    def _sync_region_list(self) -> None:
        self.region_list.delete(0, tk.END)
        bg_count = 0
        keep_count = 0
        for idx, region in enumerate(self._sample_regions, start=1):
            if region.kind == "background":
                bg_count += 1
            else:
                keep_count += 1
            label = f"{idx:02d}. {region.kind} {region.shape} ({region.x0:.2f},{region.y0:.2f})-({region.x1:.2f},{region.y1:.2f})"
            self.region_list.insert(tk.END, label)
        self.summary_var.set(f"Total: {len(self._sample_regions)} | Background: {bg_count} | Keep: {keep_count}")

    def _image_to_normalized(self, x: int, y: int) -> tuple[float, float]:
        nx = float(np.clip(x / max(self._display_width - 1, 1), 0.0, 1.0))
        ny = float(np.clip(y / max(self._display_height - 1, 1), 0.0, 1.0))
        return nx, ny

    def _on_press(self, event: tk.Event[tk.Misc]) -> None:
        self._drag_start = (
            int(np.clip(event.x, 0, self._display_width - 1)),
            int(np.clip(event.y, 0, self._display_height - 1)),
        )
        if self._preview_item is not None:
            self.canvas.delete(self._preview_item)
            self._preview_item = None

    def _on_drag(self, event: tk.Event[tk.Misc]) -> None:
        if self._drag_start is None:
            return
        x0, y0 = self._drag_start
        x1 = int(np.clip(event.x, 0, self._display_width - 1))
        y1 = int(np.clip(event.y, 0, self._display_height - 1))
        if self._preview_item is not None:
            self.canvas.delete(self._preview_item)
        color = "#eb4c40" if self.kind_var.get() == "background" else "#38c46e"
        if self.shape_var.get() == "ellipse":
            self._preview_item = self.canvas.create_oval(x0, y0, x1, y1, outline=color, width=2, dash=(4, 2))
        else:
            self._preview_item = self.canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=2, dash=(4, 2))

    def _on_release(self, event: tk.Event[tk.Misc]) -> None:
        if self._drag_start is None:
            return
        x0, y0 = self._drag_start
        x1 = int(np.clip(event.x, 0, self._display_width - 1))
        y1 = int(np.clip(event.y, 0, self._display_height - 1))
        self._drag_start = None
        if self._preview_item is not None:
            self.canvas.delete(self._preview_item)
            self._preview_item = None
        if abs(x1 - x0) < 6 or abs(y1 - y0) < 6:
            return

        nx0, ny0 = self._image_to_normalized(x0, y0)
        nx1, ny1 = self._image_to_normalized(x1, y1)
        region = SampleRegion(
            kind=self.kind_var.get(),
            shape=self.shape_var.get(),
            x0=nx0,
            y0=ny0,
            x1=nx1,
            y1=ny1,
        ).normalized()
        self._sample_regions.append(region)
        self._refresh()

    def _delete_selected(self) -> None:
        selection = self.region_list.curselection()
        if not selection:
            return
        index = int(selection[0])
        del self._sample_regions[index]
        self._refresh()

    def _clear_all(self) -> None:
        self._sample_regions.clear()
        self._refresh()

    def _finish(self) -> None:
        self.result = list(self._sample_regions)
        self.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.destroy()
