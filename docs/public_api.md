# Public API

`Numbat` provides a class `SourcetrailDB` created to be easily used by external projects to create Sourcetrail projects. It provides methods to:

- [manage the database file](#numbat.SourcetrailDB.open);
- [record symbols](#numbat.SourcetrailDB.record_symbol_node) (according to their types);
- [customize symbols](#numbat.SourcetrailDB.set_node_type);
- [record references](#numbat.SourcetrailDB.record_ref_member) (links) between symbols;
- [record a file](#numbat.SourcetrailDB.record_file) and [information related to the source code](#numbat.SourcetrailDB.record_symbol_location) it contained.

::: numbat.SourcetrailDB
    options:
      filters:
        - "!^_"
        - "!^__"
      line_length: 80

