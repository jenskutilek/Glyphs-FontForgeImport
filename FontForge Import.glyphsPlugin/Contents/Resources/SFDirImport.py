# MenuTitle: FontForge (SFDir) Import
from __future__ import annotations

import codecs
import os

from SFDImport import SFDImport


class SFDirImport(SFDImport):
    """Import a FontForge .sfdir folder by assembling it into a virtual SFD text.

    The parser in SFDImport works on a single SFD string. A .sfdir folder keeps
    the same data split into a font.props header plus one .glyph file per glyph,
    so we only need to provide a different data source -- no parser changes.
    """

    def read_sfd(self):
        header = self._read_text(os.path.join(self.sfd_path, "font.props"))
        glyph_parts = []
        for entry in sorted(os.listdir(self.sfd_path)):
            if not entry.endswith(".glyph"):
                continue
            glyph_parts.append(self._read_glyph(os.path.join(self.sfd_path, entry)))
        self.sfd = header + "\nBeginChars: %d\n" % len(glyph_parts)
        self.sfd += "\n".join(glyph_parts)
        self.sfd += "\nEndChars\n"

    def _read_text(self, path):
        try:
            with codecs.open(path, "rb", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with codecs.open(path, "rb", encoding="utf-7") as f:
                return f.read()

    def _read_glyph(self, path):
        text = self._read_text(path)
        if "\nLayer:" not in text:
            return text
        # The parser only knows Back/Fore. Skip any additional layer segments
        # ("Layer: N" ... "EndSplineSet") so their outlines are not drawn
        # into the foreground layer.
        lines = []
        in_extra_layer = False
        for line in text.splitlines():
            if line.startswith("Layer:"):
                in_extra_layer = True
                continue
            if in_extra_layer:
                if line.strip() == "EndSplineSet":
                    in_extra_layer = False
                continue
            lines.append(line)
        return "\n".join(lines)
