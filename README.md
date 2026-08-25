# Glyphs-FontForgeImport

Importer for FontForge (SFD and SFDir) files in Glyphs.

I wanted to be able to quickly look at FontForge files without going through the hassle to install FontForge on macOS, so I hacked this little plugin. It is not perfect yet, but imports the glyph outlines well enough.

Let me know if something is missing.

## Usage

- **File > Import > FontForge File...** — import a `.sfd` file.
- **File > Import > FontForge Folder (SFDir)...** — import a `.sfdir` folder (a directory holding a `font.props` header plus one `.glyph` file per glyph).

Works with Glyphs 3 and Glyphs 4.

## What gets imported

- Font-level attributes: family name, copyright, note, ...
- Master-level metrics: ascender, descender, italic angle
- `BeginPrivate` section: alignment zones (`BlueValues`), stems (`StdHW`, `StdVW`, `StemSnapH`, `StemSnapV`)
- Glyph outlines (`SplineSet`), foreground and background layers, widths, encodings
- Component references (`Refer` lines), e.g. for `i`, `j`, `f`, and PUA variants

See `docs/architecture.md` for a technical overview.

## Installation

1. Download the plugin from the [latest release](https://github.com/jenskutilek/Glyphs-FontForgeImport/releases).
2. Double-click the `.glyphsPlugin` file to install it into `~/Library/Application Support/Glyphs 3/Plugins`.
3. Restart Glyphs.
