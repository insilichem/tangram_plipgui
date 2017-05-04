#!/usr/bin/env python
# encoding: utf-8

"""
This is the file that Chimera searches for to load new extensions
at runtime. Normally, you will only need to edit:

- the returned strings in name() and description() methods

- the name of the class in both the class statement and the 
  registerExtension() call at the end of the file.

"""

# get used to importing this in your Py27 projects!
from __future__ import print_function, division 
import chimera
from Midas.midas_text import doExtensionFunc, addCommand
from plipgui.core import cmd_plip, cmd_unplip


class PLIPExtension(chimera.extension.EMO):

    def name(self):
        return 'Plume PLIP'

    def description(self):
        return 'Protein-Ligand Interaction Profiler'

    def categories(self):
        return ['InsiliChem']

    def icon(self):
        # To be implemented
        return

    def activate(self):
        # Don't edit unless you know what you're doing
        self.module('gui').showUI()


def _cmd_plip(cmdName, args):
    doExtensionFunc(cmd_plip, args, specInfo=[("selSpec", "selection", None)])


def _cmd_unplip(cmdName, args):
    doExtensionFunc(cmd_unplip, args)


addCommand("plip", _cmd_plip, revFunc=_cmd_unplip)
chimera.extension.manager.registerExtension(PLIPExtension(__file__))