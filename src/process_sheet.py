"""
Core logic: make solid background transparent and split sheet into M×N frames.
Preview export: GIF, APNG, MP4; optional checkerboard background.
"""
from __future__ import annotations

from pathlib import Path
from typing import cast

import numpy as np
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
    out = cast(Image.Image, rembg_remove(image))
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


def _checkerboard(size: tuple[int, int], tile_size: int = 8) -> Image.Image:
    """Create a checkerboard pattern (light gray / white) as RGB image."""
    w, h = size
    tile = tile_size
    # Two colors: #e0e0e0 and #ffffff
    c1, c2 = (0xE0, 0xE0, 0xE0), (0xFF, 0xFF, 0xFF)
    out = Image.new("RGB", size)
    px = out.load()
    assert px is not None  # PIL load() returns PixelAccess for new images
    for y in range(h):
        for x in range(w):
            ix, iy = x // tile, y // tile
            px[x, y] = c1 if ((ix + iy) % 2 == 0) else c2
    return out


def _composite_on_checkerboard(frame: Image.Image, tile_size: int = 8) -> Image.Image:
    """Composite RGBA frame onto checkerboard; returns RGB."""
    if frame.mode != "RGBA":
        frame = frame.convert("RGBA")
    bg = _checkerboard(frame.size, tile_size)
    bg.paste(frame, (0, 0), frame)
    return bg.convert("RGB")


def _composite_on_white(frame: Image.Image) -> Image.Image:
    """Composite RGBA frame onto white; returns RGB."""
    if frame.mode != "RGBA":
        return frame.convert("RGB")
    bg = Image.new("RGB", frame.size, (255, 255, 255))
    bg.paste(frame, (0, 0), frame)
    return bg


def frames_to_gif(
    frames: list[Image.Image],
    path: Path | str,
    duration_ms: int = 100,
    checkerboard: bool = False,
) -> None:
    """
    Save RGBA frames as animated GIF. disposal=2 so each frame replaces the previous.
    If checkerboard=True, composite each frame on a checkerboard background (no transparency in output).
    """
    if not frames:
        return
    path = Path(path)
    if checkerboard:
        frames = [_composite_on_checkerboard(f) for f in frames]
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


def frames_to_apng(
    frames: list[Image.Image],
    path: Path | str,
    duration_ms: int = 100,
    checkerboard: bool = False,
) -> None:
    """Save RGBA frames as APNG. Requires: pip install apng."""
    if not frames:
        return
    path = Path(path)
    if checkerboard:
        frames = [_composite_on_checkerboard(f) for f in frames]
    else:
        frames = [f.convert("RGBA") if f.mode != "RGBA" else f for f in frames]
    try:
        import apng
    except ImportError as e:
        raise RuntimeError("apng is not installed. Install with: pip install apng") from e
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        files = [Path(tmp) / f"f{i}.png" for i in range(len(frames))]
        for f, p in zip(frames, files):
            f.save(str(p), "PNG")
        # delay: delay_num/delay_den = seconds (APNG fcTL); 100ms = 10/100 s
        delay_cs = max(1, round(duration_ms / 10))
        im = apng.APNG(num_plays=0)  # 0 = loop forever
        for p in files:
            im.append_file(str(p), delay=delay_cs, delay_den=100)
        im.save(str(path))


def frames_to_mp4(
    frames: list[Image.Image],
    path: Path | str,
    duration_ms: int = 100,
    checkerboard: bool = False,
) -> None:
    """Save RGBA frames as MP4. Requires: pip install imageio imageio-ffmpeg."""
    if not frames:
        return
    path = Path(path)
    if checkerboard:
        frames = [_composite_on_checkerboard(f) for f in frames]
    else:
        frames = [f.convert("RGB") if f.mode != "RGBA" else _composite_on_white(f) for f in frames]
    try:
        import imageio
    except ImportError as e:
        raise RuntimeError(
            "imageio is not installed. Install with: pip install imageio imageio-ffmpeg"
        ) from e
    fps = 1000.0 / max(1, duration_ms)
    arrays = [np.asarray(f) for f in frames]
    # Explicit format so imageio uses FFmpeg for .mp4 (avoids wrong plugin selection)
    writer = imageio.get_writer(str(path), format="FFMPEG", fps=fps, codec="libx264")  # type: ignore[arg-type]
    for arr in arrays:
        writer.append_data(arr)
    writer.close()
