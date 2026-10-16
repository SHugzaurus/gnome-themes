#!/usr/bin/env bash
# Teinte une image aux couleurs de src/_monbo-palette.scss (gradient map).
# Usage : teinter.sh <image> <dossier de sortie> [sauge|sombre|nuance ...]
#   sauge  : dégradé vert noir → sauge → blanc cassé
#   sombre : même principe, ramené vers des tons plus sombres
#   nuance : « sombre » mélangé à 20 % des couleurs d'origine
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$1"; OUT="$2"; shift 2
MODES=("${@:-nuance}")
[[ $# -eq 0 ]] && MODES=(sauge sombre nuance)

color() { grep -oP "\\\$$1:\s*\K#[0-9a-fA-F]{6}" "$ROOT/src/_monbo-palette.scss"; }
PANEL=$(color monbo_panel); ACCENT=$(color monbo_accent); FG=$(color monbo_fg)

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
mkdir -p "$OUT"
NAME=$(basename "${SRC%.*}")

# dégradés : index 0 (haut) = ombres, 255 (bas) = lumières
magick -size 1x128 gradient:"$PANEL"-"$ACCENT" -size 1x128 gradient:"$ACCENT"-"$FG" \
  -append "$TMP/clut-sauge.png"
magick -size 1x86 gradient:"$PANEL"-"$(magick xc:"$ACCENT" -fill black -colorize 40% -format '%[hex:p{0,0}]' info: | sed 's/^/#/')" \
  -size 1x85 gradient:"$(magick xc:"$ACCENT" -fill black -colorize 40% -format '%[hex:p{0,0}]' info: | sed 's/^/#/')"-"$ACCENT" \
  -size 1x85 gradient:"$ACCENT"-"$(magick xc:"$FG" -fill "$ACCENT" -colorize 30% -format '%[hex:p{0,0}]' info: | sed 's/^/#/')" \
  -append "$TMP/clut-sombre.png"

for mode in "${MODES[@]}"; do
  dest="$OUT/$NAME-$mode.png"
  case "$mode" in
    sauge)  magick "$SRC" -colorspace gray "$TMP/clut-sauge.png" -clut "$dest" ;;
    sombre) magick "$SRC" -colorspace gray -level 0%,100%,0.75 "$TMP/clut-sombre.png" -clut "$dest" ;;
    nuance)
      magick "$SRC" -colorspace gray -level 0%,100%,0.75 "$TMP/clut-sombre.png" -clut "$TMP/sombre.png"
      magick "$SRC" "$TMP/sombre.png" -compose blend -define compose:args=80,20 -composite "$dest" ;;
    *) echo "mode inconnu : $mode" >&2; exit 1 ;;
  esac
  echo "Créé : $dest"
done
