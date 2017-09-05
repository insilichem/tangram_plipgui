# Plume PLIP-GUI

An UCSF Chimera wrapper and GUI for PLIP.

## Dependencies that must be manually installed

Also:

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
