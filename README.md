# Tangram PLIP-GUI

An UCSF Chimera wrapper and GUI for PLIP.

## Known issues

PLIP, the backend for this extension, relies on openbabel as a dependency. However, using pychimera, openbabel and rdkit (used by other extensions in Tangram) is not possible. So, if you want to use PLIP-GUI, you have to uninstall rdkit (and stop using Tangram SubAlign, amongst others) and install openbabel:

```
# From the activated conda environment
conda remove rdkit
conda install -c openbabel openbabel
```
## Standalone installation on Ubuntu

```
sudo apt install python2.7-openbabel
pip install plip
pip install https://github.com/insilichem/libtangram/archive/v0.0.2.zip
pip install https://github.com/insilichem/tangram_plipgui/archive/v0.0.2.zip
```

Then, open UCSF Chimera and add ~/.local/lib/python2.7/site-packages in the
Favorites> Add to Favorites/Toolbar> Third-party plugin locations dialog.
If everything has worked so far, a new InsiliChem entry must appear in the
Chimera Tools menu.

## Standalone installation

If you want to install PLIP-GUI outside the Tangram Suite, follow these instructions:

Download this repo and install these packages as dependencies:

- plip itself
- openbabel & pybel

```
cd /your/chimera/extensions/directory
pip install -t . https://github.com/ssalentin/plip/archive/v1.3.3.zip --no-deps
# read http://openbabel.org/wiki/Category:Installation for openbabel
```

You can also use `pychimera` and `conda` to manage dependencies:

```
conda install -c openbabel openbabel
pychimera --gui  # to start patched UCSF Chimera
```
