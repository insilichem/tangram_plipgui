#!/usr/bin/env python
# encoding: utf-8

"""
A functional wrapper for UCSF Chimera & PLIP
"""

import sys
from cStringIO import StringIO


class Mock(object):

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return Mock()

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
            return Mock()

    def __getitem__(self, *args, **kwargs):
        return

    def __setitem__(self, *args, **kwargs):
        return


# Patch unneeded PLIP dependencies
MOCK_MODULES = ('pymol',)
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)


import chimera
from plip.modules.preparation import PDBComplex
from plip.modules.chimeraplip import ChimeraVisualizer
from plip.modules.plipremote import VisualizerData
from plip.modules.report import StructureReport
from plip.modules import config as plip_config
plip_config.PLUGIN_MODE = True


def export_temporary_pdbstream(molecule):
    temp = StringIO()
    chimera.pdbWrite([molecule], molecule.openState.xform, temp)
    temp.seek(0)
    return temp


def analyze_with_plip(pdb):
    pdbcomplex = PDBComplex()
    pdbcomplex.load_pdb(pdb, as_string=True)
    pdbcomplex.analyze()
    pdbcomplex.sourcefiles['filename'] = '/dev/null'
    return pdbcomplex


def patch_molecule(molecule):
    # Create copies of original models in Chimera &
    # Patch molecule names to work with PLIP
    stream = export_temporary_pdbstream(molecule)
    pdb = chimera.PDBio()
    molcopy, _ = pdb.readPDBstream(stream, '{}.pdb'.format(molecule.name), 0)
    chimera.openModels.add(molcopy, sameAs=molecule)
    molcopy, = molcopy
    molcopy.name = 'PLIP-{}'.format(molecule.id)
    molecule.display = False
    return stream, molcopy


def depict_analysis(pdbcomplex, molecule):
    # Export analysis back to Chimera
    interactions = {}
    for interaction in pdbcomplex.interaction_sets:
        view_data = VisualizerData(pdbcomplex, interaction)
        viewer = ChimeraVisualizer(view_data, chimera, molecule.id)
        interactions[interaction] = viewer
        for method in ('cationpi', 'halogen', 'hbonds', 'hydrophobic',
                       'metal', 'sbridges', 'stacking', 'wbridges'):
            getattr(viewer, 'show_' + method)()

    report = StructureReport(pdbcomplex)

    return interactions, report


def do(molecules):
    molecules = [m for m in molecules if not getattr(m, 'plip_copy', None)]
    if len(molecules) != 1:
        raise ValueError('Only one model can be analyzed at the same time.')
    molecule = molecules[0]
    stream, patched_molecule = patch_molecule(molecule)
    molecule.plip_copy = patched_molecule
    analyzed = analyze_with_plip(stream.getvalue())
    stream.close()
    return depict_analysis(analyzed, patched_molecule)


def undo():
    pbnames = ['Water Bridges', 'Salt Bridges', 'Hydrophobic Interactions',
               'HalogenBonds', 'pi-Stacking', 'Hydrogen Bonds',
               'Metal Coordination', 'Cation-Pi']

    for m in chimera.openModels.list(modelTypes=[chimera.Molecule]):
        manager = m.pseudoBondMgr()
        for group in manager.pseudoBondGroups:
            if group.category.rsplit('-')[0] in pbnames:
                manager.deletePseudoBondGroup(group)
        if hasattr(m, 'plip_copy'):
            m.display = True
            delattr(m, 'plip_copy')
        if m.name.startswith('PLIP-'):
            m.destroy()

    chimera.viewer.updateCB(chimera.viewer)

if __name__ == '__main__':
    do()
