#!/usr/bin/env python3
"""Generate icon.png / icon.icns and tab close PNGs for PyInstaller / QSS."""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "resources"


def _draw_tab_close(size: int, hover: bool) -> Image.Image:
    """White × on transparent (or subtle circle when hover) for dark tab bar."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    if hover:
        pad = size // 8
        draw.ellipse(
            (pad, pad, size - pad, size - pad),
            fill=(255, 255, 255, 38),
            outline=(255, 255, 255, 90),
            width=1,
        )
    margin = size // 3
    color = (232, 234, 237, 255)
    w = max(2, size // 10)
    draw.line((margin, margin, size - margin, size - margin), fill=color, width=w)
    draw.line((size - margin, margin, margin, size - margin), fill=color, width=w)
    return im


def main() -> None:
    RES.mkdir(parents=True, exist_ok=True)
    for name, hover in (("tab_close.png", False), ("tab_close_hover.png", True)):
        p = RES / name
        _draw_tab_close(18, hover).save(p, "PNG")
        print("Wrote", p)

    size = 512
    im = Image.new("RGBA", (size, size), (124, 58, 237, 255))
    draw = ImageDraw.Draw(im)
    margin = size // 7
    draw.rounded_rectangle(
        (margin, margin * 2, size - margin, size - margin),
        radius=size // 16,
        fill=(255, 255, 255, 255),
    )
    inner = margin + size // 14
    draw.rounded_rectangle(
        (inner, inner + margin, size - inner, size - inner - margin),
        radius=size // 20,
        fill=(237, 233, 254, 255),
    )
    png = ROOT / "icon.png"
    im.save(png, "PNG")
    print("Wrote", png)
    icns = ROOT / "icon.icns"
    im.save(icns, "ICNS")
    print("Wrote", icns)


if __name__ == "__main__":
    main()
