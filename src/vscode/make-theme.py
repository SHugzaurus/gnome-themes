#!/usr/bin/env python3
"""Génère le thème VS Code (extension .vsix) à partir de src/_monbo-palette.scss."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PALETTE = ROOT / "src" / "_monbo-palette.scss"
VERSION = (ROOT / "VERSION").read_text().strip()

# couleurs de la coloration syntaxique et du terminal : tons doux et terreux,
# choisis pour aller avec la sauge (la palette du Shell n'en définit pas)
SYNTAX = {
    "comment": "#6b7a6e",
    "string": "#d6c48e",      # blé
    "number": "#e2a27c",      # terre cuite
    "function": "#92c6be",    # vert d'eau
    "type": "#a9bfdc",        # bleu poussière
    "property": "#c5d3c2",
    "operator": "#a3ada2",
    "regex": "#d9a3b8",       # vieux rose
    "error": "#e07a7a",
}


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
    """#rrggbbaa, la notation de transparence de VS Code."""
    return c + f"{round(a * 255):02x}"


def semver(version):
    parts = version.split(".")
    return ".".join((parts + ["0", "0"])[:3])


def workbench_colors(p):
    accent, accent_fg = p["monbo_accent"], p["monbo_accent_fg"]
    panel, surface, fg = p["monbo_panel"], p["monbo_surface"], p["monbo_fg"]

    # mêmes teintes que les applis GTK (src/gtk/_gtk-colors.scss)
    window_bg = mix(panel, surface, .4)
    view_bg = mix(panel, surface, .7)
    sidebar_bg = mix(panel, surface, .55)
    popover_bg = mix("#ffffff", surface, .03)
    accent_text = mix("#ffffff", accent, .25)
    dim_fg = alpha(fg, .6)
    border = alpha(fg, .07)
    hover = alpha(fg, .07)
    selection = alpha(accent, .28)

    return {
        "foreground": fg,
        "disabledForeground": alpha(fg, .4),
        "descriptionForeground": dim_fg,
        "errorForeground": SYNTAX["error"],
        "focusBorder": alpha(accent, .6),
        "contrastBorder": "#00000000",
        "widget.border": alpha(accent, .15),
        "widget.shadow": "#0000005c",
        "selection.background": selection,
        "icon.foreground": fg,
        "sash.hoverBorder": accent,
        "textLink.foreground": accent_text,
        "textLink.activeForeground": mix("#ffffff", accent, .4),
        "progressBar.background": accent,

        # barres
        "titleBar.activeBackground": panel,
        "titleBar.activeForeground": fg,
        "titleBar.inactiveBackground": panel,
        "titleBar.inactiveForeground": dim_fg,
        "titleBar.border": "#00000000",
        "activityBar.background": view_bg,
        "activityBar.foreground": fg,
        "activityBar.inactiveForeground": alpha(fg, .45),
        "activityBar.activeBorder": accent,
        "activityBar.activeBackground": hover,
        "activityBar.border": "#00000000",
        "activityBarBadge.background": accent,
        "activityBarBadge.foreground": accent_fg,
        "activityBarTop.foreground": fg,
        "activityBarTop.activeBorder": accent,
        "statusBar.background": panel,
        "statusBar.foreground": dim_fg,
        "statusBar.border": "#00000000",
        "statusBar.noFolderBackground": panel,
        "statusBar.debuggingBackground": accent,
        "statusBar.debuggingForeground": accent_fg,
        "statusBarItem.hoverBackground": hover,
        "statusBarItem.remoteBackground": accent,
        "statusBarItem.remoteForeground": accent_fg,
        "statusBarItem.prominentBackground": alpha(accent, .2),

        # panneaux latéraux et du bas
        "sideBar.background": sidebar_bg,
        "sideBar.foreground": fg,
        "sideBar.border": "#00000000",
        "sideBarTitle.foreground": dim_fg,
        "sideBarSectionHeader.background": "#00000000",
        "sideBarSectionHeader.foreground": fg,
        "sideBarSectionHeader.border": border,
        "panel.background": view_bg,
        "panel.border": border,
        "panelTitle.activeBorder": accent,
        "panelTitle.activeForeground": fg,
        "panelTitle.inactiveForeground": dim_fg,

        # listes et arbres
        "list.activeSelectionBackground": alpha(accent, .22),
        "list.activeSelectionForeground": fg,
        "list.inactiveSelectionBackground": alpha(fg, .08),
        "list.hoverBackground": hover,
        "list.focusOutline": alpha(accent, .5),
        "list.highlightForeground": accent_text,
        "list.dropBackground": alpha(accent, .2),
        "tree.indentGuidesStroke": alpha(fg, .12),

        # onglets
        "editorGroupHeader.tabsBackground": view_bg,
        "editorGroupHeader.tabsBorder": "#00000000",
        "editorGroup.border": border,
        "tab.activeBackground": window_bg,
        "tab.activeForeground": fg,
        "tab.activeBorderTop": accent,
        "tab.inactiveBackground": view_bg,
        "tab.inactiveForeground": dim_fg,
        "tab.hoverBackground": mix(view_bg, window_bg, .5),
        "tab.border": "#00000000",
        "tab.unfocusedActiveBorderTop": alpha(accent, .4),
        "breadcrumb.background": window_bg,
        "breadcrumb.foreground": dim_fg,
        "breadcrumb.focusForeground": fg,

        # éditeur
        "editor.background": window_bg,
        "editor.foreground": fg,
        "editorLineNumber.foreground": alpha(fg, .25),
        "editorLineNumber.activeForeground": accent,
        "editorCursor.foreground": accent,
        "editor.selectionBackground": selection,
        "editor.inactiveSelectionBackground": alpha(accent, .14),
        "editor.selectionHighlightBackground": alpha(accent, .14),
        "editor.wordHighlightBackground": alpha(fg, .08),
        "editor.wordHighlightStrongBackground": alpha(accent, .18),
        "editor.findMatchBackground": alpha(SYNTAX["string"], .4),
        "editor.findMatchHighlightBackground": alpha(SYNTAX["string"], .18),
        "editor.lineHighlightBackground": alpha(fg, .035),
        "editor.lineHighlightBorder": "#00000000",
        "editorIndentGuide.background1": alpha(fg, .06),
        "editorIndentGuide.activeBackground1": alpha(accent, .4),
        "editorWhitespace.foreground": alpha(fg, .12),
        "editorRuler.foreground": alpha(fg, .07),
        "editorBracketMatch.background": alpha(accent, .15),
        "editorBracketMatch.border": alpha(accent, .5),
        "editorBracketHighlight.foreground1": accent,
        "editorBracketHighlight.foreground2": SYNTAX["string"],
        "editorBracketHighlight.foreground3": SYNTAX["type"],
        "editorBracketHighlight.foreground4": SYNTAX["regex"],
        "editorGutter.addedBackground": accent,
        "editorGutter.modifiedBackground": SYNTAX["type"],
        "editorGutter.deletedBackground": SYNTAX["error"],
        "editorError.foreground": SYNTAX["error"],
        "editorWarning.foreground": SYNTAX["string"],
        "editorInfo.foreground": SYNTAX["type"],
        "editorOverviewRuler.border": "#00000000",
        "editorLink.activeForeground": accent_text,
        "scrollbar.shadow": "#00000000",
        "scrollbarSlider.background": alpha(fg, .1),
        "scrollbarSlider.hoverBackground": alpha(fg, .18),
        "scrollbarSlider.activeBackground": alpha(accent, .4),
        "minimap.background": window_bg,
        "minimap.selectionHighlight": selection,

        # popovers, menus, palette de commandes
        "editorWidget.background": popover_bg,
        "editorWidget.border": alpha(accent, .15),
        "editorSuggestWidget.background": popover_bg,
        "editorSuggestWidget.border": alpha(accent, .15),
        "editorSuggestWidget.selectedBackground": alpha(accent, .22),
        "editorSuggestWidget.highlightForeground": accent_text,
        "editorHoverWidget.background": popover_bg,
        "editorHoverWidget.border": alpha(accent, .15),
        "quickInput.background": popover_bg,
        "quickInputList.focusBackground": alpha(accent, .22),
        "quickInputTitle.background": surface,
        "pickerGroup.foreground": accent_text,
        "pickerGroup.border": border,
        "menu.background": popover_bg,
        "menu.foreground": fg,
        "menu.selectionBackground": accent,
        "menu.selectionForeground": accent_fg,
        "menu.separatorBackground": border,
        "menu.border": alpha(accent, .12),
        "menubar.selectionBackground": hover,
        "notifications.background": popover_bg,
        "notifications.border": alpha(accent, .15),
        "notificationCenterHeader.background": surface,
        "notificationsInfoIcon.foreground": SYNTAX["type"],
        "notificationsWarningIcon.foreground": SYNTAX["string"],
        "notificationsErrorIcon.foreground": SYNTAX["error"],

        # champs et boutons
        "input.background": alpha(fg, .06),
        "input.foreground": fg,
        "input.border": "#00000000",
        "input.placeholderForeground": alpha(fg, .4),
        "inputOption.activeBackground": alpha(accent, .25),
        "inputOption.activeBorder": "#00000000",
        "dropdown.background": popover_bg,
        "dropdown.border": "#00000000",
        "button.background": accent,
        "button.foreground": accent_fg,
        "button.hoverBackground": mix("#ffffff", accent, .12),
        "button.secondaryBackground": alpha(fg, .1),
        "button.secondaryForeground": fg,
        "button.secondaryHoverBackground": alpha(fg, .16),
        "checkbox.background": alpha(fg, .06),
        "checkbox.border": alpha(fg, .15),
        "badge.background": accent,
        "badge.foreground": accent_fg,
        "keybindingLabel.background": alpha(fg, .08),
        "keybindingLabel.border": "#00000000",
        "keybindingLabel.bottomBorder": "#00000000",

        # git et diff
        "gitDecoration.addedResourceForeground": accent_text,
        "gitDecoration.untrackedResourceForeground": accent_text,
        "gitDecoration.modifiedResourceForeground": SYNTAX["type"],
        "gitDecoration.deletedResourceForeground": SYNTAX["error"],
        "gitDecoration.conflictingResourceForeground": SYNTAX["number"],
        "gitDecoration.ignoredResourceForeground": alpha(fg, .35),
        "diffEditor.insertedTextBackground": alpha(accent, .15),
        "diffEditor.removedTextBackground": alpha(SYNTAX["error"], .15),

        # terminal
        "terminal.background": view_bg,
        "terminal.foreground": fg,
        "terminalCursor.foreground": accent,
        "terminal.selectionBackground": selection,
        "terminal.ansiBlack": panel,
        "terminal.ansiRed": SYNTAX["error"],
        "terminal.ansiGreen": accent,
        "terminal.ansiYellow": SYNTAX["string"],
        "terminal.ansiBlue": SYNTAX["type"],
        "terminal.ansiMagenta": SYNTAX["regex"],
        "terminal.ansiCyan": SYNTAX["function"],
        "terminal.ansiWhite": mix(fg, surface, .8),
        "terminal.ansiBrightBlack": SYNTAX["comment"],
        "terminal.ansiBrightRed": mix("#ffffff", SYNTAX["error"], .2),
        "terminal.ansiBrightGreen": accent_text,
        "terminal.ansiBrightYellow": mix("#ffffff", SYNTAX["string"], .2),
        "terminal.ansiBrightBlue": mix("#ffffff", SYNTAX["type"], .2),
        "terminal.ansiBrightMagenta": mix("#ffffff", SYNTAX["regex"], .2),
        "terminal.ansiBrightCyan": mix("#ffffff", SYNTAX["function"], .2),
        "terminal.ansiBrightWhite": fg,
    }


