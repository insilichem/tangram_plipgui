#!/usr/bin/env python
# encoding: utf-8


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
from libplume.ui import PlumeBaseDialog
from core import Controller


ui = None
def showUI(callback=None):
    if chimera.nogui:
        tk.Tk().withdraw()
    global ui
    if not ui:
        ui = PLIPInputDialog()
    _ = Controller(gui=ui)
    ui.enter()
    if callback:
        ui.addCallback(callback)


class PLIPInputDialog(PlumeBaseDialog):

    buttons = ('Run', 'Close')

    def __init__(self, *args, **kwargs):
        # GUI init
        self.title = 'Plume PLIP'
        self.controller = None

        # Fire up
        super(PLIPInputDialog, self).__init__(*args, **kwargs)

    def fill_in_ui(self, parent):
        input_frame = tk.LabelFrame(self.canvas, text='Select a protein-ligand complex')
        self.ui_molecules = MoleculeScrolledListBox(input_frame)
        self.ui_molecules.filtFunc = lambda m: not m.name.startswith('PLIP-')
        self.ui_molecules.refresh()
        self.ui_molecules.pack(padx=5, pady=5, expand=True, fill='both')

        input_frame.pack(padx=5, pady=5, expand=True, fill='both')

    def Apply(self):
        pass

    def Run(self):
        self.Apply()
        self.Close()
    
    def Close(self):
        global ui
        ui = None
        super(PLIPInputDialog, self).Close()

    def load_controller(self):
        pass


class PLIPResultsDialog(PlumeBaseDialog):

    buttons = ('Save', 'Close')
    
    def __init__(self, molecule=None, controller=None, *args, **kwargs):
        self.molecule = molecule
        self.controller = controller
        self.title = 'PLIP results'
        if molecule:
            self.title += ' for {}'.format(molecule.name)

        self._binding_site = tk.StringVar()

        # Fire up
        super(PLIPResultsDialog, self).__init__(*args, **kwargs)

    def fill_in_ui(self, parent):
        self.ui_binding_sites_dropdown = OptionMenu(self.canvas,
                                                 labelpos='w',
                                                 label_text='Select binding site:',
                                                 menubutton_textvariable=self._binding_site,
                                                 command=self._binding_site_cb)
        self.ui_binding_sites_dropdown.pack(padx=5, pady=5)

        self.ui_tables_frame = tk.LabelFrame(self.canvas, text='Found interactions')
        self.tables = {}
        
    def fillInData(self, binding_sites):
        binding_sites.sort()
        self.ui_binding_sites_dropdown.setitems(binding_sites)
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
              'format': '%s',
              'refresh': False}
        for interaction in self.controller._INTERACTIONS:
            info = getattr(report, interaction + '_info', None)
            if not info:
                continue
            t = self.tables[interaction] = SortableTable(self.ui_tables_frame)
            t.checked = tk.IntVar()
            t.checked.set(1)
            t.label = tk.Checkbutton(self.ui_tables_frame, text=interaction.title(),
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
            self.canvas.after(1000, t.requestFullWidth)

        self.ui_tables_frame.pack(expand=True, fill='both', padx=5, pady=5)
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