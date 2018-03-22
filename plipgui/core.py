#!/usr/bin/env python
# encoding: utf-8


from __future__ import print_function, division
# Python stdlib
import contextlib
from cStringIO import StringIO
import sys
from tkFileDialog import asksaveasfilename
import Tkinter as tk
# Chimera stuff
import chimera
from Midas import MidasError
# Additional 3rd parties


class _Mock(object):

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return _Mock()

    @classmethod
    def __getattr__(cls, name):
        if name in ('__file__', '__path__'):
            return '.',
        elif name == '__all__':
            return []
        elif name[0] == name[0].upper():
            mockType = type(name, (), {})
            mockType.__module__ = __name__
            return mockType
        else:
            return _Mock()

    def __getitem__(self, *args, **kwargs):
        return

    def __setitem__(self, *args, **kwargs):
        return


# Patch unneeded PLIP dependencies
MOCK_MODULES = ['pymol']
sys.modules.update((mod_name, _Mock()) for mod_name in MOCK_MODULES)

from plip.modules.preparation import PDBComplex
from plip.modules.chimeraplip import ChimeraVisualizer
from plip.modules.plipremote import VisualizerData
from plip.modules.report import StructureReport, BindingSiteReport
from plip.modules import config as plip_config
plip_config.PLUGIN_MODE = True


class Controller(object):

    _PBNAMES = ('Water Bridges', 'Salt Bridges', 'Hydrophobic Interactions',
                'HalogenBonds', 'pi-Stacking', 'Hydrogen Bonds', 'Metal Coordination',
                'Cation-Pi')
    _METHODS = ('wbridges', 'sbridges', 'hydrophobic', 'halogen', 'stacking',
                'hbonds', 'metal', 'cationpi')
    _INTERACTIONS = ('waterbridge', 'saltbridge', 'hydrophobic', 'halogen',
                     'pistacking', 'hbond', 'metal', 'pication')
    _PBNAMES_TO_METHODS = dict((p, m) for (p, m) in zip(_PBNAMES, _METHODS))
    _METHODS_TO_PBNAMES = dict((m, p) for (p, m) in zip(_PBNAMES, _METHODS))
    _PBNAMES_TO_INTERACTIONS = dict((p, i) for (p, i) in zip(_PBNAMES, _INTERACTIONS))
    _INTERACTIONS_TO_PBNAMES = dict((i, p) for (p, i) in zip(_PBNAMES, _INTERACTIONS))

    def __init__(self, gui, model=None, *args, **kwargs):
        self.gui = gui
        self.gui_results = None
        self.model = None
        self._molecule = None
        self._interactions = None
        self.set_mvc()

    def set_mvc(self):
        # Buttons callbacks
        self.gui.buttonWidgets['Run'].configure(command=self.run)

    def run(self):
        from gui import PLIPResultsDialog
        self.check()
        self.model = Model(self.molecule)

        dialog = PLIPResultsDialog(molecule=self.molecule, controller=self)
        dialog.enter()
        dialog.buttonWidgets['Close'].configure(command=self._on_close_cb)
        dialog.buttonWidgets['Save'].configure(command=self._on_save_cb)
        dialog.fillInData(self.binding_sites)
        self.gui_results = dialog

    def depict(self, binding_site):
        interaction_set, viewer, view_data = self.interactions[binding_site]
        for method in self._METHODS:
            getattr(viewer, 'show_' + method)()

        self.focus_binding_site(binding_site)

    def focus_binding_site(self, binding_site):
        resname, chain, resid = binding_site.split(':')
        try:
            spec = ':{}.{}'.format(resid, chain) if chain else ':{}'.format(resid)
            chimera.runCommand('show {} zr < 5'.format(spec))
            chimera.runCommand('focus {} zr < 5'.format(spec))
        except MidasError:
            spec = ':{}'.format(resname)
            chimera.runCommand('show {} zr < 5'.format(spec))
            chimera.runCommand('focus {} zr < 5'.format(spec))

    def focus_interaction(self, interaction):
        pass

    @property
    def molecule(self):
        if self._molecule is None:
            self._molecule = self.gui.ui_molecules.getvalue()
        return self._molecule

    @property
    def binding_sites(self):
        if self.model is None:
            raise ValueError("You must run .run() first!")
        return self.model.complex.interaction_sets.keys()

    @property
    def interactions(self):
        if self.model is None:
            raise ValueError("You must run .run() first!")
        if self._interactions is not None:
            return self._interactions

        interactions = {}
        for binding_site, interaction_set in self.model.complex.interaction_sets.items():
            report = BindingSiteReport(interaction_set)
            view_data = VisualizerData(self.model.complex, binding_site)
            viewer = ChimeraVisualizer(view_data, chimera, self.molecule.id)
            interactions[binding_site] = report, viewer, view_data
        self._interactions = interactions
        return interactions

    def check(self):
        """
        Basic tests to assert everything is in order.
        """
        if not self.molecule:
            raise ValueError("No molecule selected")
        return True

    def _on_close_cb(self, *args):


        manager = self.model.molecule_copy.pseudoBondMgr()
        for group in manager.pseudoBondGroups:
            if group.category.rsplit('-', 1)[0] in self._PBNAMES_TO_METHODS:
                manager.deletePseudoBondGroup(group)

        self.model.molecule.display = True
        chimera.openModels.remove(self.model.molecule_copy)
        self.gui_results.Close()

    def _on_save_cb(self, *args):
        path = asksaveasfilename(parent=self.gui_results.canvas)
        with open(path, 'w') as f:
            lines = self.model.report().txtreport
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('**') and line.endswith('**'):
                    lines[i] = line + '\n'
            lines.insert(2, "Generated with InsiliChem's Tangram PLIP GUI.")
            f.write('\n'.join(lines))
        chimera.statusline.show_message('Report written to {}'.format(path),
                                        blankAfter=5)

