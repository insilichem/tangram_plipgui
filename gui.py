#!/usr/bin/env python
# encoding: utf-8

# Get used to importing this in your Py27 projects!
from __future__ import print_function, division 
# Python stdlib
import Tkinter as tk
from Pmw import OptionMenu
from operator import itemgetter
# Chimera stuff
import chimera
from chimera.baseDialog import ModelessDialog
from chimera.widgets import MoleculeScrolledListBox, SortableTable
# Additional 3rd parties

# Own
from core import Controller

"""
The gui.py module contains the interface code, and only that. 
It should only 'draw' the window, and should NOT contain any
business logic like parsing files or applying modifications
to the opened molecules. That belongs to core.py.
"""

# This is a Chimera thing. Do it, and deal with it.
ui = None
def showUI(callback=None):
    """
    Requested by Chimera way-of-doing-things
    """
    if chimera.nogui:
        tk.Tk().withdraw()
    global ui
    if not ui: # Edit this to reflect the name of the class!
        ui = PLIPInputDialog()
    _ = Controller(gui=ui)
    ui.enter()
    if callback:
        ui.addCallback(callback)

ENTRY_STYLE = {
    'background': 'white',
    'borderwidth': 1,
    'highlightthickness': 0,
    'insertwidth': 1,
}
BUTTON_STYLE = {
    'borderwidth': 1,
    'highlightthickness': 0,
}

class PLIPInputDialog(ModelessDialog):

    """
    To display a new dialog on the interface, you will normally inherit from
    ModelessDialog class of chimera.baseDialog module. Being modeless means
    you can have this dialog open while using other parts of the interface.
    If you don't want this behaviour and instead you want your extension to 
    claim exclusive usage, use ModalDialog.
    """

    buttons = ('Run', 'Close')
    default = None
    help = 'https://www.insilichem.com'

    def __init__(self, *args, **kwarg):
        # GUI init
        self.title = 'Plume PLIP'
        self.controller = None

        # Fire up
        ModelessDialog.__init__(self)
        if not chimera.nogui:  # avoid useless errors during development
            chimera.extension.manager.registerInstance(self)

        # Fix styles
        self._fix_styles()

    def _initialPositionCheck(self, *args):
        try:
            ModelessDialog._initialPositionCheck(self, *args)
        except Exception as e:
            if not chimera.nogui:  # avoid useless errors during development
                raise e

    def _fix_styles(self):
        for name, btn in self.buttonWidgets.items():
            btn.configure(**BUTTON_STYLE)

    def fillInUI(self, parent):
        """
        This is the main part of the interface. With this method you code
        the whole dialog, buttons, textareas and everything.
        """
        # Create main window
        self.parent = parent
        self.canvas = tk.Frame(parent)
        self.canvas.pack(expand=True, fill='both')
        
        input_frame = tk.LabelFrame(self.canvas, text='Select a protein-ligand complex')
        input_frame.rowconfigure(0, weight=1)
        input_frame.columnconfigure(1, weight=1)
        self.molecules = MoleculeScrolledListBox(input_frame)
        self.molecules.filtFunc = lambda m: not m.name.startswith('PLIP-')
        self.molecules.refresh()
        self.molecules.grid(row=0, columnspan=3, padx=5, pady=5, sticky='news')

        input_frame.pack()

    def Apply(self):
        """
        Default! Triggered action if you click on an Apply button
        """
        pass

    def Run(self):
        """
        Default! Triggered action if you click on an OK button
        """
        self.Apply()
        self.Close()

    def Close(self):
        """
        Default! Triggered action if you click on the Close button
        """
        global ui
        ui = None
        ModelessDialog.Close(self)
        self.destroy()

    # Below this line, implement all your custom methods for the GUI.
    def load_controller(self):
        pass


class PLIPResultsDialog(ModelessDialog):

    buttons = ('Save', 'Close')
    def __init__(self, parent=None, molecule=None, controller=None, *args, **kwargs):
        self.parent = parent
        self.molecule = molecule
        self.controller = controller
        self.title = 'PLIP results'
        if molecule:
            self.title += ' for {}'.format(molecule.name)

        self._binding_site = tk.StringVar()

        # Fire up
        ModelessDialog.__init__(self, *args, **kwargs)
        if not chimera.nogui:
            chimera.extension.manager.registerInstance(self)

    def _initialPositionCheck(self, *args):
        try:
            ModelessDialog._initialPositionCheck(self, *args)
        except Exception as e:
            if not chimera.nogui:
                raise e

    def fillInUI(self, parent):
        self.canvas = tk.Frame(parent)
        self.canvas.pack(expand=True, fill='both', padx=5, pady=5)
        self.canvas.columnconfigure(0, weight=1)

        self.binding_sites_dropdown = OptionMenu(self.canvas,
                                                 labelpos='w',
                                                 label_text='Select binding site:',
                                                 menubutton_textvariable=self._binding_site,
                                                 command=self._binding_site_cb)
        self.binding_sites_dropdown.pack(padx=5, pady=5)

        self.tables_frame = tk.LabelFrame(parent, text='Found interactions')
        self.tables = {}
        
    def fillInData(self, binding_sites):
        binding_sites.sort()
        self.binding_sites_dropdown.setitems(binding_sites)
        self._binding_site.set(binding_sites[0])
        self._binding_site_cb(binding_sites[0])

    def _clear_tables(self):
        for table in self.tables.values():
            table.label.destroy()
            del table.checked
            table.destroy()
        self.tables.clear()

    def _binding_site_cb(self, binding_site):
        self._clear_tables()
        report = self.controller.interactions[binding_site][0]
        kw = {'headerAnchor': 'center', 
              'font': ('Courier', 10),
              'anchor': 'e',
              'format': '%s'}
        for interaction in self.controller._INTERACTIONS:
            info = getattr(report, interaction + '_info', None)
            if not info:
                continue
            t = self.tables[interaction] = SortableTable(self.tables_frame)
            t.checked = tk.IntVar()
            t.checked.set(1)
            t.label = tk.Checkbutton(self.tables_frame, text=interaction.title(),
                                     variable=t.checked, command=self._on_checkbox_cb)
            t.label.pack()

            # Add columns
            for i, header in enumerate(getattr(report, interaction + '_features')):
                t.addColumn(header, _itemgetter(i), **kw)
            # Populate table data
            t.setData(info)
            try:
                t.launch(selectMode='single')
            except tk.TclError:
                t.refresh(rebuild=True)
            t.pack(expand=True, fill='both', padx=5, pady=5)
            self.canvas.after(100, t.requestFullWidth)

        self.tables_frame.pack(expand=True, fill='both', padx=5, pady=5)
        self.controller.depict(binding_site)

    def _on_checkbox_cb(self, *args):
        mgr = self.controller.model.molecule_copy.pseudoBondMgr()
        for title, table in self.tables.items():
            key = self.controller._INTERACTIONS_TO_PBNAMES[title.lower()]
            for name, pbgroup in mgr.pseudoBondGroupsMap.items():
                if name.lower().startswith(key.lower()):
                    pbgroup.display = True if table.checked.get() else False


def _itemgetter(i):
    def fn(row):
        value = row[i]
        if isinstance(value, (tuple, list)):
            return value,
        return value
    return fn