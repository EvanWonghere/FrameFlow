"""
Core logic: make solid background transparent and split sheet into M×N frames.
Single responsibility: one concern per function; no CLI here.
"""
from __future__ import annotations

from pathlib import Path
from typing import cast

from PIL import Image


def remove_background_rembg(image: Image.Image) -> Image.Image:
    """
    Remove background using rembg (AI-based). Returns RGBA with transparent background.
    Requires: pip install rembg (Python 3.11+).
    """
    try:
        from rembg import remove as rembg_remove
    except ImportError as e:
        raise RuntimeError(
            "rembg is not installed. Install with: pip install rembg  (requires Python 3.11+)"
        ) from e
    out = rembg_remove(image)
    return out.convert("RGBA") if out.mode != "RGBA" else out


def make_background_transparent(
    image: Image.Image,
    bg_rgb: tuple[int, int, int],
    tolerance: int = 0,
) -> Image.Image:
    """
    Make pixels close to bg_rgb transparent by setting their alpha to 0.
    Only alpha is changed; RGB is unchanged for smooth edges.
    """
    img = image.convert("RGBA")
    r0, g0, b0 = bg_rgb
    data = img.getdata()
    new_data: list[tuple[int, int, int, int]] = []
    for raw in data:
        item = cast(tuple[int, int, int, int], raw)
        r, g, b, a = item
        if (
            abs(r - r0) <= tolerance
            and abs(g - g0) <= tolerance
            and abs(b - b0) <= tolerance
        ):
            new_data.append((r, g, b, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    return img


def split_into_frames(
    image: Image.Image,
    rows: int,
    cols: int | None = None,
) -> list[Image.Image]:
    """
    Split image into rows×cols frames. Row-major order: left-to-right, then top-to-bottom.
    If cols is None, use rows×rows (N×N).
    Returns list of frame images (frame_0, frame_1, ...).
    """
    if cols is None:
        cols = rows
    w, h = image.size
    fw = w // cols
    fh = h // rows
    frames: list[Image.Image] = []
    for row in range(rows):
        for col in range(cols):
            left = col * fw
            top = row * fh
            box = (left, top, left + fw, top + fh)
            frames.append(image.crop(box))
    return frames


def frames_to_gif(
    frames: list[Image.Image],
    path: Path | str,
    duration_ms: int = 100,
) -> None:
    """
    Save a list of RGBA frame images as an animated GIF for preview.
    duration_ms: display time per frame in milliseconds.
    disposal=2: each frame replaces the previous (no stacking).
    """
    if not frames:
        return
    path = Path(path)
    first = frames[0]
    rest = frames[1:]
    first.save(
        path,
        save_all=True,
        append_images=rest,
        duration=duration_ms,
        loop=0,
        disposal=2,
    )
