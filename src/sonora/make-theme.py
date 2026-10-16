#!/usr/bin/env python3
"""Génère le thème Sonora (monbothemesamer.json) à partir de src/_monbo-palette.scss."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PALETTE = ROOT / "src" / "_monbo-palette.scss"


def read_palette():
    text = PALETTE.read_text()
    return {name: value for name, value in re.findall(r"\$(\w+):\s*(#[0-9a-fA-F]{6})", text)}


def rgb(hex_color):
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def to_hex(c):
    return "#" + "".join(f"{round(v):02x}" for v in c)


def mix(a, b, weight):
    """Comme mix() de Sass : weight de a, le reste de b."""
    return to_hex(x * weight + y * (1 - weight) for x, y in zip(rgb(a), rgb(b)))


def alpha(c, a):
    """Sonora n'accepte que #rrggbb ou #rrggbbaa."""
    return f"{c}{round(a * 255):02x}"


def main(out_dir):
    p = read_palette()
    accent, accent_fg = p["monbo_accent"], p["monbo_accent_fg"]
    panel, surface, fg = p["monbo_panel"], p["monbo_surface"], p["monbo_fg"]

    # mêmes teintes que les applis GTK (src/gtk/_gtk-colors.scss)
    window_bg = mix(panel, surface, .4)
    view_bg = mix(panel, surface, .7)
    sidebar_bg = mix(panel, surface, .55)
    popover_bg = mix("#ffffff", surface, .03)
    muted_fg = mix(fg, window_bg, .62)

    # Sonora refuse les champs inconnus et ignore radius/font_size dans un fichier
    theme = {
        "name": "Monbothemesamer",
        "author": "Monbothemesamer",
        "version": 1,
        "theme": {
            "background": window_bg,
            "foreground": fg,
            "border": alpha(fg, .1),
            "muted": surface,
            "muted_foreground": muted_fg,
            "overlay": alpha(fg, .06),
            "overlay_foreground": fg,
            "secondary": surface,
            "secondary_hover": mix("#ffffff", surface, .06),
            "secondary_active": mix("#ffffff", surface, .1),
            "primary": accent,
            "primary_foreground": accent_fg,
            "primary_hover": mix("#ffffff", accent, .12),
            "popover": popover_bg,
            "popover_foreground": fg,
            "progress_bar": accent,
            "selection": alpha(accent, .35),
            "sidebar": sidebar_bg,
            "sidebar_accent": surface,
            "sidebar_border": view_bg,
            "title_bar_border": view_bg,
            "table_head": window_bg,
            "table_head_foreground": muted_fg,
            "table_row_border": alpha(fg, .06),
            "table_hover": alpha(fg, .05),
            "table_active": alpha(accent, .16),
            "table_active_border": alpha(accent, .5),
        },
    }

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "monbothemesamer.json").write_text(json.dumps(theme, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