def token_colors(p):
    accent, fg = p["monbo_accent"], p["monbo_fg"]
    s = SYNTAX

    def rule(scope, color=None, style=None):
        settings = {}
        if color:
            settings["foreground"] = color
        if style is not None:
            settings["fontStyle"] = style
        return {"scope": scope, "settings": settings}

    return [
        rule(["comment", "punctuation.definition.comment"], s["comment"], "italic"),
        rule(["keyword", "storage", "storage.type", "keyword.control"], accent),
        rule(["keyword.operator", "punctuation"], s["operator"]),
        rule(["keyword.operator.new", "keyword.operator.expression",
              "keyword.operator.logical.python", "keyword.operator.wordlike"], accent),
        rule(["string", "markup.inline.raw"], s["string"]),
        rule(["string.regexp", "constant.character.escape", "constant.other.placeholder"], s["regex"]),
        rule(["constant", "constant.numeric", "constant.language", "support.constant"], s["number"]),
        rule(["entity.name.function", "support.function", "meta.function-call.generic",
              "variable.function"], s["function"]),
        rule(["entity.name.type", "entity.name.class", "support.type", "support.class",
              "entity.other.inherited-class", "storage.type.class"], s["type"]),
        rule(["variable", "meta.definition.variable"], fg),
        rule(["variable.parameter"], fg, "italic"),
        rule(["variable.language", "variable.language.this", "variable.language.self"], s["number"], "italic"),
        rule(["variable.other.property", "variable.other.object.property", "support.variable.property",
              "meta.object-literal.key", "support.type.property-name"], s["property"]),
        rule(["entity.name.tag", "meta.tag.sgml"], accent),
        rule(["entity.other.attribute-name"], s["type"], "italic"),
        rule(["entity.name.function.decorator", "meta.decorator", "punctuation.decorator",
              "entity.name.function.macro", "meta.preprocessor"], s["regex"]),
        rule(["entity.name.namespace", "entity.name.module"], s["type"]),
        rule(["invalid", "invalid.illegal"], s["error"]),
        # Sass / CSS
        rule(["variable.scss", "variable.css", "variable.argument.css"], s["regex"]),
        rule(["entity.other.attribute-name.class.css", "entity.other.attribute-name.id.css"], s["function"], ""),
        rule(["keyword.other.unit"], s["number"]),
        # Markdown
        rule(["markup.heading", "entity.name.section"], accent, "bold"),
        rule(["markup.bold"], None, "bold"),
        rule(["markup.italic"], None, "italic"),
        rule(["markup.underline.link", "string.other.link"], s["function"]),
        rule(["markup.quote"], s["comment"], "italic"),
        rule(["markup.list punctuation.definition.list"], accent),
        rule(["markup.inserted"], accent),
        rule(["markup.deleted"], s["error"]),
        rule(["markup.changed"], s["type"]),
    ]


