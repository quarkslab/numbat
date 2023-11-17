# Numbat Internal Dev

## Numbat Architecture

The following picture provides an overview of Sourcetrail database. The main component is the element table which is used by almost all the other elements for simple cross-referencing between tables. 

![Sourcetrail Database](../../img/sourcetrail_db.png)
**Figure: Sourcetrail Database Structure**

Numbat is structured in three main submodules:

- [`numbat.base`](base) which defines all the objects manipulated by Numbat. These objects mainly match the different database tables.
- [`numbat.dao`](dao) which interacts with the SQlite Database.
- [`numbat.api`](api) which is the implementation of the user API. It is exposed to the user directly through the main module `numbat`. It contains a lot of wrappers as the idea is to hide all the complex types used by Numbat to the final user.


## Differences with SourcetrailDB

There are a few difference of behavior between this project and the existing [SourcetrailDB API](https://github.com/CoatiSoftware/SourcetrailDB):

 - Duplicate in the Node table are not allowed, which means that is not possible to add, for example, two classes with the same prefix, name and postfix.

 - Instead of returning invalid objects such as empty `NameHierarchy` when the serialization fails, an exception is raised.

Except these differences, Numbat implement the same API as SourcetrailDB with the addition of extra features.

## Testing

In order to test for regression, some tests are available inside the `tests/` directory. The tests are 
using the package `pytest` which can be used and installed like this:

```bash
# Download the repo
git clone https://gitlab.qb/firmware-re/cartography/numbat
cd numbat
# Create a new virtual environement 
python -m venv venv
source venv/bin/activate
# Install numbat locally
pip install '.[test]'
# Run the test
pytest
```