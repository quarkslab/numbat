# Numbat

<img align="right" src="numbat.png" width="250">

Numbat is an API to create and manipulate Sourcetrail databases. [Sourcetrail](https://github.com/CoatiSoftware/Sourcetrail) is a code source
explorer which allows users to navigate through the different components (functions, classes, types, etc.) easily. 

Numbat main goal is to offer a full-python SDK given the fact that the current one, SourcetrailDB cannot be used anymore efficiently. It is not user-friendly at first sight, need to be compiled to provide Python bindings and, moreover, it is no longer maintained. Finally, we have added some little new features as finding an element in the database. 

With Numbat, you will be able to visualize your data quickly with the nice graphical Sourcetrail interface. For example, [Pyrrha](https://github.com/quarkslab/pyrrha) uses Numbat to map firmware structure.



## Installation 

Numbat is available on `pypi`.
```bash
pip install numbat
```

### From sources
You can also install it from the `git` repository. Either using the following oneliner:
```bash
pip install 'numbat @ git+https://github.com/quarkslab/numbat'
```
or doing it in few steps:
```bash
# Download the repo
git clone https://gitlab.qb/firmware-re/cartography/numbat
cd numbat
# Install numbat locally
pip install .
```

### Build Documentation
If you want to build the documentation by first installing Numbat with the required `[doc]` dependencies and then serve the documentation on a local server.

```bash
# if you already have a local clone of the project
cd NUMBAT_DIR
pip install .[doc]

# otherwise
pip install 'numbat[doc]'

# serve doc locally
mkdocs serve
```

## Basic Usage

A complete usage with examples is available in the [documentation](getting_started.md) but here is a quick usage to begin with Numbat.

To use Numbat, you must first create a `SourcetrailDB` object and either create a new database or open an existing one:
```python
from pathlib import Path
from numbat import SourcetrailDB

db_path = Path('my_database')
try:
    # Create a new database
    srctrl = SourcetrailDB.create(db_path)
except FileExistsError:
    # Database already exists, open it and remove the entire content with clear
    srctrl = SourcetrailDB.open(db_path)
    srctrl.clear()
```

You could also use this one-liner to open the database quicker:
```python hl_lines="5"
from pathlib import Path
from numbat import SourcetrailDB

srctrl = SourcetrailDB.open(Path('my_database'), clear=True)
```

Once the database is open, you can add one or more source files in the database using the following snippet:
```python
file_id = srctrl.record_file(Path('my_file.c'))
srctrl.record_file_language(file_id, 'C')
``` 

To populate the database, it is possible to record different symbols such as class or function like this:
```python
symbol_id = srctrl.record_class(name="MyClass", is_indexed=True)
# if you have a source code, you can add the location of your symbol definition
srctrl.record_symbol_location(symbol_id, file_id, 2, 7, 2, 12)
# and your symbol scope
srctrl.record_symbol_scope_location(symbol_id, file_id, 2, 1, 7, 1)
``` 

Once the database is filled with information, it must be saved and close like this:
```python 
srctrl.commit()
srctrl.close()
```

## Authors
- Sami Babigeon (@sbabigeon), Quarkslab
- Eloïse Brocas (@ebrocas), Quarkslab

The logo is a creation of Benoît Forgette and Sami Babigeon.
