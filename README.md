# Numbat

<img align="right" src="https://gitlab.qb/sbabigeon/numbat/-/raw/main/numbat.png" width="250" heigh="250">

## Introduction

The goal of this project is to provide a new API to Sourcetrail software. Sourcetrail is a archived project
so the API is no longer maintain. Our goal is to provide a better SDK than the already existing one to
manipulate the underlying sqlite3 database with less constraints. On top of that, we are planning to add
new features such finding an element in the database. 

Numbat will be used in the already existing project [pyrrha](https://gitlab.qb/firmware-re/cartography/pyrrha).

Here is an overview of Sourcetrail database, the main component is the element table which is used
by almost all the other elements for simple cross referencing between tables. 

![Sourcetrail Database](https://gitlab.qb/sbabigeon/numbat/-/raw/main/sourcetrail_db.png)

## Difference with SourcetrailDB

There are a few difference of behavior between this project and the existing SourcetrailDB API:

 - Duplicate in the Node table are not allowed, which means that is not possible to add, for 
   example, two classes with the same prefix, name and postfix.

 - Instead of returning invalid objects such as empty NameHierarchy when the serialization fails,
   an exception is raised.

Except theses differences, Numbat implement the same API than SourcetrailDB with the addition of extra features.

## Installation 

To install locally from the git repository:    
```bash
# Download the repo
git clone https://gitlab.qb/firmware-re/cartography/numbat
cd numbat
# Create a new virtual environement 
python -m venv venv
source venv/bin/activate
# Install numbat locally
pip install .
```
To install directly from pip package (@TODO):
```
pip install .
```

## Basic Usage

To use numbat, you must first create a `SourcetrailDB` object and either create a new database or open an existing one:
```python
from numbat import SourcetrailDB

srctrl = SourcetrailDB()
try:
    # Create a new database
    srctrl.create('my_database')
except FileExistsError:
    # Database already exists, open it and remove the entire content with clear
    srctrl.open('my_database')
    srctrl.clear()
    # A quicker way to open and clear 
    srctrl.open('my_database', clear=True)
```

Once the database is open, the first thing to do is to add one or more source file in the database using the following snippet:
```python
file_id = srctrl.record_file(pathlib.Path('my_file.c'))
srctrl.record_file_language(file_id, 'C')
``` 

To populate the database, it's possible to record different symbol such as class or function like this:
```python


``` 
