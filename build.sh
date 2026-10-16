#!/usr/bin/env bash
# Compile le thème et, avec --install, l'installe pour l'utilisateur
set -euo pipefail

NAME=Monbothemesamer
ROOT="$(cd "$(dirname "$0")" && pwd)"
BUILD="$ROOT/build"
OUT="$BUILD/$NAME/gnome-shell"
MARKER="Monbothemesamer : fichier généré"

mkdir -p "$OUT" "$BUILD/gtk-4.0" "$BUILD/gtk-3.0"
sassc -M -t expanded "$ROOT/src/gnome-shell.scss" "$OUT/gnome-shell.css"
sassc -M -t expanded "$ROOT/src/gtk/gtk4.scss" "$BUILD/gtk-4.0/gtk.css"
sassc -M -t expanded "$ROOT/src/gtk/gtk3.scss" "$BUILD/gtk-3.0/gtk.css"
# GTK ne connaît pas @charset (ajouté par sassc à cause des accents)
sed -i '/^@charset/d' "$BUILD/gtk-4.0/gtk.css" "$BUILD/gtk-3.0/gtk.css"

# thème Firefox : manifest.json + archive .xpi
python3 -I "$ROOT/src/firefox/make-theme.py" "$BUILD/firefox"
rm -f "$BUILD/$NAME-firefox.xpi"
(cd "$BUILD/firefox" && zip -q -X "$BUILD/$NAME-firefox.xpi" manifest.json)

# thème VS Code : extension .vsix
rm -rf "$BUILD/vscode" "$BUILD/$NAME-vscode.vsix"
python3 -I "$ROOT/src/vscode/make-theme.py" "$BUILD/vscode"
(cd "$BUILD/vscode" && zip -q -X -r "$BUILD/$NAME-vscode.vsix" .)

# thème Sonora
python3 -I "$ROOT/src/sonora/make-theme.py" "$BUILD/sonora"

# palette du terminal Ptyxis
python3 -I "$ROOT/src/ptyxis/make-palette.py" "$BUILD/ptyxis/$NAME.palette"

# icônes : Papirus-Dark dérivé vers la sauge (~20 s)
if [[ -d /usr/share/icons/Papirus-Dark ]]; then
  python3 -I "$ROOT/src/icons/make-icons.py" "$BUILD/icons"
else
  echo "Attention : Papirus absent, pas de thème d'icônes (sudo dnf install papirus-icon-theme)" >&2
fi
echo "Compilé dans : $BUILD"

# installe un gtk.css sans écraser un fichier qui ne vient pas de ce thème
install_gtk() {
  local src="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  if [[ -f "$dest" ]] && ! grep -q "$MARKER" "$dest"; then
    cp "$dest" "$dest.avant-monbo"
    echo "Sauvegarde : $dest.avant-monbo"
  fi
  cp "$src" "$dest"
  echo "Installé : $dest"
}

