## v0.2.6—Add Options in File Operation
### Features
User can now specify the name under which a file is recorded in db (`SourcetrailDB.record_file`)

### Fixes
- File directory (for side loaded files) is only created when required not automatically at the init of the DB.

**Full Changelog**: [https://github.com/quarkslab/numbat/compare/v0.2.5...v0.2.6](https://github.com/quarkslab/numbat/compare/v0.2.5...v0.2.6)


## v0.2.5—Improve Exceptions
### Features
A new exception has been implemented (`DBException`) to abstract the underlying DB and its particular exceptions. User will only need to catch
this exception to catch all the DB related exceptions.

### Fixes
- Fix custom command addition.

**Full Changelog**: [https://github.com/quarkslab/numbat/compare/v0.2.4...v0.2.5](https://github.com/quarkslab/numbat/compare/v0.2.4...v0.2.5)

## v0.2.4—Fixes
### Features
N/A

### Fixes
- Internal get catch errors when needed.
- Detail errors to improve debug experience.

**Full Changelog**: [https://github.com/quarkslab/numbat/compare/v0.2.3...v0.2.4](https://github.com/quarkslab/numbat/compare/v0.2.3...v0.2.4)

## v0.2.3—Typing Support (PEP 561)
### Features
- Add packaging type information.
- Add linter and formatter info.

### Fixes
- Various little fixes following linter application.

**Full Changelog**: [https://github.com/quarkslab/numbat/compare/v0.2.2...v0.2.3](https://github.com/quarkslab/numbat/compare/v0.2.2...v0.2.3)


## v0.2.2—Graph Customization Features
### Features
- Class member publicity (internal, private, public) could now be set with the `SourcetrailDB.record_{public, default, private}_access` methods.
- Integrate customization features provided by NumbatUI (*cf* [dedicated doc page](https://quarkslab.github.io/numbat/customization/) for details).

### Fixes
- Update CI to replace EoL actions versions.
- Parent directory iteration

**Full Changelog**: [https://github.com/quarkslab/numbat/compare/v0.2.1...v0.2.2](https://github.com/quarkslab/numbat/compare/v0.2.1...v0.2.2)

## v0.2.1—Opensourcing
### Features
- add small details in the documentation.

### Fixes
- Tests with correct modules name

**Full Changelog**: [https://github.com/quarkslab/numbat/compare/v0.2.0...v0.2.1](https://github.com/quarkslab/numbat/compare/v0.2.0...v0.2.1)

## v0.2.0
### Features
- add a cache system for names/id to avoid doing DB request to obtain the id associated to a given name
- add the classmethod `SourcetrailDB.exists` to check if a path correspond to an existing db

### Fixes
- None

**Full Changelog**: [https://github.com/quarkslab/numbat/compare/v0.1.0...v0.2.0](https://github.com/quarkslab/numbat/compare/v0.1.0...v0.2.0)

## v0.1.0—First release
**Full Changelog**: [https://github.com/quarkslab/numbat/commits/v0.1.0](https://github.com/quarkslab/numbat/commits/v0.1.0)
