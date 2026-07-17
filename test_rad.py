import cv2
import numpy as np
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.pipeline import AlphaFix2Processor

def test_subject():
    video_path = r"C:\Users\Kaged\Documents\Projects\Overlay\Finished overlay\Animation\Hailuo_Video_Seamless looping animation_512532828527190022_webm_alpha.webm"
    print(f"Reading from video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Failed to open video")
        return
        
    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        print("Failed to read first frame")
        return
        
    print(f"Loaded frame of size {frame.shape}")
    
    cfg = AlphaFix2Config(mode="subject")
    proc = AlphaFix2Processor(cfg)
    
    res = proc.process_frame(frame)
    
    alpha = res.alpha
    alpha_u8 = np.clip(alpha * 255.0, 0.0, 255.0).astype(np.uint8)
    
    out_path = r"C:\Users\Kaged\.gemini\antigravity\brain\9c45762a-e3b1-49b7-8965-96fb787a6613\artifacts\test_subject.png"
    cv2.imwrite(out_path, alpha_u8)
    print(f"Saved {out_path}")
    
    # Save anchor as well
    anchor_out = r"C:\Users\Kaged\.gemini\antigravity\brain\9c45762a-e3b1-49b7-8965-96fb787a6613\artifacts\test_subject_anchor.png"
    anchor_u8 = np.clip(res.alpha0 * 255.0, 0.0, 255.0).astype(np.uint8)
    cv2.imwrite(anchor_out, anchor_u8)
    
    # Save original frame for visual context
    orig_out = r"C:\Users\Kaged\.gemini\antigravity\brain\9c45762a-e3b1-49b7-8965-96fb787a6613\artifacts\test_subject_orig.png"
    cv2.imwrite(orig_out, frame)

if __name__ == "__main__":
    test_subject()
