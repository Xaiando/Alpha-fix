import cv2
import numpy as np
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.pipeline import AlphaFix2Processor

def compare():
    video_path = r"C:\Users\Kaged\Documents\Projects\Overlay\Finished overlay\Animation\Hailuo_Video_Seamless looping animation_512532828527190022_webm_alpha.webm"
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Failed to read frame")
        return

    # NEW PIPELINE WITH ALL OPTIMIZATIONS (Dominant Cluster + Selective Hole Filling)
    cfg = AlphaFix2Config(mode="subject", subject_low=0.8, subject_high=2.5, anchor_blur_sigma=1.0)
    proc = AlphaFix2Processor(cfg)
    
    # Run the full processing pipeline!
    res = proc.process_frame(frame)
    alpha = res.alpha
    
    # Let's save a full high-resolution image of the alpha channel side-by-side with original frame
    h, w = frame.shape[:2]
    scale = 0.5
    h_s, w_s = int(h * scale), int(w * scale)
    
    frame_s = cv2.resize(frame, (w_s, h_s))
    alpha_s = cv2.resize((alpha * 255).astype(np.uint8), (w_s, h_s))
    alpha_3ch = cv2.cvtColor(alpha_s, cv2.COLOR_GRAY2BGR)
    
    cv2.putText(frame_s, "Original Frame", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(alpha_3ch, "Fitted Dominant + Selective Hair Gaps", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    combined = np.hstack([frame_s, alpha_3ch])
    
    out_path = r"C:\Users\Kaged\.gemini\antigravity\brain\9c45762a-e3b1-49b7-8965-96fb787a6613\artifacts\compare_subject.png"
    cv2.imwrite(out_path, combined)
    print(f"Comparison saved to {out_path}")

if __name__ == "__main__":
    compare()
