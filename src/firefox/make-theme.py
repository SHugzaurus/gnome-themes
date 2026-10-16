#!/usr/bin/env python3
"""Génère le thème Firefox (manifest.json) à partir de src/_monbo-palette.scss."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PALETTE = ROOT / "src" / "_monbo-palette.scss"
VERSION = (ROOT / "VERSION").read_text().strip()


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
    r, g, b = rgb(c)
    return f"rgba({r}, {g}, {b}, {a})"


def main(out_dir):
    p = read_palette()
    accent, accent_fg = p["monbo_accent"], p["monbo_accent_fg"]
    panel, surface, fg = p["monbo_panel"], p["monbo_surface"], p["monbo_fg"]

    # mêmes teintes que les applis GTK (src/gtk/_gtk-colors.scss)
    window_bg = mix(panel, surface, .4)
    view_bg = mix(panel, surface, .7)
    popover_bg = mix("#ffffff", surface, .03)

    manifest = {
        "manifest_version": 2,
        "name": "Monbothemesamer",
        "version": VERSION,
        "description": "Thème sauge sombre assorti au thème GNOME Shell Monbothemesamer",
        "browser_specific_settings": {"gecko": {"id": "monbothemesamer@local"}},
        "theme": {
            "colors": {
                "frame": view_bg,
                "frame_inactive": view_bg,
                "tab_background_text": alpha(fg, .7),
                "tab_selected": surface,
                "tab_text": fg,
                "tab_line": accent,
                "tab_loading": accent,
                "toolbar": surface,
                "toolbar_text": fg,
                "toolbar_top_separator": surface,
                "toolbar_bottom_separator": view_bg,
                "toolbar_field": window_bg,
                "toolbar_field_text": fg,
                "toolbar_field_focus": view_bg,
                "toolbar_field_text_focus": fg,
                "toolbar_field_border_focus": accent,
                "toolbar_field_highlight": accent,
                "toolbar_field_highlight_text": accent_fg,
                "button_background_hover": alpha(fg, .1),
                "button_background_active": alpha(fg, .18),
                "icons": fg,
                "icons_attention": accent,
                "popup": popover_bg,
                "popup_text": fg,
                "popup_border": alpha(accent, .15),
                "popup_highlight": accent,
                "popup_highlight_text": accent_fg,
                "sidebar": window_bg,
                "sidebar_text": fg,
                "sidebar_border": view_bg,
                "sidebar_highlight": accent,
                "sidebar_highlight_text": accent_fg,
                "ntp_background": window_bg,
                "ntp_text": fg,
                "ntp_card_background": surface,
            },
            "properties": {"color_scheme": "dark", "content_color_scheme": "dark"},
        },
    }

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    # Les pages internes (about:*) n'utilisent pas le thème : Firefox y impose
    # son propre accent (violet avec browser.nova.enabled). On le remplace via
    # userContent.css ; une règle hors @layer l'emporte sur leurs tokens.
    accent_text = mix("#ffffff", accent, .25)
    user_content = f"""/* Monbothemesamer : fichier généré, modifier src/firefox/ puis relancer build.sh */
@-moz-document url-prefix("about:"), url-prefix("chrome:") {{
  :root {{
    --color-accent-primary: {accent} !important;
    --color-accent-primary-hover: {mix("#ffffff", accent, .12)} !important;
    --color-accent-primary-active: {mix("#ffffff", accent, .24)} !important;
    --color-accent-primary-selected: {accent} !important;
    --button-text-color-primary: {accent_fg} !important;
    --text-color-accent-primary-selected: {accent_fg} !important;
    --link-color: {accent_text} !important;
    --link-color-hover: {mix("#ffffff", accent, .4)} !important;
    --link-color-active: {mix("#ffffff", accent, .5)} !important;
    --focus-outline-color: {accent} !important;
  }}
}}
"""
    (out / "userContent.css").write_text(user_content)


if __name__ == "__main__":
    main(sys.argv[1])
