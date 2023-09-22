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

For now the only difference in term of behavior, is that we don't allow duplicate in the Node table, which 
means that is not possible to add, for example, two classes with the same prefix, name and postfix.
