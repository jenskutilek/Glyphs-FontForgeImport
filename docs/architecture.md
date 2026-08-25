# FontForge Import — Technical Overview

This document describes how the FontForge Import plugin is structured and how it
handles the FontForge (SFD / SFDir) formats, including the workarounds required
for modern Glyphs versions.

## Module layout

All Python code lives in
`FontForge Import.glyphsPlugin/Contents/Resources/`:

| Module        | Responsibility                                              |
|---------------|-------------------------------------------------------------|
| `plugin.py`   | Glyphs plugin entry point: menu items and file/folder dialogs |
| `SFDImport.py`| The SFD text parser: header and glyph blocks                 |
| `SFDirImport.py` | Assembles a `.sfdir` folder into an SFD text, then reuses `SFDImport` |

The parser never depends on FontForge or any third-party library; it only uses
the Glyphs SDK (`GlyphsApp`), `AppKit`, and the standard library.

## The SFD parser (`SFDImport.py`)

`SFDImport` is built around one core idea: an SFD file is parsed into a single
string (`self.sfd`) which is then split into a header and a glyph section and
processed line by line.

```
__init__(path)
  read_sfd()            # load the file into self.sfd
  import_sfd()
    GSFont()            # create a new font
    import_header(header)  # font/master/instance attributes + Private section
    import_glyphs(chars)   # one glyph block per StartChar...EndChar
```

### Header (`import_header`)

- Parses `key: value` lines.
- Three lookup tables map SFD keys to Glyphs attributes:
  - `header_font_map` → `GSFont` properties (e.g. `FamilyName`, `Copyright`)
  - `header_master_map` → `GSFontMaster` properties (e.g. `Ascent`, `Descent`,
    `ItalicAngle`; note that `Descent` and `ItalicAngle` are sign-flipped)
  - `header_instance_map` → `GSInstance` properties (e.g. `FontName`, `Weight`)
- Tracks `BeginPrivate` / `EndPrivate` state. Inside the Private section it maps
  `BlueValues` to alignment zones and `StdHW`/`StdVW`/`StemSnapH`/`StemSnapV`
  to stem definitions. On Glyphs 3+ (`buildNumber >= 3000`) stems/zones via the
  new `GSMetric` API are not implemented yet (see the FIXME in the source).
- `Grid ... EndSplineSet` blocks are ignored.

### Glyphs (`import_glyphs`)

Each glyph block starts with `StartChar:` and ends with `EndChar`. Handled
lines:

| Line         | Action                                        |
|--------------|-----------------------------------------------|
| `StartChar:` | Create `GSGlyph`, add to font, get layer      |
| `Encoding:`  | Set unicode (hex), record gid → name          |
| `Width:`     | Set layer width                               |
| `Fore`       | Switch pen to the foreground layer            |
| `Back`       | Switch pen to the background layer            |
| `Refer:`     | Add a `GSComponent` (see below)               |
| `SplineSet` … `EndSplineSet` | Feed `m`/`l`/`c` commands into a pen |

#### Glyphs 4.1: `append` no longer creates a layer

In Glyphs 3, `font.glyphs.append(glyph)` automatically created a master layer,
so `glyph.layers[0]` was always valid. **In Glyphs 4.1 the glyph is added with
zero layers.** The parser therefore adds a fallback:

```python
self.font.glyphs.append(glyph)
glyph = self.font.glyphs[name]
if not glyph.layers:
    glyph.layers.append(GSLayer())   # SDK associates it with masters[0]
layer = glyph.layers[0]
```

`glyph.layers.append(GSLayer())` goes through the SDK proxy, which sets
`associatedMasterId` to the first master automatically. On Glyphs 3 the branch
is never taken.

#### Component references (`Refer:`)

FontForge stores glyphs that consist of other glyphs (e.g. `i` = dotlessi + a
dot accent) as references, not outlines:

```
StartChar: i
Fore
Refer: 121 775 S 1 0 0 1 4 22 2
Refer: 76 305 N 1 0 0 1 0 0 3
EndChar
```

A `Refer` line is:

```
Refer: <gid> <flags> <S/N> <a> <b> <c> <d> <e> <f> <layer>
```

The first field is the **SFD-internal glyph index** (the 4th field of
`Encoding:`), not a name. Because a referenced glyph may appear *later* in the
file, `import_glyphs` first scans the whole glyph section to build an
index → name map (`gid_to_name`), then converts each `Refer` into a
`GSComponent` with the 6-value transform `(a b c d e f)` and appends it to the
current layer's shapes. Glyphs resolves the component chain recursively.

## SFDir support (`SFDirImport.py`)

A `.sfdir` folder stores the same data split across many files:

```
font.sfdir/
  font.props      # identical to the SFD header (SplineFontDB: ...)
  A.glyph         # one StartChar...EndChar block per glyph
  ...
```

`SFDirImport` subclasses `SFDImport` and only overrides the data source:

```python
class SFDirImport(SFDImport):
    def read_sfd(self):
        header = read("font.props")
        glyphs  = [read(g) for g in sorted("*.glyph")]
        self.sfd = header + "\nBeginChars: N\n" + "\n".join(glyphs) + "\nEndChars\n"
```

Everything downstream (`import_sfd`, `import_header`, `import_glyphs`) is
inherited unchanged. The filename of a glyph file does **not** match its
`StartChar` (e.g. `A.glyph` contains `StartChar: a`), which is why the parser
always trusts the file contents.

One format quirk is handled during assembly: some `.glyph` files contain extra
layer segments (`Layer: N ... EndSplineSet`). The SFD parser only understands
`Fore`/`Back`, so those segments are stripped out in `read_sfd` to keep their
outlines out of the foreground layer.

## Menu integration (`plugin.py`)

The plugin adds two items under **File > Import**:

- `FontForge File...` (`GetOpenFile`, restricted to `sfd`)
- `FontForge Folder (SFDir)...` (custom `NSOpenPanel`)

### Localized "Import" menu

`Glyphs.menu[FILE_MENU]` returns the File menu item. The Import submenu is
located with:

```python
import_menu = file_menu.submenu().itemWithTitle_("Import")
if import_menu is None:
    import_menu = file_menu.submenu().itemWithTag_(22)
```

On non-English systems the Import item's title is localized (e.g. 匯入, 导入,
Importieren), so `itemWithTitle_("Import")` returns `None`. The Import item has
a stable menu tag of **22** across Glyphs 3 and 4, so that is used as a
language-independent fallback.

### Selecting `.sfdir` folders

macOS treats any directory whose name ends in an extension (`.sfdir`) as a
package/bundle, which `NSOpenPanel`'s directory mode disables by default. The
folder picker therefore configures the panel explicitly:

```python
panel = NSOpenPanel.new()
panel.setCanChooseFiles_(False)
panel.setCanChooseDirectories_(True)
panel.setTreatsFilePackagesAsDirectories_(True)   # make .sfdir selectable
panel.setAllowsMultipleSelection_(True)
```

Without `setTreatsFilePackagesAsDirectories_(True)` the `.sfdir` folders stay
greyed out in the open dialog.

## Known limitations

- Stems and alignment zones on Glyphs 3+ are not written yet (FIXME in
  `SFDImport.py`).
- Smart components, glyph-level attributes beyond encoding/width, and font-wide
  kerning are not imported.
- Additional layers beyond Fore/Back in `.glyph` files are skipped.
- `UnicodeInterp`, `NameList`, and other OpenType-specific header entries are
  ignored.
