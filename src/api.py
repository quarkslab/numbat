import os 
import sys
import base
import sqlite3
from collections.abc import Callable

class SqliteHelper(object):
    """
        Helper class for sqlite operation
    """
        
    @staticmethod 
    def exec(database: sqlite3.Connection, request: str, 
            parameters: tuple = ()) -> int:
        """
            Execute the sqlite request without returning the result 
        """

        if not database:
            raise Exception('Invalid database handle')

        cur = database.cursor()
        cur.execute(request, parameters)
        cur.close()
        return cur.lastrowid

    def fetch(database: sqlite3.Connection, request: str, 
            parameters: tuple = ()) -> list:
        """
            Return the result of the sqlite request as list 
        """

        if not database:
            raise Exception('Invalid database handle')

        cur = database.cursor()
        cur.execute(request, parameters)
        result = cur.fetchall()
        cur.close()

        return result
        
class ElementDAO(object):
     
    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''    
            CREATE TABLE IF NOT EXISTS element(
                id INTEGER,                         
                PRIMARY KEY(id));'''
        )
 
    @staticmethod 
    def delete_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DROP TABLE IF EXISTS main.element;'''
        )
        
    @staticmethod
    def new(database: sqlite3.Connection, obj: base.Element) -> int:
        return SqliteHelper.exec(database, '''
            INSERT INTO element(id) VALUES (NULL);'''
        )
    
    @staticmethod
    def delete(database: sqlite3.Connection, obj: base.Element) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM element WHERE id = ?;''', (obj.id,)
        )
   
    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.Element:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM element WHERE id = ?;''', (elem_id,)
        ) 

        if len(out) == 1:
            return base.Element(*out[0])

    @staticmethod
    def update(database: sqlite3.Connection, obj: base.Element) -> None:
        # Since the Element object does only contains a primary key
        # it can't be updated
        pass

    @staticmethod
    def list(database: sqlite3.Connection) -> list[base.Element]:
        rows = SqliteHelper.fetch(database, '''
            SELECT * FROM element;'''
        ) 

        result = list()
        for row in rows:
            result.append(base.Element(*row))

        return result

class ElementComponentDAO(object):
 
    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''    
            CREATE TABLE IF NOT EXISTS element_component(
                id INTEGER, 
                element_id INTEGER, 
                type INTEGER, 
                data TEXT, 
                PRIMARY KEY(id), 
                FOREIGN KEY(element_id) REFERENCES element(id) ON DELETE CASCADE
            );'''
        )
       
    @staticmethod 
    def delete_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DROP TABLE IF EXISTS main.element_component;'''
        )
 
    @staticmethod
    def new(database: sqlite3.Connection, obj: base.ElementComponent) -> int:
        return SqliteHelper.exec(database, '''
            INSERT INTO element_component(
                id, element_id, type, data
            ) VALUES(?, ?, ?, ?);''', (obj.id, obj.elem_id, obj.type.value, obj.data)
        )
 
    @staticmethod
    def delete(database: sqlite3.Connection, obj: base.ElementComponent) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM element_component WHERE id = ?;''', (obj.id,)
        )
         
    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.ElementComponent:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM element_component WHERE id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            return base.ElementComponent(*out[0])
     
    @staticmethod
    def update(database: sqlite3.Connection, obj: base.ElementComponent) -> None:
        SqliteHelper.exec(database, '''
            UPDATE element_component SET
                element_id = ?, 
                type = ?, 
                data = ?
            WHERE
                id = ?;''', (obj.elem_id, obj.type.value, obj.data, obj.id)
        )
 
    @staticmethod
    def list(database: sqlite3.Connection) -> list[base.ElementComponent]:
        rows = SqliteHelper.fetch(database, '''
            SELECT * FROM element_component;'''
        ) 
  
        result = list()
        for row in rows:
            result.append(base.ElementComponent(*row))
        
        return result
    
class EdgeDAO(object):
 
    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''    
            CREATE TABLE IF NOT EXISTS edge(
                id INTEGER NOT NULL, 
                type INTEGER NOT NULL, 
                source_node_id INTEGER NOT NULL, 
                target_node_id INTEGER NOT NULL, 
                PRIMARY KEY(id), 
                FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE, 
                FOREIGN KEY(source_node_id) REFERENCES node(id) ON DELETE CASCADE, 
                FOREIGN KEY(target_node_id) REFERENCES node(id) ON DELETE CASCADE
            );'''
        )
       
    @staticmethod 
    def delete_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DROP TABLE IF EXISTS main.edge;'''
        )
 
    @staticmethod
    def new(database: sqlite3.Connection, obj: base.Edge) -> int:
        return SqliteHelper.exec(database, '''
            INSERT INTO edge(
                id, type, source_node_id, target_node_id
            ) VALUES(?, ?, ?, ?);''', (obj.id, obj.type.value, obj.src, obj.dst)
        )
 
    @staticmethod
    def delete(database: sqlite3.Connection, obj: base.Edge) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM edge WHERE id = ?;''', (obj.id,)
        )
         
    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.Edge:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM edge WHERE id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            return base.Edge(*out[0])

    @staticmethod
    def update(database: sqlite3.Connection, obj: base.Edge) -> None:
        SqliteHelper.exec(database, '''
            UPDATE edge SET
                type = ?, 
                source_node_id = ?,
                target_node_id = ?
            WHERE
                id = ?;''', (obj.type.value, obj.src, obj.dst, obj.id)
        )
 
    @staticmethod
    def list(database: sqlite3.Connection) -> list[base.Edge]:
        rows = SqliteHelper.fetch(database, '''
            SELECT * FROM edge;'''
        ) 
  
        result = list()
        for row in rows:
            result.append(base.Edge(*row))
        
        return result

