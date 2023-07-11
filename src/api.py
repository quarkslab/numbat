import os 
import sys
import base
import dao
from collections.abc import Callable

class SourcetrailDB(object):
    """
        This class implement a wrapper to sourcetrail internal database,
        it his able to create, edit and delete the underlying sqlite3
        database used by sourcetrail.
    """

    # Sourcetrail files extension
    SOURCETRAIL_PROJECT_EXT = '.srctrlprj'
    SOURCETRAIL_DB_EXT      = '.srctrldb'

    SOURCETRAIL_XML         = '\n'.join([
        '<?xml version="1.0" encoding="utf-8" ?>',
        '<config>',
        '   <version>0</version>',
        '</config>'
    ])

    def __init__(self) -> None:
        self.database = None

    # ------------------------------------------------------------------------ #
    # Database file management functions                                       #
    # ------------------------------------------------------------------------ #

    def open(self, path: str) -> None:
        """ 
            This method allow to open an existing sourcetrail database 
        """

        # Check that a database is not already opened
        if self.database:
            raise Exception('Database already opened')

        self.path = path
        # Check that the file has the correct extension
        if not self.path.endswith(self.SOURCETRAIL_DB_EXT):
            self.path += self.SOURCETRAIL_DB_EXT

        # Check that the file exists 
        self.path = os.path.realpath(self.path)
        if not os.path.isfile(self.path):
            raise Exception('File not found')

        self.database = dao.SqliteHelper.connect(self.path)

    def create(self, path: str) -> None:
        """
            This method allow to create a sourcetrail database 
        """
        # Check that a database is not already opened
        if self.database:
            raise Exception('Database already opened')

        self.path = path
        # Check that the file has the correct extension
        if not self.path.endswith(self.SOURCETRAIL_DB_EXT):
            self.path += self.SOURCETRAIL_DB_EXT
 
        # Check that the file exists 
        self.path = os.path.realpath(self.path)
        if os.path.isfile(self.path):
            raise Exception('File already exists')

        self.database = dao.SqliteHelper.connect(self.path)
        # Try to create the tables
        try:
            self.__create_sql_tables()
            self.__create_project_file()
            self.__add_meta_info()
        except Exception as e:
            # They already exists, fail
            self.close()
            raise e
         
    def commit(self) -> None:
        """
            This method allow to commit changes made to a sourcetrail database
        """
        if self.database:
            self.database.commit()
        else:
            raise Exception('Database is not opened yet')

    def clear(self) -> None:
        """
            Clear all elements present in the database 
        """
        self.__clear_sql_tables()

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
        dao.ElementDAO.create_table(self.database)
        dao.ElementComponentDAO.create_table(self.database)
        dao.EdgeDAO.create_table(self.database)
        dao.NodeDAO.create_table(self.database)
        dao.SymbolDAO.create_table(self.database)
        dao.FileDAO.create_table(self.database)
        dao.FileContentDAO.create_table(self.database)
        dao.LocalSymbolDAO.create_table(self.database)
        dao.SourceLocationDAO.create_table(self.database)
        dao.OccurrenceDAO.create_table(self.database)
        dao.ComponentAccessDAO.create_table(self.database)
        dao.ErrorDAO.create_table(self.database)
        dao.MetaDAO.create_table(self.database)
   
    def __clear_sql_tables(self) -> None:
        """
            This method allow to clear all the sql tables 
            used by sourcetrail 
        """
        dao.ElementDAO.clear(self.database)
        dao.ElementComponentDAO.clear(self.database)
        dao.EdgeDAO.clear(self.database)
        dao.NodeDAO.clear(self.database)
        dao.SymbolDAO.clear(self.database)
        dao.FileDAO.clear(self.database)
        dao.FileContentDAO.clear(self.database)
        dao.LocalSymbolDAO.clear(self.database)
        dao.SourceLocationDAO.clear(self.database)
        dao.OccurrenceDAO.clear(self.database)
        dao.ComponentAccessDAO.clear(self.database)
        dao.ErrorDAO.clear(self.database)
        
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
            prj.write(self.SOURCETRAIL_XML)
    
    def __add_meta_info(self) -> None:
        """
            Add the meta information inside sourcetrail database  
        """
        dao.MetaDAO.new(self.database, 'storage_version', '25')
        dao.MetaDAO.new(self.database, 'project_settings', self.SOURCETRAIL_XML)
    
    # ------------------------------------------------------------------------ #
    # Basic API for database                                                   #
    # ------------------------------------------------------------------------ #

    def new_element(self) -> base.Element:
        """
            Add a new Element into the sourcetrail database
        """
        elem = base.Element()
        elem.id = dao.ElementDAO.new(self.database, elem) 
        return elem
    
    def update_element(self, obj: base.Element) -> None:
        """
            Update a Element into the sourcetrail database
        """
        # An element has only a primary key so it can't be updated
        pass 

    def find_elements(self, predicate: Callable[[base.Element], bool]
        ) -> list[base.Element]:
        """
            Return a list of Element that satisfy a predicate
        """ 
        elements = dao.ElementDAO.list(self.database)
        return list(filter(predicate, elements))

    def delete_element(self, obj: base.Element) -> None:
        """
            Delete the specified Element from the database
        """ 
        dao.ElementDAO.delete(self.database, obj)

    def new_node(self, nodetype: base.NodeType, name: str) -> base.Node:
        """
            Add a new Node into the sourcetrail database
        """
        # First insert an element object  
        elem = self.new_element()
        # Create a new Node
        node = base.Node()
        node.id   = elem.id 
        node.type = nodetype
        node.name = name 
        # Add it to the database
        dao.NodeDAO.new(self.database, node)
        return node 
    
    def update_node(self, obj: base.Node) -> None:
        """
            Update a Node into the sourcetrail database
        """
        dao.NodeDAO.update(self.database, obj)

    def find_nodes(self, predicate: Callable[[base.Node], bool]
        ) -> list[base.Node]:
        """
            Return a list of Node that satisfy a predicate
        """ 
        elements = dao.NodeDAO.list(self.database)
        return list(filter(predicate, elements))

    def delete_node(self, obj: base.Node, cascade: bool = False) -> None:
        """
            Delete the specified Node from the database
        """ 
        # Check if user want to delete everything that 
        # reference this Node
        if cascade:
            # Delete the element directly
            dao.ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node
            dao.NodeDAO.delete(self.database, obj)  
 
    def new_local_symbol(self, name: str) -> base.LocalSymbol:
        """
            Add a new LocalSymbol into the sourcetrail database
        """
        # First insert an element object  
        elem = self.new_element()
        # Create a new LocalSymbol
        symb = base.LocalSymbol()
        symb.id   = elem.id
        symb.name = name 
        # Add it to the database
        dao.LocalSymbolDAO.new(self.database, symb)
        return symb
    
    def update_local_symbol(self, obj: base.LocalSymbol) -> None:
        """
            Update a LocalSymbol into the sourcetrail database
        """
        dao.LocalSymbolDAO.update(self.database, obj)

    def find_local_symbols(self, predicate: Callable[[base.LocalSymbol], bool]
        ) -> list[base.LocalSymbol]:
        """
            Return a list of LocalSymbol that satisfy a predicate
        """ 
        elements = dao.LocalSymbolDAO.list(self.database)
        return list(filter(predicate, elements))

    def delete_local_symbol(self, obj: base.LocalSymbol, cascade: bool = False) -> None:
        """
            Delete the specified LocalSymbol from the database
        """ 
        # Check if user want to delete everything that 
        # reference this LocalSymbol
        if cascade:
            # Delete the element directly
            dao.ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node
            dao.LocalSymbolDAO.delete(self.database, obj)  
 
    def new_element_component(self, elem_id: int, type_: base.ElementComponentType, 
            data: str) -> base.ElementComponent:
        """
            Add a new ElementComponent into the sourcetrail database
        """
        # First insert an element object  
        elem = self.new_element()
        # Create a new ElementComponent
        comp = base.ElementComponent()
        comp.id   = elem.id
        comp.name = name 
        # Add it to the database
        dao.ElementComponentDAO.new(self.database, com)
        return comp
    
    def update_element_component(self, obj: base.ElementComponent) -> None:
        """
            Update a ElementComponent into the sourcetrail database
        """
        dao.ElementComponentDAO.update(self.database, obj)

    def find_element_components(self, predicate: Callable[[base.ElementComponent], bool]
        ) -> list[base.ElementComponent]:
        """
            Return a list of ElementComponent that satisfy a predicate
        """ 
        elements = dao.ElementComponentDAO.list(self.database)
        return list(filter(predicate, elements))

    def delete_element_component(self, obj: base.ElementComponent, cascade: bool = False) -> None:
        """
            Delete the specified ElementComponent from the database
        """ 
        # Check if user want to delete everything that 
        # reference this ElementComponent
        if cascade:
            # Delete the element directly
            dao.ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node
            dao.ElementComponentDAO.delete(self.database, obj)  

    def new_error(self, message: str, fatal: int, indexed: int, 
            translation_unit: str) -> base.Error:
        """
            Add a new Error into the sourcetrail database
        """
        # First insert an element object  
        elem = self.new_element()
        # Create a new Error
        error = base.Error()
        error.id               = elem.id 
        error.message          = message
        error.fatal            = fatal
        error.indexed          = indexed
        error.translation_unit = translation_unit
        # Add it to the database
        dao.ErrorDAO.new(self.database, node)
        return node 
    
    def update_error(self, obj: base.Error) -> None:
        """
            Update a Error into the sourcetrail database
        """
        dao.ErrorDAO.update(self.database, obj)

    def find_errors(self, predicate: Callable[[base.Error], bool]
        ) -> list[base.Error]:
        """
            Return a list of Error that satisfy a predicate
        """ 
        elements = dao.ErrorDAO.list(self.database)
        return list(filter(predicate, elements))

    def delete_error(self, obj: base.Error, cascade: bool = False) -> None:
        """
            Delete the specified Error from the database
        """ 
        # Check if user want to delete everything that 
        # reference this Error
        if cascade:
            # Delete the element directly
            dao.ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node
            dao.ErrorDAO.delete(self.database, obj)  
 
    def new_symbol(self, type_: base.SymbolType, node: base.Node, 
            cascade: bool = False) -> base.Symbol:
        """
            Add a new Symbol into the sourcetrail database. If cascade is false,
            the node passed as parameter must exist in the database and must have 
            been created by the new_node method otherwise it will be also inserted
            as a new Node into the database.
        """
        # Create a new Symbol
        symb = base.Symbol()
        symb.definition_kind = type_
        if cascade:
            # Insert a new Node in the database
            node = self.new_node(node.type, node.name)

        symb.id = node.id
        # Add Symbol to the database
        dao.SymbolDAO.new(self.database, symb)
        return symb
    
    def update_symbol(self, obj: base.Symbol) -> None:
        """
            Update a Symbol into the sourcetrail database
        """
        dao.SymbolDAO.update(self.database, obj)

    def find_symbols(self, predicate: Callable[[base.Symbol], bool]
        ) -> list[base.Symbol]:
        """
            Return a list of Symbol that satisfy a predicate
        """ 
        elements = dao.SymbolDAO.list(self.database)
        return list(filter(predicate, elements))

    def delete_symbol(self, obj: base.Symbol, cascade: bool = False) -> None:
        """
            Delete the specified Symbol from the database
        """ 
        # Check if user want to delete everything that 
        # reference this Symbol
        if cascade:
            # Delete the element directly
            dao.ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node
            dao.SymbolDAO.delete(self.database, obj)  

    def new_component_access(self, type_: base.ComponentAccessType, node: base.Node, 
            cascade: bool = False) -> base.ComponentAccess:
        """
            Add a new ComponentAccess into the sourcetrail database. If cascade is false,
            the node passed as parameter must exist in the database and must have 
            been created by the new_node method otherwise it will be also inserted
            as a new Node into the database.
        """
        # Create a new ComponentAccess
        access = base.ComponentAccess()
        access.type = type_
        if cascade:
            # Insert a new Node in the database
            node = self.new_node(node.type, node.name)

        access.node_id = node.id
        # Add ComponentAccess to the database
        dao.ComponentAccessDAO.new(self.database, access)
        return access
    
    def update_component_access(self, obj: base.ComponentAccess) -> None:
        """
            Update a ComponentAccess into the sourcetrail database
        """
        dao.ComponentAccessDAO.update(self.database, obj)

    def find_component_accesss(self, predicate: Callable[[base.ComponentAccess], bool]
        ) -> list[base.ComponentAccess]:
        """
            Return a list of ComponentAccess that satisfy a predicate
        """ 
        elements = dao.ComponentAccessDAO.list(self.database)
        return list(filter(predicate, elements))

    def delete_component_access(self, obj: base.ComponentAccess, cascade: bool = False) -> None:
        """
            Delete the specified ComponentAccess from the database
        """ 
        # Check if user want to delete everything that 
        # reference this ComponentAccess
        if cascade:
            # Delete the element directly
            dao.ElementDAO.delete(self.database, base.Element(obj.node_id))
        else:
            # Only delete the node
            dao.ComponentAccessDAO.delete(self.database, obj)  

    def new_edge(self, type_: base.EdgeType, src: base.Node, dst: base.Node,
            cascade: bool = False) -> base.Edge:
        """
            Add a new Edge into the sourcetrail database. If cascade is false,
            the nodes passed as parameter must exist in the database and must have 
            been created by the new_node method otherwise it will be also inserted
            as a new Node into the database.
        """
        # Create a new Edge
        edge = base.Edge()
        edge.type = type_
        if cascade:
            # Insert the two new Node in the database
            src = self.new_node(src.type, src.name)
            dst = self.new_node(dst.type, dst.name)

        edge.src = src.id
        edge.dst = dst.id 
        # Add Edge to the database
        dao.EdgeDAO.new(self.database, edge)
        return edge
    
    def update_edge(self, obj: base.Edge) -> None:
        """
            Update a Edge into the sourcetrail database
        """
        dao.EdgeDAO.update(self.database, obj)

    def find_edges(self, predicate: Callable[[base.Edge], bool]
        ) -> list[base.Edge]:
        """
            Return a list of Edge that satisfy a predicate
        """ 
        elements = dao.EdgeDAO.list(self.database)
        return list(filter(predicate, elements))

    def delete_edge(self, obj: base.Edge, cascade: bool = False) -> None:
        """
            Delete the specified Edge from the database
        """ 
        # Check if user want to delete everything that 
        # reference this Edge
        if cascade:
            # Delete the element directly
            dao.ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node
            dao.EdgeDAO.delete(self.database, obj)  

    def new_source_location(self, start_line: int, start_column: int, end_line: int,
            end_column: int, type_: base.SourceLocationType,  node: base.Node,
            cascade: bool = False) -> base.SourceLocation:
        """
            Add a new SourceLocation into the sourcetrail database. If cascade is false,
            the node passed as parameter must exist in the database and must have 
            been created by the new_node method otherwise it will be also inserted
            as a new Node into the database.
        """
        # Create a new SourceLocation
        loc = base.SourceLocation()
        loc.type         = type_
        loc.start_line   = start_line
        loc.start_column = start_column
        loc.end_line     = end_line
        loc.end_column   = end_column
        if cascade:
            # Insert a new Node in the database
            node = self.new_node(node.type, node.name)

        loc.file_node_id = node.id
        # Add SourceLocation to the database
        loc.id = dao.SourceLocationDAO.new(self.database, loc)
        return loc
    
    def update_source_location(self, obj: base.SourceLocation) -> None:
        """
            Update a SourceLocation into the sourcetrail database
        """
        dao.SourceLocationDAO.update(self.database, obj)

    def find_source_locations(self, predicate: Callable[[base.SourceLocation], bool]
        ) -> list[base.SourceLocation]:
        """
            Return a list of SourceLocation that satisfy a predicate
        """ 
        elements = dao.SourceLocationDAO.list(self.database)
        return list(filter(predicate, elements))

    def delete_source_location(self, obj: base.SourceLocation, cascade: bool = False) -> None:
        """
            Delete the specified SourceLocation from the database
        """ 
        # Delete the source location, no need to cascade since 
        # this element doesn't **direcly** reference any other elements/nodes 
        dao.SourceLocationDAO.delete(self.database, obj)  

    def new_file(self, path: str, language: str, modification_time: str,
            indexed: int, complete: int, line_count: int, node: base.Node, 
            cascade: bool = False) -> base.File:
        """
            Add a new File into the sourcetrail database. If cascade is false,
            the node passed as parameter must exist in the database and must have 
            been created by the new_node method otherwise it will be also inserted
            as a new Node into the database.
        """
        # Create a new File
        file = base.File()
        file.path              = path
        file.language          = language
        file.modification_time = modification_time
        file.indexed           = indexed
        file.complete          = complete
        file.line_count        = line_count
        if cascade:
            # Insert the new Node in the database
            node = self.new_node(node.type, node.name)

        file.id = node.id 
        # Add File to the database
        dao.FileDAO.new(self.database, file)
        return file
    
    def update_file(self, obj: base.File) -> None:
        """
            Update a File into the sourcetrail database
        """
        dao.FileDAO.update(self.database, obj)

    def find_files(self, predicate: Callable[[base.File], bool]
        ) -> list[base.File]:
        """
            Return a list of File that satisfy a predicate
        """ 
        elements = dao.FileDAO.list(self.database)
        return list(filter(predicate, elements))

    def delete_file(self, obj: base.File, cascade: bool = False) -> None:
        """
            Delete the specified File from the database
        """ 
        # Check if user want to delete everything that 
        # reference this File
        if cascade:
            # Delete the element directly
            dao.ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node
            dao.FileDAO.delete(self.database, obj)  

    def new_file_content(self, content: str, file: base.File, node: base.Node = None, 
            cascade: bool = False) -> base.FileContent:
        """
            Add a new FileContent into the sourcetrail database. If cascade is false,
            the File passed as parameter must exist in the database and must have 
            been created by the new_node method otherwise it will be also inserted
            as a new Node into the database.
        """
        # If cascade is requested, node must be not null
        if cascade and not node:
            return None
 
        # Create a new FileContent
        filecontent = base.FileContent()
        filecontent.content = content
        if cascade:
            # Insert the new File in the database
            file = self.new_file(
                file.path, 
                file.language,
                file.modification_time,
                file.indexed,
                file.complete,
                file.line_count,
                node,
                cascade=True
            )

        filecontent.id = file.id 
        # Add FileContent to the database
        dao.FileContentDAO.new(self.database, filecontent)
        return filecontent
    
    def update_file_content(self, obj: base.FileContent) -> None:
        """
            Update a FileContent into the sourcetrail database
        """
        dao.FileContentDAO.update(self.database, obj)

    def find_file_contents(self, predicate: Callable[[base.FileContent], bool]
        ) -> list[base.FileContent]:
        """
            Return a list of FileContent that satisfy a predicate
        """ 
        elements = dao.FileContentDAO.list(self.database)
        return list(filter(predicate, elements))

    def delete_file_content(self, obj: base.FileContent, cascade: bool = False) -> None:
        """
            Delete the specified FileContent from the database
        """ 
        # Check if user want to delete everything that 
        # reference this FileContent
        if cascade:
            # Delete the element directly
            dao.ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node
            dao.FileContentDAO.delete(self.database, obj)  

    def new_occurrence(self, location: base.SourceLocation, element: base.Element, 
            node: base.Node = None, cascade: bool = False) -> base.Occurrence:
        """
            Add a new Occurrence into the sourcetrail database. If cascade is false,
            the SourceLocation passed as parameter must exist in the database and must have 
            been created by the new_node method otherwise it will be also inserted
            as a new Node into the database.
        """
        # If cascade is requested, node must be not null
        if cascade and not node:
            return None
 
        # Create a new Occurrence
        occurrence = base.Occurrence()
        if cascade:
            # Insert the new SourceLocation in the database
            location = self.new_source_location(
                location.start_line,
                location.start_column,
                location.end_line,
                location.end_column,
                location.type,
                node,
                cascade=True
            )
               
            # Insert a new element 
            element = self.new_element() 

        occurrence.element_id         = element.id
        occurrence.source_location_id = location.id
        # Add Occurrence to the database
        dao.OccurrenceDAO.new(self.database, occurrence)
        return occurrence
    
    def update_occurrence(self, obj: base.Occurrence) -> None:
        """
            Update a Occurrence into the sourcetrail database
        """
        dao.OccurrenceDAO.update(self.database, obj)

    def find_occurrences(self, predicate: Callable[[base.Occurrence], bool]
        ) -> list[base.Occurrence]:
        """
            Return a list of Occurrence that satisfy a predicate
        """ 
        elements = dao.OccurrenceDAO.list(self.database)
        return list(filter(predicate, elements))

    def delete_occurrence(self, obj: base.Occurrence, cascade: bool = False) -> None:
        """
            Delete the specified Occurrence from the database
        """ 
        # Check if user want to delete everything that 
        # reference this Occurrence
        if cascade:
            # Delete the element directly
            dao.ElementDAO.delete(self.database, base.Element(obj.element_id))
            dao.ElementDAO.delete(self.database, base.Element(obj.source_location_id))
        else:
            # Only delete the node
            dao.OccurrenceDAO.delete(self.database, obj)  

    # ------------------------------------------------------------------------ #
    # Advanced API for database                                                #
    # ------------------------------------------------------------------------ #

    def new_class(self, name: str = '', prefix: str ='', 
        suffix: str = '', indexed: bool = True) -> base.Class:
        """
            Add a new Class into the sourcetrail database
        """
        # Create a new Class element
        cls = base.Class()
        cls.name    = name
        cls.prefix  = prefix
        cls.suffix  = suffix
        cls.indexed = indexed

        # Insert a new node in the database 
        node = self.new_node(
            base.NodeType.NODE_CLASS,
            dao.NodeDAO.serialize_name(
                cls.prefix,
                cls.name,       
                cls.suffix
            )  
        )
        cls.id = node.id
        # Indicate whether the element is implicit or non-indexed   
        if indexed:
            # Add a new symbol, no need to save symbol id has it should
            # be the same as the id of the node
            self.new_symbol(
                base.SymbolType.EXPLICIT,
                node 
            )   
        return cls
    
    def update_class(self, obj: base.Class) -> None:
        """
            Update a Class into the sourcetrail database
        """

        # Search for the corresponding node
        node = dao.NodeDAO.get(self.database, obj.id)
        # Update object 
        node.name = dao.NodeDAO.serialize_name(
            obj.prefix,
            obj.name,
            obj.suffix
        ) 
        # Reflect change in the database
        self.update_node(node)      
        # Also apply modification to the symbol
        symb = dao.SymbolDAO.get(self.database, node.id)

        if obj.indexed and not symb:
            # Insert a new symbol
            self.new_symbol(
                base.SymbolType.EXPLICIT,
                node 
            )
        elif obj.indexed and symb.definition_kind != base.SymbolType.EXPLICIT:
            # Update the existing one
            symb.definition_kind = base.SymbolType.EXPLICIT
            self.update_symbol(symb)
        elif not obj.indexed and symb.definition_kind == base.SymbolType.EXPLICIT:
            # Update the existing one
            symb.definition_kind = base.SymbolType.IMPLICIT
            self.update_symbol(symb)
        else:
            # No action are required
            pass
        
    def find_class(self, predicate: Callable[[base.Class], bool]
        ) -> list[base.Class]:
        """
            Return a list of Class that satisfy a predicate
        """ 
        # Convert a Node object to Class 
        def convert(node: base.Node):
            prefix, name, suffix = dao.NodeDAO.deserialize_name(node.name) 
            
            indexed = False
            symb = dao.SymbolDAO.get(self.database, node.id)
            if symb and symb.definition_kind == base.SymbolType.EXPLICIT:
                indexed = True

            cls = base.Class()
            cls.id      = node.id
            cls.prefix  = prefix
            cls.name    = name
            cls.suffix  = suffix
            cls.indexed = indexed   
            
            return cls 

        # Apply our wrapper to all the nodes
        nodes = dao.NodeDAO.list(self.database)
        return list(filter(predicate, list(map(convert, nodes))))

    def delete_class(self, obj: base.Class, cascade: bool = False) -> None:
        """
            Delete the specified Class from the database
        """ 
        # Check if user want to delete everything that reference this Class
        if cascade:
            # Delete the element directly
            dao.ElementDAO.delete(self.database, base.Element(obj.id))
        else:
            # Only delete the node and it's symbol
            dao.NodeDAO.delete(self.database, base.Node(
                obj.id,
                base.NodeType.NODE_CLASS,
                dao.NodeDAO.serialized_name(
                    cls.prefix,
                    cls.name,       
                    cls.suffix
                )
            ))
            dao.SymbolDAO.delete(self.database, base.Symbol(
                obj.id,
                base.SymbolType.NONE 
            ))  

def main():

    srctrl = SourcetrailDB()
    try:
        srctrl.create('database')
    except Exception as e:
        print(e)
        srctrl.open('database')
        srctrl.clear()

    cls = srctrl.new_class('MyClass', 'class', '()') 
    cls = srctrl.new_class('MyOtherClass', 'class', '()') 

    classes = srctrl.find_class(lambda e: e.name == 'MyClass')
    for cls in classes:
        cls.name = 'MyUpdatedClass'
        srctrl.update_class(cls)
        
    classes = srctrl.find_class(lambda e: True)
    for cls in classes:
        print('%s %s%s' %(cls.prefix, cls.name, cls.suffix))
   
    srctrl.commit()
    srctrl.close()
       
if __name__ == '__main__':
    main()
