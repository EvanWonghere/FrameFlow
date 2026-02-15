#!/usr/bin/env python3
"""
Command-line entry for sprite sheet processing: transparent background + M×N split.
Supports batch and glob patterns (e.g. raw/*.png). Background: color-based or rembg.
"""
import argparse
import sys
from pathlib import Path

# Unbuffered output so progress and logs show in real time (e.g. when run via conda run)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

from PIL import Image
from tqdm import tqdm

from src.process_sheet import (
    frames_to_gif,
    make_background_transparent,
    remove_background_rembg,
    split_into_frames,
)


def parse_hex_color(s: str) -> tuple[int, int, int]:
    """Parse '#RRGGBB' or 'RRGGBB' to (r, g, b)."""
    s = s.lstrip("#")
    if len(s) != 6:
        raise ValueError(f"Invalid hex color: {s}")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def expand_inputs(paths: list[Path]) -> list[Path]:
    """Expand glob patterns (*, ?, []) in paths. Concrete file paths are kept as-is."""
    result: list[Path] = []
    for p in paths:
        if p.is_file():
            result.append(p)
        elif "*" in p.name or "?" in p.name or "[" in p.name:
            matches = sorted(p.parent.glob(p.name))
            if not matches:
                raise SystemExit(f"No files match pattern: {p}")
            result.extend(matches)
        else:
            result.append(p)
    return result


def process_one(
    input_path: Path,
    output_base: Path,
    rows: int,
    cols: int,
    use_rembg: bool,
    bg_rgb: tuple[int, int, int] | None,
    tolerance: int,
    save_full: bool,
    gif_duration_ms: int,
) -> None:
    """Process a single sprite sheet: transparent, split, save frames + GIF."""
    stem = input_path.stem
    frame_dir = output_base / stem
    # Ensure we never write outside output_base (path traversal safety)
    try:
        frame_dir.resolve().relative_to(output_base.resolve())
    except ValueError:
        raise ValueError(f"Output path would escape output dir: {frame_dir}")
    frame_dir.mkdir(parents=True, exist_ok=True)

    img = Image.open(input_path).convert("RGB")

    if use_rembg:
        # rembg works per subject: split first, then remove bg on each frame.
        # Running rembg on the full sheet treats the whole grid as one scene and fails.
        raw_frames = split_into_frames(img, rows, cols)
        frames = [
            remove_background_rembg(f)
            for f in tqdm(
                raw_frames,
                desc=f"  {stem} rembg",
                unit="frame",
                leave=False,
            )
        ]
        if save_full:
            fw, fh = frames[0].size
            full = Image.new("RGBA", (fw * cols, fh * rows), (0, 0, 0, 0))
            for i, frame in enumerate(frames):
                row, col = i // cols, i % cols
                full.paste(frame, (col * fw, row * fh))
            full_path = frame_dir / f"{stem}_sheet.png"
            full.save(full_path, "PNG")
            print(f"  Saved full sheet: {full_path}")
    else:
        if bg_rgb is None:
            raise ValueError("--bg is required when not using --rembg")
        img = make_background_transparent(img, bg_rgb, tolerance)
        if save_full:
            full_path = frame_dir / f"{stem}_sheet.png"
            img.save(full_path, "PNG")
            print(f"  Saved full sheet: {full_path}")
        frames = split_into_frames(img, rows, cols)

    for i, frame in enumerate(frames):
        path = frame_dir / f"{stem}_{i + 1}.png"
        frame.save(path, "PNG")
    print(f"  Saved {len(frames)} frames to {frame_dir} ({stem}_1 .. {stem}_{len(frames)}).")

    gif_path = frame_dir / f"{stem}.gif"
    frames_to_gif(frames, gif_path, duration_ms=gif_duration_ms)
    print(f"  Saved preview GIF: {gif_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process sprite sheet(s): make background transparent and split into M×N frames. Batch: same grid/bg for all inputs."
    )
    parser.add_argument(
        "input",
        type=Path,
        nargs="+",
        help="Input image path(s) or glob (e.g. raw/*.png); batch = same spec for all.",
    )
    parser.add_argument(
        "--grid",
        "-g",
        type=int,
        nargs="+",
        required=True,
        metavar=("N", "M"),
        help="Grid: one number for N×N, or two for rows×cols (e.g. 4 8).",
    )
    parser.add_argument(
        "--rembg",
        action="store_true",
        help="Use rembg (AI) to remove background instead of solid-color removal.",
    )
    parser.add_argument(
        "--bg",
        type=str,
        default=None,
        metavar="HEX",
        help='Background color as hex when not using --rembg (e.g. "#FFFFFF"). Required without --rembg.',
    )
    parser.add_argument(
        "--tolerance",
        "-t",
        type=int,
        default=0,
        metavar="T",
        help="Color tolerance for transparency (0-255), default 0",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("./frames"),
        metavar="DIR",
        help="Output directory for frame PNGs, default ./frames",
    )
    parser.add_argument(
        "--save-full",
        action="store_true",
        help="Also save the full sheet with transparent background",
    )
    parser.add_argument(
        "--gif-duration",
        type=int,
        default=100,
        metavar="MS",
        help="GIF duration per frame in ms, default 100",
    )
    args = parser.parse_args()

    if len(args.grid) == 1:
        rows = cols = args.grid[0]
    elif len(args.grid) == 2:
        rows, cols = args.grid[0], args.grid[1]
    else:
        raise SystemExit("--grid must be one number (N×N) or two numbers (rows cols).")

    if rows < 1 or cols < 1:
        raise SystemExit("Grid rows and cols must be >= 1.")

    inputs = expand_inputs(args.input)
    missing = [p for p in inputs if not p.is_file()]
    if missing:
        raise SystemExit(f"Input file(s) not found: {missing}")

    if not args.rembg and args.bg is None:
        raise SystemExit("Either --rembg or --bg HEX is required.")

    bg_rgb: tuple[int, int, int] | None = None
    if args.bg is not None:
        try:
            bg_rgb = parse_hex_color(args.bg)
        except ValueError as e:
            raise SystemExit(e)

    if not (0 <= args.tolerance <= 255):
        raise SystemExit("Tolerance must be between 0 and 255.")

    args.output.mkdir(parents=True, exist_ok=True)

    iterator = (
        tqdm(enumerate(inputs), total=len(inputs), desc="Sheets", unit="sheet")
        if len(inputs) > 1
        else enumerate(inputs)
    )
    for idx, input_path in iterator:
        if len(inputs) > 1:
            tqdm.write(f"[{idx + 1}/{len(inputs)}] {input_path.name}")
        process_one(
            input_path,
            args.output,
            rows,
            cols,
            args.rembg,
            bg_rgb,
            args.tolerance,
            args.save_full,
            args.gif_duration,
        )


if __name__ == "__main__":
    main()