class NodeDAO(object):
 
    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''    
            CREATE TABLE IF NOT EXISTS node(
                id INTEGER NOT NULL, 
                type INTEGER NOT NULL, 
                serialized_name TEXT, 
                PRIMARY KEY(id), 
                FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE
            );'''
        )
       
    @staticmethod 
    def delete_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DROP TABLE IF EXISTS main.node;'''
        )
 
    @staticmethod
    def new(database: sqlite3.Connection, obj: base.Node) -> int:
        return SqliteHelper.exec(database, '''
            INSERT INTO node(
                id, type, serialized_name 
            ) VALUES(?, ?, ?);''', (obj.id, obj.type.value, obj.name)
        )
 
    @staticmethod
    def delete(database: sqlite3.Connection, obj: base.Node) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM node WHERE id = ?;''', (obj.id,)
        )
         
    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.Node:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM node WHERE id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            return base.Node(*out[0])
 
    @staticmethod
    def update(database: sqlite3.Connection, obj: base.Node) -> None:
        SqliteHelper.exec(database, '''
            UPDATE node SET
                type = ?, 
                serialized_name = ?
            WHERE
                id = ?;''', (obj.type.value, obj.name, obj.id)
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[base.Node]:
        rows = SqliteHelper.fetch(database, '''
            SELECT * FROM node;'''
        ) 
  
        result = list()
        for row in rows:
            result.append(base.Node(*row))
        
        return result

class SymbolDAO(object):
 
    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''    
            CREATE TABLE symbol(
                id INTEGER NOT NULL, 
                definition_kind INTEGER NOT NULL, 
                PRIMARY KEY(id), 
                FOREIGN KEY(id) REFERENCES node(id) ON DELETE CASCADE
            );'''
        )
       
    @staticmethod 
    def delete_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DROP TABLE IF EXISTS main.symbol;'''
        )
 
    @staticmethod
    def new(database: sqlite3.Connection, obj: base.Symbol) -> int:
        return SqliteHelper.exec(database, '''
            INSERT INTO symbol(
                id, definition_kind 
            ) VALUES(?, ?);''', (obj.id, obj.definition_kind.value)
        )
 
    @staticmethod
    def delete(database: sqlite3.Connection, obj: base.Symbol) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM symbol WHERE id = ?;''', (obj.id,)
        )
         
    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.Symbol:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM symbol WHERE id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            return base.Symbol(*out[0])
 
    @staticmethod
    def update(database: sqlite3.Connection, obj: base.Symbol) -> None:
        SqliteHelper.exec(database, '''
            UPDATE symbol SET
                definition_kind = ?
            WHERE
                id = ?;''', (obj.definition_kind.value, obj.id)
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[base.Symbol]:
        rows = SqliteHelper.fetch(database, '''
            SELECT * FROM symbol;'''
        ) 
  
        result = list()
        for row in rows:
            result.append(base.Symbol(*row))
        
        return result

class FileDAO(object):
 
    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''    
            CREATE TABLE file(
                id INTEGER NOT NULL, 
                path TEXT, 
                language TEXT, 
                modification_time TEXT, 
                indexed INTEGER, 
                complete INTEGER, 
                line_count INTEGER, 
                PRIMARY KEY(id), 
                FOREIGN KEY(id) REFERENCES node(id) ON DELETE CASCADE
            );'''
        )
       
    @staticmethod 
    def delete_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DROP TABLE IF EXISTS main.file;'''
        )
 
    @staticmethod
    def new(database: sqlite3.Connection, obj: base.File) -> int:
        return SqliteHelper.exec(database, '''
            INSERT INTO file(
                id, path, language, modification_time, indexed, complete, line_count 
            ) VALUES(?, ?, ?, ?, ?, ?, ?);''', (
                obj.id, obj.path, obj.language, obj.modification_time, 
                obj.indexed, obj.complete, obj.line_count
            )
        )
 
    @staticmethod
    def delete(database: sqlite3.Connection, obj: base.File) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM file WHERE id = ?;''', (obj.id,)
        )
         
    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.File:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM file WHERE id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            return base.File(*out[0])
 
    @staticmethod
    def update(database: sqlite3.Connection, obj: base.File) -> None:
        SqliteHelper.exec(database, '''
            UPDATE file SET
                path = ?,
                language = ?,
                modification_time = ?,
                indexed = ?,
                complete = ?,
                line_count = ? 
            WHERE
                id = ?;''', (
                    obj.path, obj.language, obj.modification_time, 
                    obj.indexed, obj.complete, obj.line_count, obj.id
                )
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[base.File]:
        rows = SqliteHelper.fetch(database, '''
            SELECT * FROM file;'''
        ) 
  
        result = list()
        for row in rows:
            result.append(base.File(*row))
        
        return result
 
class FileContentDAO(object):
 
    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''    
            CREATE TABLE filecontent(
                id INTEGER, 
                content TEXT, 
                PRIMARY KEY(id), 
                FOREIGN KEY(id) REFERENCES file(id)ON DELETE CASCADE ON UPDATE CASCADE
            );'''
        )
       
    @staticmethod 
    def delete_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DROP TABLE IF EXISTS main.filecontent;'''
        )
 
    @staticmethod
    def new(database: sqlite3.Connection, obj: base.FileContent) -> int:
        return SqliteHelper.exec(database, '''
            INSERT INTO filecontent(
                id, content 
            ) VALUES(?, ?);''', (obj.id, obj.content)
        )
 
    @staticmethod
    def delete(database: sqlite3.Connection, obj: base.FileContent) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM filecontent WHERE id = ?;''', (obj.id,)
        )
         
    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.FileContent:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM filecontent WHERE id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            return base.FileContent(*out[0])

    @staticmethod
    def update(database: sqlite3.Connection, obj: base.FileContent) -> None:
        SqliteHelper.exec(database, '''
            UPDATE filecontent SET
                content = ? 
            WHERE
                id = ?;''', (obj.content, obj.id)
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[base.FileContent]:
        rows = SqliteHelper.fetch(database, '''
            SELECT * FROM filecontent;'''
        ) 
  
        result = list()
        for row in rows:
            result.append(base.FileContent(*row))
        
        return result

class LocalSymbolDAO(object):
 
    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''    
            CREATE TABLE local_symbol(
                id INTEGER NOT NULL, 
                name TEXT, 
                PRIMARY KEY(id), 
                FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE
            );'''
        )
       
    @staticmethod 
    def delete_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DROP TABLE IF EXISTS main.local_symbol;'''
        )
 
    @staticmethod
    def new(database: sqlite3.Connection, obj: base.LocalSymbol) -> int:
        return SqliteHelper.exec(database, '''
            INSERT INTO local_symbol(
                id, name 
            ) VALUES(?, ?);''', (obj.id, obj.name)
        )
 
    @staticmethod
    def delete(database: sqlite3.Connection, obj: base.LocalSymbol) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM local_symbol WHERE id = ?;''', (obj.id,)
        )
         
    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.LocalSymbol:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM local_symbol WHERE id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            return base.LocalSymbol(*out[0])
 
    @staticmethod
    def update(database: sqlite3.Connection, obj: base.LocalSymbol) -> None:
        SqliteHelper.exec(database, '''
            UPDATE local_symbol SET
                name = ? 
            WHERE
                id = ?;''', (obj.name, obj.id)
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[base.LocalSymbol]:
        rows = SqliteHelper.fetch(database, '''
            SELECT * FROM local_symbol;'''
        ) 
  
        result = list()
        for row in rows:
            result.append(base.LocalSymbol(*row))
        
        return result

class SourceLocationDAO(object):
 
    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''    
            CREATE TABLE source_location(
                id INTEGER NOT NULL, 
                file_node_id INTEGER, 
                start_line INTEGER, 
                start_column INTEGER, 
                end_line INTEGER, 
                end_column INTEGER, 
                type INTEGER, 
                PRIMARY KEY(id), 
                FOREIGN KEY(file_node_id) REFERENCES node(id) ON DELETE CASCADE
            );'''
        )
       
    @staticmethod 
    def delete_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DROP TABLE IF EXISTS main.source_location;'''
        )
 
    @staticmethod
    def new(database: sqlite3.Connection, obj: base.SourceLocation) -> int:
        return SqliteHelper.exec(database, '''
            INSERT INTO source_location(
                id, file_node_id, start_line, start_column, end_line, end_column, type 
            ) VALUES(NULL, ?, ?, ?, ?, ?, ?);''', (
                obj.file_node_id, obj.start_line, obj.start_column,
                obj.end_line, obj.end_column, obj.type
            )
        )
 
    @staticmethod
    def delete(database: sqlite3.Connection, obj: base.SourceLocation) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM source_location WHERE id = ?;''', (obj.id,)
        )
         
    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.SourceLocation:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM source_location WHERE id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            return base.SourceLocation(*out[0])
 
    @staticmethod
    def update(database: sqlite3.Connection, obj: base.SourceLocation) -> None:
        SqliteHelper.exec(database, '''
            UPDATE source_location SET
                file_node_id = ?,
                start_line = ?,
                start_column = ?,
                end_line = ?,
                end_column = ?,
                type = ? 
            WHERE
                id = ?;''', (
                    obj.file_node_id, obj.start_line, obj.start_column,
                    obj.end_line, obj.end_column, obj.type, obj.id
                )
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[base.SourceLocation]:
        rows = SqliteHelper.fetch(database, '''
            SELECT * FROM source_location;'''
        ) 
  
        result = list()
        for row in rows:
            result.append(base.SourceLocation(*row))
        
        return result

class OccurrenceDAO(object):
 
    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''    
            CREATE TABLE occurrence(
                element_id INTEGER NOT NULL, 
                source_location_id INTEGER NOT NULL, 
                PRIMARY KEY(element_id, source_location_id), 
                FOREIGN KEY(element_id) REFERENCES element(id) ON DELETE CASCADE, 
                FOREIGN KEY(source_location_id) REFERENCES source_location(id) 
                    ON DELETE CASCADE
            );'''
        )
       
    @staticmethod 
    def delete_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DROP TABLE IF EXISTS main.occurrence;'''
        )
 
    @staticmethod
    def new(database: sqlite3.Connection, obj: base.Occurrence) -> int:
        return SqliteHelper.exec(database, '''
            INSERT INTO occurrence(
                element_id, source_location_id 
            ) VALUES(?, ?);''', (obj.element_id, obj.source_location_id)
        )
 
    @staticmethod
    def delete(database: sqlite3.Connection, obj: base.Occurrence) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM occurrence WHERE element_id = ?;''', (obj.element_id,)
        )
         
    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.Occurrence:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM occurrence WHERE element_id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            return base.Occurrence(*out[0])

    @staticmethod
    def update(database: sqlite3.Connection, obj: base.Occurrence) -> None:
        SqliteHelper.exec(database, '''
            UPDATE occurrence SET
                element_id = ?,
                source_location_id = ? 
            WHERE
                id = ?;''', (obj.element_id, obj.source_location_id, obj.id)
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[base.Occurrence]:
        rows = SqliteHelper.fetch(database, '''
            SELECT * FROM occurrence;'''
        ) 
  
        result = list()
        for row in rows:
            result.append(base.Occurrence(*row))
        
        return result

class ComponentAccessDAO(object):
 
    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''    
            CREATE TABLE component_access(
                node_id INTEGER NOT NULL, 
                type INTEGER NOT NULL, 
                PRIMARY KEY(node_id), 
                FOREIGN KEY(node_id) REFERENCES node(id) ON DELETE CASCADE
            );'''
        )
       
    @staticmethod 
    def delete_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DROP TABLE IF EXISTS main.component_access;'''
        )
 
    @staticmethod
    def new(database: sqlite3.Connection, obj: base.ComponentAccess) -> int:
        return SqliteHelper.exec(database, '''
            INSERT INTO component_access(
                node_id, type 
            ) VALUES(?, ?);''', (obj.node_id, obj.type.value)
        )
 
    @staticmethod
    def delete(database: sqlite3.Connection, obj: base.ComponentAccess) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM component_access WHERE node_id = ?;''', (obj.node_id,)
        )
         
    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.ComponentAccess:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM component_access WHERE node_id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            return base.ComponentAccess(*out[0])

    @staticmethod
    def update(database: sqlite3.Connection, obj: base.ComponentAccess) -> None:
        SqliteHelper.exec(database, '''
            UPDATE component_access SET
                node_id = ?,
                type = ? 
            WHERE
                id = ?;''', (obj.node_id, obj.type.value, obj.id)
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[base.ComponentAccess]:
        rows = SqliteHelper.fetch(database, '''
            SELECT * FROM component_access;'''
        ) 
  
        result = list()
        for row in rows:
            result.append(base.ComponentAccess(*row))
        
        return result

class ErrorDAO(object):
 
    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''    
            CREATE TABLE error(
                id INTEGER NOT NULL, 
                message TEXT, 
                fatal INTEGER NOT NULL, 
                indexed INTEGER NOT NULL, 
                translation_unit TEXT, 
                PRIMARY KEY(id), 
                FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE
            );'''
        )
       
    @staticmethod 
    def delete_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DROP TABLE IF EXISTS main.error;'''
        )
 
    @staticmethod
    def new(database: sqlite3.Connection, obj: base.Error) -> int:
        return SqliteHelper.exec(database, '''
            INSERT INTO error(
                id, message, fatal, indexed, translation_unit 
            ) VALUES(?, ?, ?, ?, ?);''', (
                obj.id, obj.message, obj.fatal, obj.indexed, obj.translation_unit
            )
        )
 
    @staticmethod
    def delete(database: sqlite3.Connection, obj: base.Error) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM error WHERE id = ?;''', (obj.id,)
        )
         
    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.Error:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM error WHERE id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            return base.Error(*out[0])

    @staticmethod
    def update(database: sqlite3.Connection, obj: base.Error) -> None:
        SqliteHelper.exec(database, '''
            UPDATE error SET
                message = ?,
                fatal = ?,
                indexed = ?,
                translation_unit = ?
            WHERE
                id = ?;''', (
                    obj.message, obj.fatal, obj.indexed, 
                    obj.translation_unit, obj.id
                )
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[base.Error]:
        rows = SqliteHelper.fetch(database, '''
            SELECT * FROM error;'''
        ) 
  
        result = list()
        for row in rows:
            result.append(base.Error(*row))
        
        return result

class SourcetrailDB(object):
    """
        This class implement a wrapper to sourcetrail internal database,
        it his able to create, edit and delete the underlying sqlite3
        database used by sourcetrail.
    """

    # Sourcetrail files extension
    SOURCETRAIL_PROJECT_EXT = '.srctrlprj'
    SOURCETRAIL_DB_EXT      = '.srctrldb'

    def __init__(self) -> None:
        self.database = None

    def open(self, path: str) -> None:
        """ 
            This method allow to open an existing sourcetrail database 
        """

        # Check that a database is not already opened
        if self.database:
            raise Exception('Database already opened')

        # Check that the file exists 
        self.path = os.path.realpath(path)
        if not os.path.isfile(self.path):
            raise Exception('File not found')

        # Check that the file has the correct extension
        if not self.path.endswith(self.SOURCETRAIL_DB_EXT):
            raise Exception('File does not look like a sourcetrail database')

        self.database = sqlite3.connect(self.path)

    def create(self, path: str) -> None:
        """
            This method allow to create a sourcetrail database 
        """
        # Check that the file exists 
        self.path = os.path.realpath(path)
        if os.path.isfile(self.path):
            raise Exception('File already exists')

        # Check that the file has the correct extension
        if not self.path.endswith(self.SOURCETRAIL_DB_EXT):
            self.path += self.SOURCETRAIL_DB_EXT
 
        self.database = sqlite3.connect(self.path)
        self.__create_sql_tables()
        self.__create_project_file()
         
    def commit(self) -> None:
        """
            This method allow to commit changes made to a sourcetrail database
        """
        if self.database:
            self.database.commit()
        else:
            raise Exception('Database is not opened yet')

    def close(self) -> None:
        """
            This method allow to close a sourcetrail database
        """
        if self.database:
            self.database.close()
            self.database = None
        else:
            raise Exception('Database is not opened yet') 

    def __create_sql_tables(self) -> None:
        """
            This method allow to create all the sql tables needed 
            by sourcetrail 
        """
        ElementDAO.create_table(self.database)
        ElementComponentDAO.create_table(self.database)
        EdgeDAO.create_table(self.database)
        NodeDAO.create_table(self.database)
        SymbolDAO.create_table(self.database)
        FileDAO.create_table(self.database)
        FileContentDAO.create_table(self.database)
        LocalSymbolDAO.create_table(self.database)
        SourceLocationDAO.create_table(self.database)
        OccurrenceDAO.create_table(self.database)
        ComponentAccessDAO.create_table(self.database)
        ErrorDAO.create_table(self.database)
        
    def __create_project_file(self) -> None:
        """
            This method create a simple project file 
            for sourcetrail
        """
 
        filename = self.path.replace(
            self.SOURCETRAIL_DB_EXT,
            self.SOURCETRAIL_PROJECT_EXT
        )

        with open(filename, 'w') as prj:
            prj.write('\n'.join([
                '<?xml version="1.0" encoding="utf-8" ?>',
                '<config>',
                '   <version>0</version>',
                '</config>'
            ]))
 
    def newElement(self) -> base.Element:
        """
            Add a new Element into the sourcetrail database
        """
        elem = base.Element()
        elem.id = ElementDAO.new(self.database, elem) 
        return elem
    
    def updateElement(self, obj: base.Element) -> None:
        """
            Update a Element into the sourcetrail database
        """
        # An element has only a primary key so it can't be updated
        pass 

    def findElements(self, predicate: Callable[[base.Element], bool]
        ) -> list[base.Element]:
        """
            Return a list of Element that satisfy a predicate
        """ 
        elements = ElementDAO.list(self.database)
        return list(filter(predicate, elements))

    def deleteElement(self, obj: base.Element) -> None:
        """
            Delete the specified Element from the database
        """ 
        ElementDAO.delete(self.database, obj)

    def newNode(self, nodetype: base.NodeType, name: str) -> base.Node:
        """
            Add a new Node into the sourcetrail database
        """
        # First insert an element object  
        elem = self.newElement()
        # Create a new Node
        node = base.Node()
        node.id   = elem.id 
        node.type = nodetype
        node.name = name 
        # Add it to the database
        NodeDAO.new(self.database, node)
        return node 
    
    def updateNode(self, obj: base.Node) -> None:
        """
            Update a Node into the sourcetrail database
        """
        NodeDAO.update(self.database, obj)

    def findNodes(self, predicate: Callable[[base.Node], bool]
        ) -> list[base.Node]:
        """
            Return a list of Node that satisfy a predicate
        """ 
        elements = NodeDAO.list(self.database)
        return list(filter(predicate, elements))

    def deleteNode(self, obj: base.Node, cascade: bool = False) -> None:
        """
            Delete the specified Node from the database
        """ 
        # Check if user want to delete everything that 
        # reference this Node
        if cascade:
            # Delete the element directly
            ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node
            NodeDAO.delete(self.database, obj)  
 
    def newLocalSymbol(self, name: str) -> base.LocalSymbol:
        """
            Add a new LocalSymbol into the sourcetrail database
        """
        # First insert an element object  
        elem = self.newElement()
        # Create a new LocalSymbol
        symb = base.LocalSymbol()
        symb.id   = elem.id
        symb.name = name 
        # Add it to the database
        LocalSymbolDAO.new(self.database, symb)
        return symb
    
    def updateLocalSymbol(self, obj: base.LocalSymbol) -> None:
        """
            Update a LocalSymbol into the sourcetrail database
        """
        LocalSymbolDAO.update(self.database, obj)

    def findLocalSymbols(self, predicate: Callable[[base.LocalSymbol], bool]
        ) -> list[base.LocalSymbol]:
        """
            Return a list of LocalSymbol that satisfy a predicate
        """ 
        elements = LocalSymbolDAO.list(self.database)
        return list(filter(predicate, elements))

    def deleteLocalSymbol(self, obj: base.LocalSymbol, cascade: bool = False) -> None:
        """
            Delete the specified LocalSymbol from the database
        """ 
        # Check if user want to delete everything that 
        # reference this LocalSymbol
        if cascade:
            # Delete the element directly
            ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node
            LocalSymbolDAO.delete(self.database, obj)  
 
    def newElementComponent(self, elem_id: int, type_: base.ElementComponentType, 
            data: str) -> base.ElementComponent:
        """
            Add a new ElementComponent into the sourcetrail database
        """
        # First insert an element object  
        elem = self.newElement()
        # Create a new ElementComponent
        comp = base.ElementComponent()
        comp.id   = elem.id
        comp.name = name 
        # Add it to the database
        ElementComponentDAO.new(self.database, com)
        return comp
    
    def updateElementComponent(self, obj: base.ElementComponent) -> None:
        """
            Update a ElementComponent into the sourcetrail database
        """
        ElementComponentDAO.update(self.database, obj)

    def findElementComponents(self, predicate: Callable[[base.ElementComponent], bool]
        ) -> list[base.ElementComponent]:
        """
            Return a list of ElementComponent that satisfy a predicate
        """ 
        elements = ElementComponentDAO.list(self.database)
        return list(filter(predicate, elements))

    def deleteElementComponent(self, obj: base.ElementComponent, cascade: bool = False) -> None:
        """
            Delete the specified ElementComponent from the database
        """ 
        # Check if user want to delete everything that 
        # reference this ElementComponent
        if cascade:
            # Delete the element directly
            ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node
            ElementComponentDAO.delete(self.database, obj)  

    def newError(self, message: str, fatal: int, indexed: int, 
            translation_unit: str) -> base.Error:
        """
            Add a new Error into the sourcetrail database
        """
        # First insert an element object  
        elem = self.newElement()
        # Create a new Error
        error = base.Error()
        error.id               = elem.id 
        error.message          = message
        error.fatal            = fatal
        error.indexed          = indexed
        error.translation_unit = translation_unit
        # Add it to the database
        ErrorDAO.new(self.database, node)
        return node 
    
    def updateError(self, obj: base.Error) -> None:
        """
            Update a Error into the sourcetrail database
        """
        ErrorDAO.update(self.database, obj)

    def findErrors(self, predicate: Callable[[base.Error], bool]
        ) -> list[base.Error]:
        """
            Return a list of Error that satisfy a predicate
        """ 
        elements = ErrorDAO.list(self.database)
        return list(filter(predicate, elements))

    def deleteError(self, obj: base.Error, cascade: bool = False) -> None:
        """
            Delete the specified Error from the database
        """ 
        # Check if user want to delete everything that 
        # reference this Error
        if cascade:
            # Delete the element directly
            ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node
            ErrorDAO.delete(self.database, obj)  
 
    def newSymbol(self, type_: base.SymbolType, node: base.Node, 
            cascade: bool = False) -> base.Symbol:
        """
            Add a new Symbol into the sourcetrail database. If cascade is false,
            the node passed as parameter must exist in the database and must have 
            been created by the newNode method otherwise it will be also inserted
            as a new Node into the database.
        """
        # Create a new Symbol
        symb = base.Symbol()
        symb.definition_kind = type_
        if cascade:
            # Insert a new Node in the database
            node = self.newNode(node.type, node.name)

        symb.id = node.id
        # Add Symbol to the database
        SymbolDAO.new(self.database, symb)
        return symb
    
    def updateSymbol(self, obj: base.Symbol) -> None:
        """
            Update a Symbol into the sourcetrail database
        """
        SymbolDAO.update(self.database, obj)

    def findSymbols(self, predicate: Callable[[base.Symbol], bool]
        ) -> list[base.Symbol]:
        """
            Return a list of Symbol that satisfy a predicate
        """ 
        elements = SymbolDAO.list(self.database)
        return list(filter(predicate, elements))

    def deleteSymbol(self, obj: base.Symbol, cascade: bool = False) -> None:
        """
            Delete the specified Symbol from the database
        """ 
        # Check if user want to delete everything that 
        # reference this Symbol
        if cascade:
            # Delete the element directly
            ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node
            SymbolDAO.delete(self.database, obj)  

    def newComponentAccess(self, type_: base.ComponentAccessType, node: base.Node, 
            cascade: bool = False) -> base.ComponentAccess:
        """
            Add a new ComponentAccess into the sourcetrail database. If cascade is false,
            the node passed as parameter must exist in the database and must have 
            been created by the newNode method otherwise it will be also inserted
            as a new Node into the database.
        """
        # Create a new ComponentAccess
        access = base.ComponentAccess()
        access.type = type_
        if cascade:
            # Insert a new Node in the database
            node = self.newNode(node.type, node.name)

        access.node_id = node.id
        # Add ComponentAccess to the database
        ComponentAccessDAO.new(self.database, access)
        return access
    
    def updateComponentAccess(self, obj: base.ComponentAccess) -> None:
        """
            Update a ComponentAccess into the sourcetrail database
        """
        ComponentAccessDAO.update(self.database, obj)

    def findComponentAccesss(self, predicate: Callable[[base.ComponentAccess], bool]
        ) -> list[base.ComponentAccess]:
        """
            Return a list of ComponentAccess that satisfy a predicate
        """ 
        elements = ComponentAccessDAO.list(self.database)
        return list(filter(predicate, elements))

    def deleteComponentAccess(self, obj: base.ComponentAccess, cascade: bool = False) -> None:
        """
            Delete the specified ComponentAccess from the database
        """ 
        # Check if user want to delete everything that 
        # reference this ComponentAccess
        if cascade:
            # Delete the element directly
            ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node
            ComponentAccessDAO.delete(self.database, obj)  

"""
API status:

@DONE:
    - Element
    - Error
    - Node
    - Symbol
    - LocalSymbol
    - ComponentAccess   
    - ElementComponent

@TODO:
    - Edge
    - SourceLocation  
    - File
    - FileContent 
    - Occurence

"""

def main():
    pass

    srctrl = SourcetrailDB()
    srctrl.create('database')
  
    node = srctrl.newNode(
        base.NodeType.NODE_SYMBOL,
        'MyFile'    
    )

    print('Elements:')
    for e in srctrl.findElements(lambda e: True):
        print(e)

    print('Nodes:')
    for n in srctrl.findNodes(lambda e: True):
        print(n)
 
    node.name = 'Modified'
    srctrl.updateNode(node)
 
    print('Elements:')
    for e in srctrl.findElements(lambda e: True):
        print(e)

    print('Nodes:')
    for n in srctrl.findNodes(lambda e: True):
        print(n)
      
    srctrl.deleteNode(node)
 
    print('Elements:')
    for e in srctrl.findElements(lambda e: True):
        print(e)

    print('Nodes:')
    for n in srctrl.findNodes(lambda e: True):
        print(n)
       
    srctrl.commit()
    srctrl.close()
       
if __name__ == '__main__':
    main()
