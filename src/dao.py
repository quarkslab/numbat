import base
import sqlite3

class SqliteHelper(object):
    """
        Helper class for sqlite operation
    """

    @staticmethod 
    def connect(path: str):
        """
            Wrapper for sqlite3 connect method so the api doesn't rely 
            directly on sqlite and his more general 
        """
        return sqlite3.connect(path)
        
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
    def clear(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM element;'''
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
    def clear(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM element_component;'''
        )        

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.ElementComponent:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM element_component WHERE id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            id_, element_id, type_, data = out[0]
            return base.ElementComponent(id_, element_id, 
                base.ElementComponentType(type_), data
            )
     
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
    def clear(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM edge;'''
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.Edge:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM edge WHERE id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            id_, type_, src, dst = out[0]
            return base.Edge(id_, base.EdgeType(type_), src, dst)

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

class NameHierarchy(object):
   
    # Delimiters for the serialized_name 
    DELIMITER              = '\t'
    META_DELIMITER         = '\tm'
    NAME_DELIMITER         = '\tn'
    PART_DELIMITER         = '\ts'
    SIGNATURE_DELIMITER    = '\tp'

    # Name delimiter type
    NAME_DELIMITER_FILE    = '/'
    NAME_DELIMITER_CXX     = '::'
    NAME_DELIMITER_JAVA    = '.'
    NAME_DELIMITER_UNKNOWN = '@'

    NAME_DELIMITERS = [
        NAME_DELIMITER_FILE,    
        NAME_DELIMITER_CXX,  
        NAME_DELIMITER_JAVA,    
        NAME_DELIMITER_UNKNOWN 
    ]

    @staticmethod
    def serialize_name(prefix: str = '', name: str = '', suffix: str = ''):
        """
            Utility method that return a serialized name
        """
        return ''.join([
            NameHierarchy.NAME_DELIMITER_CXX,
            NameHierarchy.META_DELIMITER,
            name,
            NameHierarchy.PART_DELIMITER,
            prefix,
            NameHierarchy.SIGNATURE_DELIMITER,
            suffix
        ])

    @staticmethod
    def deserialize_name(serialized_name: str = ''):
        """
            Utility method that return prefix, name and suffix 
            from a serialized name
        """
        items = serialized_name.split(NameHierarchy.DELIMITER) 
        if items[0] not in NameHierarchy.NAME_DELIMITERS:
            raise Exception("Invalide serialized name: '%s'"%serialized_name) 

        name   = items[1][1:]
        prefix = items[2][1:]
        suffix = items[3][1:]
        return (prefix, name, suffix)

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
    def clear(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM node;'''
        )      

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.Node:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM node WHERE id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            id_, type_, serialized_name = out[0]
            return base.Node(id_, base.NodeType(type_), serialized_name)
 
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

    @staticmethod
    def serialize_name(prefix: str = '', name: str = '', suffix: str = ''):
        """
            Utility method that return a serialized name
        """
        return NameHierarchy.serialize_name(prefix, name, suffix) 

    @staticmethod
    def deserialize_name(serialized_name: str = ''):
        """
            Utility method that return prefix, name and suffix 
            from a serialized name
        """
        return NameHierarchy.deserialize_name(serialized_name) 

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
    def clear(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM symbol;'''
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.Symbol:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM symbol WHERE id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            id_, type_ = out[0]
            return base.Symbol(id_, base.SymbolType(type_))
 
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
    def clear(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM file;'''
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
    def clear(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM filecontent;'''
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
    def clear(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM local_symbol;'''
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
                obj.end_line, obj.end_column, obj.type.value
            )
        )
 
    @staticmethod
    def delete(database: sqlite3.Connection, obj: base.SourceLocation) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM source_location WHERE id = ?;''', (obj.id,)
        )
         
    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM source_location;'''
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.SourceLocation:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM source_location WHERE id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            id_, fid, sl, sc, el, ec, type_ = out[0]
            return base.SourceLocation(id_, fid, sl, sc, el, ec, 
                base.SourceLocationType(type_)
            )
 
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
                    obj.end_line, obj.end_column, obj.type.value, obj.id
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
    def clear(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM occurrence;'''
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
    def clear(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM component_access;'''
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> base.ComponentAccess:
        out = SqliteHelper.fetch(database, '''
            SELECT * FROM component_access WHERE node_id = ?;''', (elem_id,)
        ) 
   
        if len(out) == 1:
            node_id, type_ = out[0]
            return base.ComponentAccess(node_id,    
                base.ComponentAccessType(type_)
            )

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
    def clear(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM error;'''
        )

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

class MetaDAO(object):
    
    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''    
            CREATE TABLE meta(
                id INTEGER, 
                key TEXT, 
                value TEXT, 
                PRIMARY KEY(id)
            );'''
        )
       
    @staticmethod 
    def delete_table(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DROP TABLE IF EXISTS main.meta;'''
        )
 
    @staticmethod
    def new(database: sqlite3.Connection, key: str, value: str) -> int:
        return SqliteHelper.exec(database, '''
            INSERT INTO meta(
                id, key, value  
            ) VALUES(NULL, ?, ?);''', (
                key, value 
            )
        )

    @staticmethod
    def delete(database: sqlite3.Connection, id_: int) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM meta WHERE id = ?;''', (id_,)
        )
         
    @staticmethod
    def get(database: sqlite3.Connection, id_: int) -> tuple[int, str, str]:
        out = SqliteHelper.fetch(database, '''
            SELECT id, key, value FROM meta WHERE id = ?;''', (id_,)
        ) 
        return tuple(out[0])   

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        SqliteHelper.exec(database, '''
            DELETE FROM meta;'''
        )

    @staticmethod
    def update(database: sqlite3.Connection, id_: int, key: str, 
            value: str) -> None:

        SqliteHelper.exec(database, '''
            UPDATE meta SET
                key = ?,
                value = ?
            WHERE
                id = ?;''', (
                    key, value, id_
                )
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[tuple[int, str, str]]:
        rows = SqliteHelper.fetch(database, '''
            SELECT * FROM meta;'''
        ) 
  
        result = list()
        for row in rows:
            result.append(tuple(row))
        
        return result

