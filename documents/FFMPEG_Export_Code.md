# FFMPEG Automated Export Engine

Below is the source code added to the Alpha Fix Sandbox to support automatic animated formats (Chroma MP4, ProRes 4444, WebM with Alpha). 

## 1. The Engine Logic (`alpha_fix_2/service.py`)

This logic runs immediately after the PNG sequence finishes rendering. It uses Python's `subprocess` module to pipe the generated frames directly into an FFMPEG command line string.

```python
import subprocess

if format != "png_sequence":
    output_name = source.stem + f"_{format}"
    
    if format == "chroma_mp4":
        output_file = target / f"{output_name}.mp4"
        # Split the video, draw a solid #00FF00 background matching its dimensions, and overlay the transparent frames
        cmd = [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", f"{rgba_dir.as_posix()}/frame_%05d.png",
            "-filter_complex", "[0:v]split[v1][v2];[v1]format=rgb24,drawbox=x=0:y=0:w=iw:h=ih:color=#00FF00:t=fill[bg];[bg][v2]overlay=format=rgb,format=yuv420p",
            "-c:v", "libx264", "-crf", "18", "-preset", "slow",
            str(output_file)
        ]
    elif format == "prores_4444":
        output_file = target / f"{output_name}.mov"
        cmd = [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", f"{rgba_dir.as_posix()}/frame_%05d.png",
            "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le",
            str(output_file)
        ]
    elif format == "webm_alpha":
        output_file = target / f"{output_name}.webm"
        cmd = [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", f"{rgba_dir.as_posix()}/frame_%05d.png",
            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
            str(output_file)
        ]
    else:
        cmd = []
        
    if cmd:
        if progress_callback is not None:
            progress_callback(frame_count, frame_count) # Max out progress bar during FFMPEG muxing
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFMPEG export failed for {format}. Error: {e}")
```

## 2. The GUI Updates (`alpha_fix_2/gui.py`)

These lines expose the export format selector directly in the Sandbox controls, making it easy to swap formats before exporting.

```python
# Add the format variable
self.export_format_var = tk.StringVar(value="chroma_mp4")

# Build the dropdown element in the UI
ttk.Label(controls, text="Export Format").grid(row=row, column=0, sticky="w", pady=(8, 2))
ttk.Combobox(
    controls,
    textvariable=self.export_format_var,
    values=("chroma_mp4", "prores_4444", "webm_alpha", "png_sequence"),
    state="readonly",
    width=18,
).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 2))
row += 1

# Updated start button
ttk.Button(controls, text="Start Processing", command=self._export).grid(
    row=row,
    column=0,
    columnspan=2,
    sticky="ew",
    pady=(8, 0),
)
```
