#!/usr/bin/env python
# encoding: utf-8


from __future__ import print_function, division
import chimera
from Midas.midas_text import doExtensionFunc, addCommand
from plipgui.core import cmd_plip, cmd_unplip


class PLIPExtension(chimera.extension.EMO):

    def name(self):
        return 'Tangram PLIP'

    def description(self):
        return 'Protein-Ligand Interaction Profiler'

    def categories(self):
        return ['InsiliChem']

    def icon(self):
        return

    def activate(self):
        self.module('gui').showUI()


def _cmd_plip(cmdName, args):
    doExtensionFunc(cmd_plip, args, specInfo=[("selSpec", "selection", None)])


def _cmd_unplip(cmdName, args):
    doExtensionFunc(cmd_unplip, args)


addCommand("plip", _cmd_plip, revFunc=_cmd_unplip)
chimera.extension.manager.registerExtension(PLIPExtension(__file__))