if [[ "${1:-}" == "--install" ]]; then
  DEST="${XDG_DATA_HOME:-$HOME/.local/share}/themes/$NAME"
  CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
  mkdir -p "$DEST"
  rm -rf "$DEST/gnome-shell"
  cp -r "$OUT" "$DEST/"
  echo "Installé : $DEST/gnome-shell"

  install_gtk "$BUILD/gtk-4.0/gtk.css" "$CONFIG/gtk-4.0/gtk.css"
  install_gtk "$BUILD/gtk-3.0/gtk.css" "$CONFIG/gtk-3.0/gtk.css"

  # GTK3 : seul adw-gtk3 lit les couleurs nommées de gtk-3.0/gtk.css
  # (l'Adwaita intégré à GTK3 a ses couleurs en dur)
  if [[ -d /usr/share/themes/adw-gtk3-dark || -d "$DEST/../adw-gtk3-dark" ]]; then
    gsettings set org.gnome.desktop.interface gtk-theme adw-gtk3-dark
    echo "Thème GTK3 : adw-gtk3-dark"
  else
    echo "Attention : adw-gtk3 absent, les applis GTK3 ne prendront pas le thème." >&2
    echo "  sudo dnf install adw-gtk3-theme && ./build.sh --install" >&2
  fi
  if command -v flatpak >/dev/null; then
    flatpak override --user --filesystem=xdg-config/gtk-3.0:ro --filesystem=xdg-config/gtk-4.0:ro
  fi
  # les portails (sélecteur de fichiers) tournent en continu et ne relisent pas gtk.css
  systemctl --user try-restart xdg-desktop-portal-gnome xdg-desktop-portal-gtk xdg-desktop-portal || true

  # Firefox : userContent.css dans le profil utilisé par défaut
  FF="$CONFIG/mozilla/firefox"
  PROFILE=$(awk -F= '/^\[Install/{i=1} i && /^Default=/{print $2; exit}' "$FF/profiles.ini" 2>/dev/null || true)
  if [[ -n "$PROFILE" && -d "$FF/$PROFILE" ]]; then
    install_gtk "$BUILD/firefox/userContent.css" "$FF/$PROFILE/chrome/userContent.css"
    PREF='user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);'
    grep -qF "$PREF" "$FF/$PROFILE/user.js" 2>/dev/null || echo "$PREF" >> "$FF/$PROFILE/user.js"
  fi

  # Ptyxis : palette installée puis choisie pour tous les profils
  PTYXIS="${XDG_DATA_HOME:-$HOME/.local/share}/org.gnome.Ptyxis/palettes"
  mkdir -p "$PTYXIS"
  cp "$BUILD/ptyxis/$NAME.palette" "$PTYXIS/"
  echo "Installé : $PTYXIS/$NAME.palette"
  if command -v ptyxis >/dev/null; then
    for uuid in $(gsettings get org.gnome.Ptyxis profile-uuids | tr -d "[]',"); do
      gsettings set "org.gnome.Ptyxis.Profile:/org/gnome/Ptyxis/Profiles/$uuid/" palette "$NAME"
    done
  fi

  # icônes
  if [[ -d "$BUILD/icons/$NAME" ]]; then
    ICONS="${XDG_DATA_HOME:-$HOME/.local/share}/icons/$NAME"
    rm -rf "$ICONS"
    cp -a "$BUILD/icons/$NAME" "$ICONS"
    gsettings set org.gnome.desktop.interface icon-theme "$NAME"
    echo "Installé : $ICONS"
  fi

  # Sonora (Flatpak) : relu à chaud, à choisir dans Réglages > Design
  SONORA="$HOME/.var/app/io.github.nolight132.sonora/config/sonora"
  if [[ -d "$SONORA" ]]; then
    mkdir -p "$SONORA/themes"
    cp "$BUILD/sonora/monbothemesamer.json" "$SONORA/themes/"
    echo "Installé : $SONORA/themes/monbothemesamer.json"
  fi

  # VS Code : à activer ensuite avec Ctrl+K Ctrl+T
  if command -v code >/dev/null; then
    code --install-extension "$BUILD/$NAME-vscode.vsix" --force
  fi
fi

# Signature du thème Firefox par Mozilla (canal non listé : le thème reste privé).
# Clés : https://addons.mozilla.org/developers/addon/api/key/
# Mozilla refuse de signer deux fois la même version : incrémenter VERSION avant.
if [[ "${1:-}" == "--sign" ]]; then
  : "${WEB_EXT_API_KEY:?définir WEB_EXT_API_KEY (identifiant JWT)}"
  : "${WEB_EXT_API_SECRET:?définir WEB_EXT_API_SECRET (secret JWT)}"
  npx --yes web-ext sign --channel=unlisted \
    --source-dir "$BUILD/firefox" --artifacts-dir "$BUILD/signed" \
    --ignore-files userContent.css
  echo "Thème signé dans : $BUILD/signed"
fi
