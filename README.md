# Numbat

<img align="right" src="https://gitlab.qb/sbabigeon/numbat/-/raw/main/numbat.png" width="250" heigh="250">

## Introduction

The goal of this project is to use sourcetrail software to map firmwares, this could be an extension
to the existing project [pyrrha](https://gitlab.qb/firmware-re/cartography/pyrrha).
 
The goal of this tool will be to list all the relation between binaries (much like pyrrha) but with
more information. In particular, we would be able to get the disassembly / decompiled code of all the 
binaries and display them in sourcetrail UI.

## TODO

The following tasks need to be done:

 - Providing a better SDK than the already existing one to be able to manipulate underlying sqlite3
   database with less constraints.
 - Provide information about decompiled code and assembly (maybe using Ghidra or IDA API) 
 - Instead of displaying link from one function to a binary (what pyrrha is currently doing)
   we would display relation with the functions within the binaries. For example, the function
   ``printf`` inside ``ls`` will have a reference to the function ``memset`` of the binary ``libc.6.so`` 

