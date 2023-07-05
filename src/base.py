import enum

class Element(object):
   
    """ 
        Wrapper class for sourcetrail element table:
            
        CREATE TABLE element(
            id INTEGER, 
            PRIMARY KEY(id)
        )
    """
 
    def __init__(self, id_: int = 0) -> None:
        self.id = id_ 

class ElementComponentType(enum.Enum):
    """
        Internal class that represent an ElementComponent type 
        inside the sourcetrail database    
    """
 
    NONE         = 0
    IS_AMBIGUOUS = 1

class ElementComponent(Element):
    """ 
        Wrapper class for sourcetrail element_component table:
            
        CREATE TABLE element_component(
            id INTEGER, 	
            element_id INTEGER, 	
            type INTEGER, 	
            data TEXT, 	
            PRIMARY KEY(id), 	
            FOREIGN KEY(element_id) REFERENCES element(id) ON DELETE CASCADE
        )
    """
 
    def __init__(self, id_: int = 0, elem_id: int = 0, 
            type_: ElementComponentType = ElementComponentType.NONE, 
            data: str = '') -> None:

        super().__init__(id_)
        self.elem_id = elem_id
        self.type    = type_
        self.data    = data     

class EdgeType(enum.Enum):
    """
        Internal class that represent a Edge type inside the 
        sourcetrail database    
    """
    UNDEFINED               = 0
    MEMBER                  = 1 << 0
    TYPE_USAGE              = 1 << 1
    USAGE                   = 1 << 2
    CALL                    = 1 << 3
    INHERITANCE             = 1 << 4
    OVERRIDE                = 1 << 5
    TYPE_ARGUMENT           = 1 << 6
    TEMPLATE_SPECIALIZATION = 1 << 7
    INCLUDE                 = 1 << 8
    IMPORT                  = 1 << 9
    BUNDLED_EDGES           = 1 << 10
    MACRO_USAGE             = 1 << 11
    ANNOTATION_USAGE        = 1 << 12

class Edge(Element):
    """ 
        Wrapper class for sourcetrail edge table:
   
        CREATE TABLE edge(
            id INTEGER NOT NULL, 
            type INTEGER NOT NULL, 
            source_node_id INTEGER NOT NULL, 
            target_node_id INTEGER NOT NULL, 
            PRIMARY KEY(id), 
            FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE, 
            FOREIGN KEY(source_node_id) REFERENCES node(id) ON DELETE CASCADE, 
            FOREIGN KEY(target_node_id) REFERENCES node(id) ON DELETE CASCADE
        ) 
    """

    def __init__(self, id_: int = 0, type_: EdgeType = EdgeType.UNDEFINED, 
            src: int = 0, dst: int = 0) -> None:

        super().__init__(id_)  
        self.type = type_
        self.src  = src
        self.dst  = dst

class NodeType(enum.Enum):
    """
        Internal class that represent a Edge type inside the 
        sourcetrail database    
    """
    NODE_SYMBOL          = 1 << 0
    NODE_TYPE            = 1 << 1
    NODE_BUILTIN_TYPE    = 1 << 2
    NODE_MODULE          = 1 << 3
    NODE_NAMESPACE       = 1 << 4
    NODE_PACKAGE         = 1 << 5
    NODE_STRUCT          = 1 << 6
    NODE_CLASS           = 1 << 7
    NODE_INTERFACE       = 1 << 8
    NODE_ANNOTATION      = 1 << 9
    NODE_GLOBAL_VARIABLE = 1 << 10
    NODE_FIELD           = 1 << 11
    NODE_FUNCTION        = 1 << 12
    NODE_METHOD          = 1 << 13
    NODE_ENUM            = 1 << 14
    NODE_ENUM_CONSTANT   = 1 << 15
    NODE_TYPEDEF         = 1 << 16
    NODE_TYPE_PARAMETER  = 1 << 17
    NODE_FILE            = 1 << 18
    NODE_MACRO           = 1 << 19
    NODE_UNION           = 1 << 20

class Node(Element):
    """
        Wrapper class for sourcetrail node table:

        CREATE TABLE node(
            id INTEGER NOT NULL, 
            type INTEGER NOT NULL, 
            serialized_name TEXT, 
            PRIMARY KEY(id), 
            FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE
        ) 
    """

    def __init__(self, id_: int = 0, type_: NodeType = NodeType.NODE_TYPE, 
            name: str = '') -> None:

        super().__init__(id_)  
        self.type = type_
        self.name = name

class SymbolType(enum.Enum):
    """
        Internal class that represent a Symbol type inside the 
        sourcetrail database    
    """
    NONE     = 0
    IMPLICIT = 1
    EXPLICIT = 2 

