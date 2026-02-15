# Process Frame Animation Sheet Image

A small tool to process sprite sheet images: one or more large images containing **M×N** animation frames. It removes the background (solid-color or AI) and splits each sheet into individual frame images.

## Features

- **Background removal**: **Solid-color** (specify `--bg` + optional `--tolerance`) or **AI-based** with **rembg** (`--rembg`) for better results on complex backgrounds.
- **Grid split**: Cut the sheet into an **M×N** grid (rows × cols). Use one number for **N×N** (e.g. `--grid 4`) or two for **M×N** (e.g. `--grid 4 8`). Row-major order.
- **Batch + glob**: Pass multiple files or a **glob pattern** (e.g. `raw/*.png`); all are processed with the same options.
- **Preview**: Export as **GIF**, **APNG**, or **MP4** (`--preview-format`). Optional **`--preview-speed`** (playback speed multiplier) and **`--preview-checkerboard`** (checkerboard background to show transparency).
- **CLI**: Configurable input path(s) or pattern, grid, background mode, output directory, and preview options.

## Requirements

- **Python** 3.11+ (required for rembg; use project conda env).
- **Pillow** (PIL), **rembg** — install via `requirements.txt`, or use the project **conda** env (recommended).

## Setup: Conda environment (recommended)

The project uses a conda env so the same interpreter is used every time you run or open the project.

**First-time setup:**

```bash
conda env create -f environment.yml
```

**Activate the env** (do this in any terminal where you run the project, or rely on Cursor’s “Python: Select Interpreter” / terminal auto-activate):

```bash
conda activate process-frame-sheet
```

- **In Cursor**: the workspace is configured to use the `process-frame-sheet` conda env and to activate it in the integrated terminal. Just open the project and run as below.
- **Without activating**: you can run `./run.sh` instead of `python cli.py`; the script uses the conda env automatically.

## Usage

### Install dependencies (if not using conda)

```bash
pip install -r requirements.txt
```

### Command line

```bash
# Make sure the conda env is active (conda activate process-frame-sheet), then:

# Solid-color background (--bg required)
python cli.py sheet.png --grid 4 --bg "#FFFFFF" --output ./frames

# AI background removal (rembg) — no --bg needed, often better quality
python cli.py sheet.png --grid 4 --rembg --output ./frames

# M×N grid: 4 rows, 8 columns
python cli.py sheet.png --grid 4 8 --bg "#FFFFFF" --output ./frames

# With tolerance for anti-aliasing (0–255) when using --bg
python cli.py sheet.png --grid 4 --bg "#FFFFFF" --tolerance 10 --output ./frames

# Preview as APNG or MP4, with checkerboard to show transparency
python cli.py sheet.png --grid 4 --rembg -o ./frames --preview-format apng --preview-checkerboard
python cli.py sheet.png --grid 4 --rembg -o ./frames --preview-format mp4 --preview-speed 2

# Glob: all PNGs in raw/ (quote the pattern so the script expands it)
./run.sh "raw/*.png" --grid 4 -o ./frames --rembg

# Batch: same spec for multiple images
python cli.py Idle.png Run.png Attack.png --grid 4 --rembg --output ./frames

# Optional: also save the full sheet with transparent background
python cli.py sheet.png --grid 4 --rembg --output ./frames --save-full
```

Or use the wrapper (no need to activate the env first):

```bash
./run.sh "raw/*.png" --grid 4 -o ./frames --rembg
./run.sh Idle.png Run.png --grid 4 --bg "#FFFFFF" --output ./frames
```

Output layout: for each input, a **subfolder named after the input image** (no extension) is created under the output directory. Frames are named **`原图名_序列号.png`** (e.g. `Idle_1.png`, `Idle_2.png`, …) in **row-major** order. A **preview** file is also written there (e.g. `Idle.gif`, `Idle.apng`, or `Idle.mp4` depending on `--preview-format`).

- **`--preview-format`**: `gif` (default), `apng`, or `mp4`. APNG/MP4 require `pip install apng imageio imageio-ffmpeg`.
- **`--preview-speed`**: Speed multiplier (e.g. `2` = twice as fast). Effective duration per frame = `--gif-duration` / `--preview-speed`.
- **`--preview-checkerboard`**: Composite the preview on a light gray/white checkerboard so transparent areas are visible.
- **`--gif-duration`**: Base duration per frame in ms (default 100). First run with `--rembg` may be slow (model download).

## Project structure

```text
ProcessFrameAnimationSheetImage/
├── README.md
├── README.zh.md
├── .cursor/
│   └── rules/
│       └── process-sprite-sheet.mdc
├── .vscode/
│   └── settings.json      # Python: process-frame-sheet conda env, terminal auto-activate
├── environment.yml       # Conda env definition (process-frame-sheet)
├── requirements.txt
├── run.sh                 # Run CLI with conda env (./run.sh ...)
├── src/
│   └── process_sheet.py   # Core: make transparent + grid split
└── cli.py                 # Command-line entry
```

- **Input**: File path(s) or **glob pattern** (e.g. `raw/*.png`). With a pattern, quote it in the shell: `./run.sh "raw/*.png" --grid 4 -o ./frames`.
- **Output**: Base directory given by `--output` (e.g. `./frames`). For input `Idle.png`, frames and preview go to `frames/Idle/`: `Idle_1.png` … `Idle_N.png`, plus `Idle.gif`/`Idle.apng`/`Idle.mp4`; optional full sheet as `Idle_sheet.png` with `--save-full`.

## Notes / Considerations

- **Background**: Use **`--rembg`** for AI-based removal (recommended when the background isn’t a uniform color), or **`--bg HEX`** for solid-color removal with optional **`--tolerance`**.
- **Preview**: Use **`--preview-format apng`** or **`mp4`** for alternative previews; **`--preview-checkerboard`** adds a checkerboard behind transparent areas; **`--preview-speed 2`** doubles playback speed.
- **Glob**: Input can be a glob pattern (e.g. `raw/*.png`). Quote it so the script receives the pattern and expands it: `./run.sh "raw/*.png" --grid 4 -o ./frames`.
- **Grid**: one number `--grid N` → N×N; two numbers `--grid R C` → R rows × C cols. Frames are emitted in **row-major** order.
- **Output format** is PNG to preserve the alpha channel. First run with `--rembg` downloads a model; large batches may use significant memory.
