#!/usr/bin/env python3
"""Génère la palette Ptyxis (terminal GNOME) à partir de src/_monbo-palette.scss.

Ptyxis ignore gtk.css pour ses couleurs : il colore toute sa fenêtre (fond,
barre de titre) d'après sa palette. On reprend les couleurs du terminal de
VS Code pour que les deux restent identiques.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location("vscode_theme", ROOT / "src" / "vscode" / "make-theme.py")
vscode = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vscode)

ANSI = ["Black", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White"]


def main(out_file):
    p = vscode.read_palette()
    c = vscode.workbench_colors(p)

    lines = [
        f"Background={c['terminal.background']}",
        f"Foreground={c['terminal.foreground']}",
        f"TitlebarBackground={p['monbo_surface']}",
        f"TitlebarForeground={p['monbo_fg']}",
        f"Cursor={c['terminalCursor.foreground']}",
    ]
    for i, name in enumerate(ANSI):
        lines.append(f"Color{i}={c['terminal.ansi' + name]}")
    for i, name in enumerate(ANSI):
        lines.append(f"Color{i + 8}={c['terminal.ansiBright' + name]}")
    body = "\n".join(lines)

    # thème sombre uniquement : la variante claire reprend les mêmes couleurs
    out = Path(out_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"""# Monbothemesamer : fichier généré, modifier src/ptyxis/ puis relancer build.sh
[Palette]
Name=Monbothemesamer

[Light]
{body}

[Dark]
{body}
""")


if __name__ == "__main__":
    main(sys.argv[1])
