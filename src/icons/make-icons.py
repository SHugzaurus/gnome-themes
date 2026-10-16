#!/usr/bin/env python3
"""Génère le thème d'icônes Monbothemesamer : Papirus-Dark dont les couleurs dérivent vers la sauge.

Usage : make-icons.py <dossier de sortie> [--pull 0.35] [--folder-pull 0.85] [--chroma 0.85]
  --pull        part de la teinte sauge mélangée à chaque couleur (0 = Papirus d'origine, 1 = tout sauge)
  --folder-pull même chose pour les dossiers, poussés plus fort pour être vraiment sauge
  --chroma saturation conservée (1 = intacte)
Les icônes symboliques ne sont pas touchées : GTK et le Shell les recolorent déjà.
"""
import argparse
import math
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PALETTE = ROOT / "src" / "_monbo-palette.scss"
OVERRIDES = Path(__file__).resolve().parent / "overrides"   # SVG perso, copiés tels quels
PAPIRUS = Path("/usr/share/icons/Papirus")
PAPIRUS_DARK = Path("/usr/share/icons/Papirus-Dark")
NAME = "Monbothemesamer"

HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")


def read_palette():
    text = PALETTE.read_text()
    return {name: value for name, value in re.findall(r"\$(\w+):\s*(#[0-9a-fA-F]{6})", text)}


# --- sRGB <-> OKLab (https://bottosson.github.io/posts/oklab/) ---

def _to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _from_linear(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hex_to_oklab(h):
    r, g, b = (_to_linear(int(h[i:i + 2], 16) / 255) for i in (1, 3, 5))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def oklab_to_rgb(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def oklab_to_hex(L, a, b):
    # hors gamut : on réduit la saturation jusqu'à rentrer dans le sRGB
    for _ in range(20):
        rgb = oklab_to_rgb(L, a, b)
        if all(-1e-4 <= c <= 1 + 1e-4 for c in rgb):
            break
        a, b = a * 0.9, b * 0.9
    return "#" + "".join(f"{round(min(max(_from_linear(min(max(c, 0), 1)), 0), 1) * 255):02x}" for c in rgb)


def make_drift(accent, pull, chroma):
    _, sa, sb = hex_to_oklab(accent)
    cache = {}

    def drift(match):
        h = match.group(1).lower()
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if h not in cache:
            L, a, b = hex_to_oklab("#" + h)
            # la luminosité reste, la teinte/saturation est mélangée avec la sauge
            a = a * chroma * (1 - pull) + sa * pull
            b = b * chroma * (1 - pull) + sb * pull
            cache[h] = oklab_to_hex(L, a, b)
        return cache[h]

    return drift


def copy_base(out):
    """Papirus complet, puis les dossiers propres à Papirus-Dark par-dessus."""
    shutil.copytree(PAPIRUS, out, symlinks=True)
    for size in PAPIRUS_DARK.iterdir():
        if size.is_symlink() or not size.is_dir():
            continue
        for category in size.iterdir():
            if category.is_symlink():
                continue
            dest = out / size.name / category.name
            if dest.is_symlink() or dest.is_file():
                dest.unlink()
            elif dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(category, dest, symlinks=True)

    index = (PAPIRUS_DARK / "index.theme").read_text()
    index = re.sub(r"^Name=.*$", f"Name={NAME}", index, count=1, flags=re.M)
    index = re.sub(r"^Comment=.*$", "Comment=Papirus-Dark dérivé vers la sauge", index, count=1, flags=re.M)
    index = re.sub(r"^Inherits=.*$", "Inherits=Adwaita,hicolor", index, count=1, flags=re.M)
    index = re.sub(r"^FollowsColorScheme=.*\n", "", index, flags=re.M)
    (out / "index.theme").write_text(index)
    (out / "icon-theme.cache").unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out")
    parser.add_argument("--pull", type=float, default=0.35)
    parser.add_argument("--folder-pull", type=float, default=0.85)
    parser.add_argument("--chroma", type=float, default=0.85)
    args = parser.parse_args()

    out = Path(args.out) / NAME
    if out.exists():
        shutil.rmtree(out)
    copy_base(out)

    accent = read_palette()["monbo_accent"]
    drift = make_drift(accent, args.pull, args.chroma)
    folder_drift = make_drift(accent, args.folder_pull, args.chroma)
    count = 0
    for svg in out.rglob("*.svg"):
        if svg.is_symlink() or "symbolic" in svg.parts or svg.name.endswith("-symbolic.svg"):
            continue
        text = svg.read_text(errors="surrogateescape")
        is_folder = "places" in svg.parts and svg.name.startswith(("folder", "user-"))
        new = HEX.sub(folder_drift if is_folder else drift, text)
        if new != text:
            svg.write_text(new, errors="surrogateescape")
            count += 1

    # icônes perso : overrides/<taille>/<catégorie>/<nom>.svg
    if OVERRIDES.is_dir():
        for svg in OVERRIDES.rglob("*.svg"):
            dest = out / svg.relative_to(OVERRIDES)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.is_symlink():
                dest.unlink()
            shutil.copy2(svg, dest)

    subprocess.run(["gtk-update-icon-cache", "-q", "-f", str(out)], check=False)
    print(f"Icônes : {count} SVG recolorés dans {out}")


if __name__ == "__main__":
    main()