def semantic_colors(p):
    s = SYNTAX
    return {
        "namespace": s["type"],
        "type": s["type"],
        "class": s["type"],
        "interface": s["type"],
        "enum": s["type"],
        "function": s["function"],
        "method": s["function"],
        "property": s["property"],
        "enumMember": s["number"],
        "parameter": {"foreground": p["monbo_fg"], "italic": True},
        "variable.readonly": s["number"],
        "selfParameter": {"foreground": s["number"], "italic": True},
        "decorator": s["regex"],
        "macro": s["regex"],
    }


def main(out_dir):
    p = read_palette()
    version = semver(VERSION)
    out = Path(out_dir)
    ext = out / "extension"
    (ext / "themes").mkdir(parents=True, exist_ok=True)

    theme = {
        "name": "Monbothemesamer",
        "type": "dark",
        "semanticHighlighting": True,
        "colors": workbench_colors(p),
        "tokenColors": token_colors(p),
        "semanticTokenColors": semantic_colors(p),
    }
    (ext / "themes" / "monbothemesamer-color-theme.json").write_text(
        json.dumps(theme, indent=2, ensure_ascii=False) + "\n")

    package = {
        "name": "monbothemesamer",
        "displayName": "Monbothemesamer",
        "description": "Thème sauge sombre assorti au thème GNOME Shell Monbothemesamer",
        "version": version,
        "publisher": "monbothemesamer",
        "engines": {"vscode": "^1.70.0"},
        "categories": ["Themes"],
        "contributes": {
            "themes": [{
                "label": "Monbothemesamer",
                "uiTheme": "vs-dark",
                "path": "./themes/monbothemesamer-color-theme.json",
            }]
        },
    }
    (ext / "package.json").write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n")

    # fichiers d'emballage .vsix (ce que produirait vsce package)
    (out / "extension.vsixmanifest").write_text(f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="monbothemesamer" Version="{version}" Publisher="monbothemesamer" />
    <DisplayName>Monbothemesamer</DisplayName>
    <Description xml:space="preserve">{package["description"]}</Description>
    <Categories>Themes</Categories>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{package["engines"]["vscode"]}" />
    </Properties>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code" />
  </Installation>
  <Dependencies />
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />
  </Assets>
</PackageManifest>
""")
    (out / "[Content_Types].xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension=".json" ContentType="application/json" />
  <Default Extension=".vsixmanifest" ContentType="text/xml" />
</Types>
""")


if __name__ == "__main__":
    main(sys.argv[1])
