# encoding: utf-8

from __future__ import division, print_function, unicode_literals

import objc

from AppKit import NSMenuItem, NSModalResponseOK, NSOpenPanel
from GlyphsApp import FILE_MENU, GetOpenFile, Glyphs
from GlyphsApp.plugins import GeneralPlugin
from SFDImport import SFDImport
from SFDirImport import SFDirImport


class FontForgeImport(GeneralPlugin):

    @objc.python_method
    def settings(self):
        self.name = Glyphs.localize(
            {"en": "FontForge File...", "de": "FontForge-Datei..."}
        )
        self.sfdirName = Glyphs.localize(
            {"en": "FontForge Folder (SFDir)...", "de": "FontForge-Ordner (SFDir)..."}
        )

    @objc.python_method
    def start(self):
        self._addMenuItem(self.name, self.showFileDialog_)
        self._addMenuItem(self.sfdirName, self.showFileDialogFolder_)

    @objc.python_method
    def _addMenuItem(self, title, action):
        newMenuItem = NSMenuItem.alloc().init()
        newMenuItem.setTitle_(title)
        newMenuItem.setAction_(action)
        newMenuItem.setTarget_(self)
        file_menu = Glyphs.menu[FILE_MENU]
        import_menu = file_menu.submenu().itemWithTitle_("Import")
        if import_menu is None:
            import_menu = file_menu.submenu().itemWithTag_(22)
        import_menu.append(newMenuItem)

    def showFileDialog_(self, sender):
        files = GetOpenFile(allowsMultipleSelection=True, filetypes=["sfd"])
        if files is None:
            return

        for file in files:
            SFDImport(file)

    def showFileDialogFolder_(self, sender):
        panel = NSOpenPanel.new()
        panel.setCanChooseFiles_(False)
        panel.setCanChooseDirectories_(True)
        panel.setCanCreateDirectories_(True)
        panel.setTreatsFilePackagesAsDirectories_(True)
        panel.setAllowsMultipleSelection_(True)
        if panel.runModal() != NSModalResponseOK:
            return

        for folder in panel.filenames():
            SFDirImport(folder)

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__