class Model(object):


    def __init__(self, molecule, *args, **kwargs):
        self.molecule = molecule
        self.molecule_copy = None
        self.complex = None
        self.run()

    def run(self):
        stream = self._patch_molecule()
        pdbcomplex = PDBComplex()
        pdbcomplex.load_pdb(stream.getvalue(), as_string=True)
        pdbcomplex.analyze()
        pdbcomplex.sourcefiles['filename'] = '/dev/null'
        stream.close()
        self.complex = pdbcomplex

    def report(self):
        if self.complex is not None:
            return StructureReport(self.complex)

    def _patch_molecule(self):
        # Create copies of original models in Chimera &
        # Patch molecule names to work with PLIP
        self.molecule_copy, stream = _duplicate_molecule(self.molecule)
        self.molecule_copy.name = 'PLIP-{}'.format(self.molecule.id)
        self.molecule.display = False
        return stream


###########
# Helpers #
###########


def _duplicate_molecule(molecule):
    """
    Export a PDB copy of the given molecule to a StringIO object
    and load it back. We use this instead of Molecule.copy_molecule
    because PLIP gets the very same PDB copy, and sometimes this
    results in different serial numbers
    """
    stream = StringIO()
    chimera.pdbWrite([molecule], molecule.openState.xform, stream)
    stream.seek(0)
    pdb = chimera.PDBio()
    molcopy, _ = pdb.readPDBstream(stream, '{}.pdb'.format(molecule.name), 0)
    chimera.openModels.add(molcopy, sameAs=molecule)
    return molcopy[0], stream


def cmd_plip(selection, report=True):
    from plipgui.plip4chimera import do as do_plip
    molecules = selection.molecules()
    interactions, reporter = do_plip(molecules)
    msg = 'Analyzed {} interaction sets!'.format(len(interactions.keys()))
    if report in (True, 'stdout'):
        reporter.write_txt(as_string=True)
    elif report.lower in ('replylog', 'log', 'reply'):
        chimera.replyobj.info(''.join(reporter.txtreport))
        chimera.replyobj.status(msg)
    elif report:
        with open(report, 'w') as f:
            f.write(''.join(reporter.txtreport))

    chimera.statusline.show_message(msg, blankAfter=5)


def cmd_unplip(*args):
    from plipgui.plip4chimera import undo
    undo()


@contextlib.contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass