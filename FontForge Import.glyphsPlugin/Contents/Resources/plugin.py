# encoding: utf-8

from __future__ import division, print_function, unicode_literals

import objc

from AppKit import NSMenuItem
from GlyphsApp import FILE_MENU, GetOpenFile, Glyphs
from GlyphsApp.plugins import GeneralPlugin
from SFDImport import SFDImport


class FontForgeImport(GeneralPlugin):

    @objc.python_method
    def settings(self):
        self.name = Glyphs.localize(
            {"en": "FontForge File...", "de": "FontForge-Datei..."}
        )

    @objc.python_method
    def start(self):
        newMenuItem = NSMenuItem.alloc().init()
        newMenuItem.setTitle_(self.name)
        newMenuItem.setAction_(self.showFileDialog_)
        newMenuItem.setTarget_(self)
        file_menu = Glyphs.menu[FILE_MENU]
        import_menu = file_menu.submenu().itemWithTitle_("Import")
        import_menu.append(newMenuItem)

    def showFileDialog_(self, sender):
        files = GetOpenFile(allowsMultipleSelection=True, filetypes=["sfd"])
        if files is None:
            return

        for file in files:
            SFDImport(file)

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__
