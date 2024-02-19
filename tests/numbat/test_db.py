from numbat import SourcetrailDB
from numbat.types import NameHierarchy

import pathlib
import shutil
import pytest
import os

TMP_PATH = 'generated'

@pytest.fixture(scope='session', autouse=True)
def prepare_and_clean():
    """
        This function will be called once before running all
        the test and once after all the test have been run.
    """

    # Create a new directory
    os.makedirs(TMP_PATH)
    yield
    # Delete it
    shutil.rmtree(TMP_PATH)

@pytest.fixture()
def test_create_db():
    print('test_create_db')
    path = '%s/db.srctrldb' % TMP_PATH

    # Clean if already exists
    if os.path.exists(path):
        os.remove(path)

    # Create a new database
    try:
        srctrl = SourcetrailDB.create(path)
        srctrl.close()
        assert True
    except Exception as e:
        print(e)
        assert False

def test_open_database(test_create_db):
    print('test_create_symbol')
    path = '%s/db.srctrldb' % TMP_PATH

    # Open an existing database
    try:
        srctrl = SourcetrailDB.open(path)
        srctrl.clear()
        srctrl.close()
        assert True
    except Exception as e:
        print(e)
        assert False

def test_record_file(test_create_db):
    path = '%s/db.srctrldb' % TMP_PATH

    # Open an existing database
    srctrl = SourcetrailDB.open(path)

    filename = '%s/test.c' % TMP_PATH
    with open(filename, 'w') as test:
        test.write('''
            int main(void) {
                return 0;
            }
        ''')

        file_id = srctrl.record_file(pathlib.Path(filename))
        assert file_id != None
        srctrl.record_file_language(file_id, 'C')
        assert True

    srctrl.close()

def test_record_class(test_create_db):
    path = '%s/db.srctrldb' % TMP_PATH

    # Open an existing database
    srctrl = SourcetrailDB.open(path)
    # Insert a symbol once
    id_a = srctrl.record_class(name='MyType', delimiter=NameHierarchy.NAME_DELIMITER_JAVA)
    assert(id_a != None)

    srctrl.close()

def test_duplicate_symbol(test_create_db):
    path = '%s/db.srctrldb' % TMP_PATH

    # Open an existing database
    srctrl = SourcetrailDB.open(path)

    # Insert a symbol once
    id_a = srctrl.record_class(name='MyType', delimiter=NameHierarchy.NAME_DELIMITER_JAVA)
    assert(id_a != None)

    # Insert the same symbol again
    id_b = srctrl.record_class(name='MyType', delimiter=NameHierarchy.NAME_DELIMITER_JAVA)

    assert(id_b != None)
    assert(id_a == id_b)

    srctrl.close()
