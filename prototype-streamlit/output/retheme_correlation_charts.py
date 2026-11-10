"""Retheme saved scientific plots without moving points or changing any values.

Input snapshots are the charts originally published with this app. Palette
mapping preserves their size, axes, labels, observation locations and r/n text.
The original RdBu heatmap is remapped at the same positions on its [-1, 1] scale.
Workload plots are rebuilt separately with the approved horizontal layout.
Requires numpy, matplotlib and Pillow; these are authoring dependencies only.
"""
from pathlib import Path
from io import BytesIO
import zipfile
import numpy as np
from PIL import Image
from matplotlib import colormaps
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]
BLUE = "#6F98B0"
CORAL = "#F4A78D"
HEATMAP = LinearSegmentedColormap.from_list("blue_white_coral", ["#6F98B0", "#FFFFFF", CORAL])


def rgb(code):
    return np.array([int(code[i:i+2], 16) for i in (1, 3, 5)], dtype=float)


def transform_colors(colors, name):
    colors = colors.astype(float)
    mapped = colors.copy()
    # Preserve text and its antialiasing, including the original navy labels.
    ink = rgb("#142F42")
    ink_ray = ink - 255
    a = np.clip(((colors-255) @ ink_ray) / (ink_ray @ ink_ray), 0, 1)
    text_dist = np.linalg.norm(colors - (255 + a[:, None]*ink_ray), axis=1)
    protected = (text_dist < 8) | (np.ptp(colors, axis=1) < 12)
    heatmap = "berth-correlation" in name or name == "unified-dgt-berth-1.png"
    if heatmap:
        # Identical colorbar coordinates and limits; no normalization by the
        # observed minimum/maximum, which would exaggerate weak correlations.
        positions = np.linspace(0, 1, 256)
        original = np.rint(colormaps["RdBu_r"](positions)[:, :3]*255)
        distances = np.linalg.norm(colors[:, None, :] - original[None, :, :], axis=2)
        index = distances.argmin(axis=1)
        use = (distances.min(axis=1) < 12) & ~protected
        mapped[use] = np.rint(HEATMAP(positions[index[use]])[:, :3]*255)
    else:
        comparison = name.endswith("-r.png") and "itt" in name
        targets = [
            ("#185DAC", BLUE),
            ("#187A72", CORAL if comparison else BLUE),
            ("#BD6043", CORAL),
            ("#4E83AF", BLUE), ("#4D82B0", BLUE),
            ("#DC9C56", CORAL), ("#D99B57", CORAL),
        ]
        best = np.full(len(colors), np.inf)
        for old_code, new_code in targets:
            old, new = rgb(old_code), rgb(new_code)
            # Includes overlapping translucent observations and edge pixels.
            for background in (255.0, 0.0):
                ray = old - background
                alpha = np.clip(((colors-background) @ ray)/(ray @ ray), 0, 1)
                expected = background + alpha[:, None]*ray
                distance = np.linalg.norm(colors-expected, axis=1)
                use = (distance < 7) & (distance < best) & ~protected
                mapped[use] = background + alpha[use, None]*(new-background)
                best[use] = distance[use]
    return np.clip(np.rint(mapped), 0, 255).astype(np.uint8)


def retheme_bytes(raw, name):
    with Image.open(BytesIO(raw)) as im:
        pixels = np.asarray(im.convert("RGB"))
    colors, inverse = np.unique(pixels.reshape(-1, 3), axis=0, return_inverse=True)
    mapped = transform_colors(colors, name)
    result = mapped[inverse].reshape(pixels.shape)
    assert result.shape == pixels.shape
    output = BytesIO()
    Image.fromarray(result).save(output, format="PNG", optimize=True)
    return output.getvalue(), int(np.any(result != pixels, axis=2).sum())


def main():
    target = ROOT / "assets/correlation-analysis/unified"
    with zipfile.ZipFile(ROOT / "output/correlation-chart-originals.zip") as archive:
        for name in archive.namelist():
            assert Path(name).name == name and name.endswith(".png")
            if name in {"unified-dgt-berth-0.png", "unified-hjnc-berth-volume.png", "unified-itt-forward-berth-volume.png", "unified-itt-reverse-berth-volume.png"}:
                continue
            result, changed = retheme_bytes(archive.read(name), name)
            assert changed > 0, name
            (target/name).write_bytes(result)
            print(f"{name}: {changed:,} palette pixels updated")


if __name__ == "__main__":
    main()
    from build_berth_volume import build
    build()