class Symbol(Element):
    """
        Wrapper class for sourcetrail symbol table:

        CREATE TABLE symbol(
            id INTEGER NOT NULL, 
            definition_kind INTEGER NOT NULL, 
            PRIMARY KEY(id), 
            FOREIGN KEY(id) REFERENCES node(id) ON DELETE CASCADE
        ) 
    """

    def __init__(self, id_: int = 0, definition: SymbolType = SymbolType.NONE) -> None:

        super().__init__(id_)  
        self.definition_kind = definition

class File(Element):
    """
        Wrapper class for sourcetrail file table:

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
        )
    """ 

    def __init__(self, id_: int = 0, path: str = '', language: str = '', 
            modification_time: str = '', indexed: int = 0, complete: int = 0, 
            line_count: int = 0) -> None:
    
        super().__init__(id_)  
        self.path              = path
        self.language          = language
        self.modification_time = modification_time
        self.indexed           = indexed
        self.complete          = complete
        self.line_count        = line_count
        
class FileContent(Element):
    """
        Wrapper class for sourcetrail filecontent table:
    
        CREATE TABLE filecontent(
            id INTEGER, 
            content TEXT, 
            PRIMARY KEY(id), 
            FOREIGN KEY(id) REFERENCES file(id)ON DELETE CASCADE ON UPDATE CASCADE
        )
    """

    def __init__(self, id_: int = 0, content: str = '') -> None:
 
        super().__init__(id_)  
        self.content = content

class LocalSymbol(Element):
    """
        Wrapper class for sourcetrail local_symbol table:

        CREATE TABLE local_symbol(
            id INTEGER NOT NULL, 
            name TEXT, 
            PRIMARY KEY(id), 
            FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE
        )        
    """

    def __init__(self, id_: int = 0, name: str = '') -> None:

        super().__init__(id_)  
        self.name = name

class SourceLocationType(enum.Enum):
    TOKEN           = 0
    SCOPE           = 1
    QUALIFIER       = 2
    LOCAL_SYMBOL    = 3
    SIGNATURE       = 4
    COMMENT         = 5
    ERROR           = 6
    FULLTEXT_SEARCH = 7
    SCREEN_SEARCH   = 8
    UNSOLVED        = 9

class SourceLocation(Element):
    """
        Wrapper class for sourcetrail source_location table:

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
        )
    """

    def __init__(self, id_: int = 0, file_node_id: int = 0, start_line: int = 0, 
            start_column: int = 0, end_line: int = 0, end_column: int = 0, 
            type_: SourceLocationType = SourceLocationType.UNSOLVED) -> None:
        
        super().__init__(id_)  
        self.file_node_id = file_node_id
        self.start_line   = start_line
        self.start_column = start_column
        self.end_line     = end_line
        self.end_column   = end_column
        self.type         = type_

class Occurrence(object):
    """
        Wrapper class for sourcetrail occurrence table:

        CREATE TABLE occurrence(
            element_id INTEGER NOT NULL, 
            source_location_id INTEGER NOT NULL, 
            PRIMARY KEY(element_id, source_location_id), 
            FOREIGN KEY(element_id) REFERENCES element(id) ON DELETE CASCADE, 
            FOREIGN KEY(source_location_id) REFERENCES source_location(id) 
                ON DELETE CASCADE
        )
    """

    def __init__(self, elem_id: int = 0, source_location_id: int = 0) -> None:
          
        self.element_id = elem_id
        self.source_location_id = source_location_id

class ComponentAccessType(enum.Enum):
    """
        Internal class that represent a ComponentAccess type inside 
        the sourcetrail database    
    """
    NONE               = 0
    PUBLIC             = 1
    PROTECTED          = 2
    PRIVATE            = 3
    DEFAULT            = 4
    TEMPLATE_PARAMETER = 5
    TYPE_PARAMETER     = 6

class ComponentAccess(object):
    """
        Wrapper class for sourcetrail component_access table:
        
        CREATE TABLE component_access(
            node_id INTEGER NOT NULL, 
            type INTEGER NOT NULL, 
            PRIMARY KEY(node_id), 
            FOREIGN KEY(node_id) REFERENCES node(id) ON DELETE CASCADE
        )
    """  

    def __init__(self, node_id: int = 0, 
        type_: ComponentAccessType = ComponentAccessType.NONE) -> None:
        
        self.node_id = node_id
        self.type    = type_

class Error(Element):
    """
        Wrapper class for sourcetrail error table:
        
        CREATE TABLE error(
            id INTEGER NOT NULL, 
            message TEXT, 
            fatal INTEGER NOT NULL, 
            indexed INTEGER NOT NULL, 
            translation_unit TEXT, 
            PRIMARY KEY(id), 
            FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE

        )
    """

    def __init__(self, id_: int = 0, message: str = '', fatal: int = 0, 
            indexed: int = 0, translation_unit: str = '') -> None:
    
        super().__init__(id_)
        self.message          = message
        self.fatal            = fatal
        self.indexed          = indexed
        self.translation_unit = translation_unit 

