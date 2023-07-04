import os 
import sys
import base
import sqlite3

class SqliteHelper(object):
    """
        Helper class for sqlite operation
    """
        
    @staticmethod 
    def exec(database: sqlite3.Connection, request: str, 
            parameters: tuple = ()) -> None:
        """
            Execute the sqlite request without returning the result 
        """

        if not database:
            raise Exception('Invalid database handle')

        cur = database.cursor()
        cur.execute(request, parameters)
        cur.close()

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
    def new(database: sqlite3.Connection, obj: base.Element) -> None:
        SqliteHelper.exec(database, '''
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
    def new(database: sqlite3.Connection, obj: base.ElementComponent) -> None:
        SqliteHelper.exec(database, '''
            INSERT INTO element_component(
                id, element_id, type, data
            ) VALUES(NULL, ?, ?, ?);''', (obj.elem_id, obj.type, obj.data)
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
    def new(database: sqlite3.Connection, obj: base.Edge) -> None:
        SqliteHelper.exec(database, '''
            INSERT INTO edge(
                id, type, source_node_id, target_node_id
            ) VALUES(NULL, ?, ?, ?);''', (obj.type.value, obj.src, obj.dst)
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
    def new(database: sqlite3.Connection, obj: base.Node) -> None:
        SqliteHelper.exec(database, '''
            INSERT INTO node(
                id, type, serialized_name 
            ) VALUES(NULL, ?, ?);''', (obj.type.value, obj.name)
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
    def new(database: sqlite3.Connection, obj: base.Symbol) -> None:
        SqliteHelper.exec(database, '''
            INSERT INTO symbol(
                id, definition_kind 
            ) VALUES(NULL, ?);''', (obj.definition_kind,)
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
    def new(database: sqlite3.Connection, obj: base.File) -> None:
        SqliteHelper.exec(database, '''
            INSERT INTO file(
                id, path, language, modification_time, indexed, complete, line_count 
            ) VALUES(NULL, ?, ?, ?, ?, ?, ?);''', (
                obj.path, obj.language, obj.modification_time, 
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
    def new(database: sqlite3.Connection, obj: base.FileContent) -> None:
        SqliteHelper.exec(database, '''
            INSERT INTO filecontent(
                id, content 
            ) VALUES(NULL, ?);''', (obj.content,)
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
    def new(database: sqlite3.Connection, obj: base.LocalSymbol) -> None:
        SqliteHelper.exec(database, '''
            INSERT INTO local_symbol(
                id, name 
            ) VALUES(NULL, ?);''', (obj.name,)
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
    def new(database: sqlite3.Connection, obj: base.SourceLocation) -> None:
        SqliteHelper.exec(database, '''
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
    def new(database: sqlite3.Connection, obj: base.Occurrence) -> None:
        SqliteHelper.exec(database, '''
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
    def new(database: sqlite3.Connection, obj: base.ComponentAccess) -> None:
        SqliteHelper.exec(database, '''
            INSERT INTO component_access(
                node_id, type 
            ) VALUES(?, ?);''', (obj.node_id, obj.type)
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
    def new(database: sqlite3.Connection, obj: base.Error) -> None:
        SqliteHelper.exec(database, '''
            INSERT INTO error(
                id, message, fatal, indexed, translation_unit 
            ) VALUES(NULL, ?, ?, ?, ?);''', (
                obj.message, obj.fatal, obj.indexed, obj.translation_unit
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

class SourcetrailDB(object):
    """
        This class implement a wrapper to sourcetrail internal database,
        it his able to create, edit and delete the underlying sqlite3
        database used by sourcetrail.
    """

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

        self.database = sqlite3.connect(self.path)

    def create_sql_tables(self) -> None:
        """
            this method allow to create all the sql tables needed 
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
        
    def create(self, path: str) -> None:
        """
            This method allow to create a sourcetrail database 
        """
        # Check that the file exists 
        self.path = os.path.realpath(path)
        if os.path.isfile(self.path):
            raise Exception('File already exists')

        self.database = sqlite3.connect(self.path)
        self.create_sql_tables()
         
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

def main():
    db = SourcetrailDB()
    db.create('toto.db')
    assert(ElementDAO.get(db.database, 1) == None) 
    ElementDAO.new(db.database, base.Element(1))
    assert(ElementDAO.get(db.database, 1) != None) 
    ElementDAO.delete(db.database, base.Element(1))
    assert(ElementDAO.get(db.database, 1) == None) 

    assert(ElementComponentDAO.get(db.database, 1) == None) 
    ElementComponentDAO.new(db.database, base.ElementComponent(1, 0, 1, 'tata'))
    assert(ElementComponentDAO.get(db.database, 1) != None)
    ElementComponentDAO.delete(db.database, base.ElementComponent(1, 0, 1, 'tata'))
    assert(ElementComponentDAO.get(db.database, 1) == None) 

    assert(EdgeDAO.get(db.database, 1) == None) 
    EdgeDAO.new(db.database, base.Edge(1, base.EdgeType.EDGE_CALL, 1, 0))
    assert(EdgeDAO.get(db.database, 1) != None)
    EdgeDAO.delete(db.database, base.Edge(1, base.EdgeType.EDGE_UNDEFINED, 1, 0))
    assert(EdgeDAO.get(db.database, 1) == None) 

    assert(NodeDAO.get(db.database, 1) == None) 
    NodeDAO.new(db.database, base.Node(1, base.NodeType.NODE_BUILTIN_TYPE, 'titi'))
    assert(NodeDAO.get(db.database, 1) != None)
    NodeDAO.delete(db.database, base.Node(1, base.NodeType.NODE_CLASS, 'titi'))
    assert(NodeDAO.get(db.database, 1) == None) 

    assert(SymbolDAO.get(db.database, 1) == None) 
    SymbolDAO.new(db.database, base.Symbol(1, 'tata'))
    assert(SymbolDAO.get(db.database, 1) != None)
    SymbolDAO.delete(db.database, base.Symbol(1, 'tata'))
    assert(SymbolDAO.get(db.database, 1) == None) 

    assert(FileDAO.get(db.database, 1) == None) 
    FileDAO.new(db.database, base.File(1, '/abc', 'C', '00:00:00', 0, 1, 42))
    assert(FileDAO.get(db.database, 1) != None)
    FileDAO.delete(db.database, base.File(1, '/abc', 'C', '00:00:00', 0, 1, 42))
    assert(FileDAO.get(db.database, 1) == None) 

    assert(FileContentDAO.get(db.database, 1) == None) 
    FileContentDAO.new(db.database, base.FileContent(1, 'Hello world'))
    assert(FileContentDAO.get(db.database, 1) != None)
    FileContentDAO.delete(db.database, base.FileContent(1, 'Hello world'))
    assert(FileContentDAO.get(db.database, 1) == None) 

    assert(LocalSymbolDAO.get(db.database, 1) == None) 
    LocalSymbolDAO.new(db.database, base.LocalSymbol(1, 'Hello content'))
    assert(LocalSymbolDAO.get(db.database, 1) != None)
    LocalSymbolDAO.delete(db.database, base.LocalSymbol(1, 'Hello content'))
    assert(LocalSymbolDAO.get(db.database, 1) == None) 

    assert(SourceLocationDAO.get(db.database, 1) == None) 
    SourceLocationDAO.new(db.database, base.SourceLocation(1, 1, 0, 0, 10, 10, 2))
    assert(SourceLocationDAO.get(db.database, 1) != None)
    SourceLocationDAO.delete(db.database, base.SourceLocation(1, 1, 0, 0, 10, 10, 2))
    assert(SourceLocationDAO.get(db.database, 1) == None) 

    assert(OccurrenceDAO.get(db.database, 1) == None) 
    OccurrenceDAO.new(db.database, base.Occurrence(1, 1337))
    assert(OccurrenceDAO.get(db.database, 1) != None)
    OccurrenceDAO.delete(db.database, base.Occurrence(1, 1337))
    assert(OccurrenceDAO.get(db.database, 1) == None) 

    assert(ComponentAccessDAO.get(db.database, 1) == None) 
    ComponentAccessDAO.new(db.database, base.ComponentAccess(1, 4))
    assert(ComponentAccessDAO.get(db.database, 1) != None)
    ComponentAccessDAO.delete(db.database, base.ComponentAccess(1, 4))
    assert(ComponentAccessDAO.get(db.database, 1) == None) 

    assert(ErrorDAO.get(db.database, 1) == None) 
    ErrorDAO.new(db.database, base.Error(1, 'Error', 1, 1))
    assert(ErrorDAO.get(db.database, 1) != None)
    ErrorDAO.delete(db.database, base.Error(1, 'Error', 1, 1))
    assert(ErrorDAO.get(db.database, 1) == None) 

    db.commit()
    db.close()

if __name__ == '__main__':
    main()
