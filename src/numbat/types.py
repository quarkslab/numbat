# -*- coding: utf-8 -*-

#  Copyright 2023-2025 Quarkslab
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Types used internally by Numbat."""

import enum

from .exceptions import DeserializeException, SerializeException

# ------------------------------------------------------------------------ #
# Basic wrapper Types for API                                              #
# ------------------------------------------------------------------------ #


class Element(object):
    """Wrapper class for sourcetrail 'element' table.

        ```sql
        CREATE TABLE element(
            id INTEGER,
            PRIMARY KEY(id)
        )
        ```

        The 'element' table is used in sourcetrail to be able to easily manage
        other elements of others tables. Since all higher level element are
        referencing an element in the 'element' table it's possible to remove
    any element by removing the correct entry in the 'element' table.
    """

    def __init__(self, id_: int = 0):
        """Create a new Element object.

        :param id_: The id of the element
        """
        self.id = id_


class ElementComponentType(enum.Enum):
    """Indicate that an element component is ambiguous."""

    NONE = 0
    IS_AMBIGUOUS = 1


class ElementComponent(Element):
    """Wrapper class for sourcetrail element_component table.

    ```sql
    CREATE TABLE element_component(
        id INTEGER,
        element_id INTEGER,
        type INTEGER,
        data TEXT,
        PRIMARY KEY(id),
        FOREIGN KEY(element_id) REFERENCES element(id) ON DELETE CASCADE
    )
    ```

    This table is not commonly used, it only contains indication about the
    ambiguity of another element such as an edge or a node.
    """

    def __init__(
        self,
        id_: int = 0,
        elem_id: int = 0,
        type_: ElementComponentType = ElementComponentType.NONE,
        data: str = "",
    ):
        """Create a new ElementComponent object.

        :param id_: The id of the element
        :param elem_id: The id of the referenced element
        :param type_: The type of the ElementComponent
        :param data: Additional data (optional)
        """
        super().__init__(id_)
        self.elem_id = elem_id
        self.type = type_
        self.data = data


class EdgeType(enum.Enum):
    """Relationship between the nodes."""

    UNDEFINED = 0
    MEMBER = 1 << 0
    TYPE_USAGE = 1 << 1
    USAGE = 1 << 2
    CALL = 1 << 3
    INHERITANCE = 1 << 4
    OVERRIDE = 1 << 5
    TYPE_ARGUMENT = 1 << 6
    TEMPLATE_SPECIALIZATION = 1 << 7
    INCLUDE = 1 << 8
    IMPORT = 1 << 9
    BUNDLED_EDGES = 1 << 10
    MACRO_USAGE = 1 << 11
    ANNOTATION_USAGE = 1 << 12


class Edge(Element):
    """Wrapper class for sourcetrail edge table.

    ```sql
    CREATE TABLE edge(
        id INTEGER NOT NULL,
        type INTEGER NOT NULL,
        source_node_id INTEGER NOT NULL,
        target_node_id INTEGER NOT NULL,
        color TEXT,
        hover_display TEXT,
        PRIMARY KEY(id),
        FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE,
        FOREIGN KEY(source_node_id) REFERENCES node(id) ON DELETE CASCADE,
        FOREIGN KEY(target_node_id) REFERENCES node(id) ON DELETE CASCADE
    )
    ```

    The 'edge' table is used to define relation between element of the 'node'
    table. For example, it can be used to indicate that a field is a member
    of a class or a function foo is calling another function bar.
    """

    def __init__(
        self,
        id_: int = 0,
        type_: EdgeType = EdgeType.UNDEFINED,
        src: int = 0,
        dst: int = 0,
        hover_display: str = "",
    ):
        """Create a new Edge object.

        :param id_: The id of the element
        :param type_: The type of the Edge
        :param src: The id of the source element
        :param dst: The id of the destination element
        :param hover_display: The display text when hovering over the Edge
        """
        super().__init__(id_)
        self.type = type_
        self.src = src
        self.dst = dst
        self.hover_display = hover_display


class NodeType(enum.Enum):
    """Type of the node in the database."""

    NODE_SYMBOL = 1 << 0
    NODE_TYPE = 1 << 1
    NODE_BUILTIN_TYPE = 1 << 2
    NODE_MODULE = 1 << 3
    NODE_NAMESPACE = 1 << 4
    NODE_PACKAGE = 1 << 5
    NODE_STRUCT = 1 << 6
    NODE_CLASS = 1 << 7
    NODE_INTERFACE = 1 << 8
    NODE_ANNOTATION = 1 << 9
    NODE_GLOBAL_VARIABLE = 1 << 10
    NODE_FIELD = 1 << 11
    NODE_FUNCTION = 1 << 12
    NODE_METHOD = 1 << 13
    NODE_ENUM = 1 << 14
    NODE_ENUM_CONSTANT = 1 << 15
    NODE_TYPEDEF = 1 << 16
    NODE_TYPE_PARAMETER = 1 << 17
    NODE_FILE = 1 << 18
    NODE_MACRO = 1 << 19
    NODE_UNION = 1 << 20


class Node(Element):
    r"""Wrapper class for sourcetrail node table.

    ```sql
    CREATE TABLE node(
        id INTEGER NOT NULL,
        type INTEGER NOT NULL,
        serialized_name TEXT,
        color TEXT,
        hover_display TEXT,
        PRIMARY KEY(id),
        FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE
    )
    ```

    The 'node' table is the main table of the sourcetrail database. It allows
    to store elements such as function, class, package, etc. However, this
    table is weirdly implemented as the field 'serialized_name' contains
    another type called NameHierarchy with a custom serialization format.

    The NameHierarchy describe a relationship between node elements, for
    example, a class 'A' with a member 'b' will result in two entries in the
    database:

        id1 | NODE_CLASS | '.\tA\ts\tp'
        id2 | NODE_FIELD | '.\tA\ts\tp\tm\tb\ts\tp'

    The above example shows that the 'serialized_name' of the member 'b' (id2)
    hold some information about his parent 'A' (id1).
    """

    def __init__(
        self,
        id_: int = 0,
        type_: NodeType = NodeType.NODE_TYPE,
        name: str = "",
        hover_display: str = "",
    ):
        """Create a new Node object.

        :param id_: The id of the element
        :param type_: The type of the Node
        :param name: The serialized name of the Node
        :param hover_display: The display text when hovering over the Node
        """
        super().__init__(id_)
        self.type = type_
        self.name = name
        self.hover_display = hover_display


class NodeDisplay:
    """
    Represent how Sourcetrail's internal node types are displayed.

    ```sql
    CREATE TABLE IF NOT EXISTS node_type(
        id INTEGER NOT NULL,
        type TEXT,
        kind TEXT,
        PRIMARY KEY(id)
    )
    ```

    The 'node_type' table is used to store how each type of node is displayed.
    """

    def __init__(self, id: NodeType, graph_display: str, hover_display: str):
        """Create a new NodeDisplay object.

        :param id: The internal id according to the NodeType enum
        :param graph_display: The display text in the Sourcetrail graph
        :param hover_display: The display text when hovering over a node
        """
        self.id = id
        self.graph_display = graph_display
        self.hover_display = hover_display


class SymbolType(enum.Enum):
    """Symbol type in the database."""

    NONE = 0
    IMPLICIT = 1
    EXPLICIT = 2


class Symbol(Element):
    """
    Wrapper class for sourcetrail symbol table.

    ```sql
    CREATE TABLE symbol(
        id INTEGER NOT NULL,
        definition_kind INTEGER NOT NULL,
        PRIMARY KEY(id),
        FOREIGN KEY(id) REFERENCES node(id) ON DELETE CASCADE
    )
    ```

    The 'symbol' table is used to add additional information on elements
    such as node.
    """

    def __init__(self, id_: int = 0, definition: SymbolType = SymbolType.NONE):
        """Create a new Symbol object.

        :param id_: The id of the element
        :param definition: The type of the Symbol
        """
        super().__init__(id_)
        self.definition_kind = definition


class File(Element):
    """
    Wrapper class for sourcetrail file table.

    ```sql
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
    ```

    The 'file' table hold the information about the different source file
    that have been parsed by sourcetrail. Each one of them contains an id that
    will be reference by the element of the 'filecontent' table.
    """

    def __init__(
        self,
        id_: int = 0,
        path: str = "",
        language: str = "",
        modification_time: str = "",
        indexed: int = 0,
        complete: int = 0,
        line_count: int = 0,
    ):
        """Create a new File object.

        :param id_: The id of the element
        :param path: The path to the source file
        :param language: The language of the source file.
        :param modification_time: The time of the last modification of the source file
        :param indexed: A indication to tell if the file was indexed or not (0 or 1)
        :param complete: A indicate to tell if the indexing is complete or not (0 or 1)
        :param line_count: The number of line in the source file
        """
        super().__init__(id_)
        self.path = path
        self.language = language
        self.modification_time = modification_time
        self.indexed = indexed
        self.complete = complete
        self.line_count = line_count


class FileContent(Element):
    """Wrapper class for sourcetrail filecontent table.

    ```sql
    CREATE TABLE filecontent(
        id INTEGER,
        content TEXT,
        PRIMARY KEY(id),
        FOREIGN KEY(id) REFERENCES file(id)ON DELETE CASCADE ON UPDATE CASCADE
    )
    ```

    The 'filecontent' table holds the content of the different source file.
    Because the id field of the filecontent is a primary key (unique element)
    a filecontent should contain the entire content of a file.
    """

    def __init__(self, id_: int = 0, content: str = ""):
        """Create a new FileContent object.

        :param id_: The id of the element
        :param content: The content of the source file.
        """
        super().__init__(id_)
        self.content = content


class NodeFile(Element):
    """Wrapper class for node_file table.

    ```sql
    CREATE TABLE node_file(
        file_id INTEGER,
        file_name TEXT,
        display_content INTEGER,
        PRIMARY KEY(id),
        FOREIGN KEY(id) REFERENCES node(id) ON DELETE CASCADE
    )
    ```

    The 'node_file' table contains the paths to all files that have been copied to the p
    roject folder, and the node they are associated to.
    """

    def __init__(self, file_id: int, file_name: str, display_content: bool):
        """Create a new NodeFile object.

        :param file_id: id of the copied file
        :param file_name: path to the copy
        :param display_content: whether the file content should be displayed or not
        """
        super().__init__(file_id)
        self.file_name = file_name
        self.display_content = display_content


class LocalSymbol(Element):
    """Wrapper class for sourcetrail local_symbol table.

    ```sql
    CREATE TABLE local_symbol(
        id INTEGER NOT NULL,
        name TEXT,
        PRIMARY KEY(id),
        FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE
    )
    ```

    The 'local_symbol' table holds reference to nodes that represent
    elements such as variables only used locally. For example, the
    following code snippet:

    ```c
    int foo(int a)
    {
        my_global_func();
        int b = 2 * a;
        return b;
    }
    ```

    While result in 3 different nodes, two of them (a and b) with have
    an entry in the 'local_symbol' table. The content of this table is
    not essential to the application but can provide a better level of
    detail to the user when browsing code in Sourcetrail UI.
    """

    def __init__(self, id_: int = 0, name: str = ""):
        """Create a new LocalSymbol object.

        :param id_: The id of the element
        :param name: The name of local symbol
        """
        super().__init__(id_)
        self.name = name


class SourceLocationType(enum.Enum):
    """Symbol location type in the db and can be used to indicate indexing errors."""

    TOKEN = 0
    SCOPE = 1
    QUALIFIER = 2
    LOCAL_SYMBOL = 3
    SIGNATURE = 4
    ATOMIC_RANGE = 5
    INDEXER_ERROR = 6
    FULLTEXT_SEARCH = 7
    SCREEN_SEARCH = 8
    UNSOLVED = 9


class SourceLocation(Element):
    """Wrapper class for sourcetrail source_location table.

    ```sql
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
    ```

    The table 'source_location' contain some entries indicating where the
    corresponding node element (the ones that are referenced by the id) are
    located in the source tree.
    """

    def __init__(
        self,
        id_: int = 0,
        file_node_id: int = 0,
        start_line: int = 0,
        start_column: int = 0,
        end_line: int = 0,
        end_column: int = 0,
        type_: SourceLocationType = SourceLocationType.UNSOLVED,
    ):
        """Create a new SourceLocation object.

        :param id_: The id of the element
        :param file_node_id: The id of the file element corresponding to this content.
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :param type_: The type of the source location.
        """
        super().__init__(id_)
        self.file_node_id = file_node_id
        self.start_line = start_line
        self.start_column = start_column
        self.end_line = end_line
        self.end_column = end_column
        self.type = type_


class Occurrence(object):
    """Wrapper class for sourcetrail occurrence table.

    ```sql
    CREATE TABLE occurrence(
        element_id INTEGER NOT NULL,
        source_location_id INTEGER NOT NULL,
        PRIMARY KEY(element_id, source_location_id),
        FOREIGN KEY(element_id) REFERENCES element(id) ON DELETE CASCADE,
        FOREIGN KEY(source_location_id) REFERENCES source_location(id)
            ON DELETE CASCADE
    )
    ```

    The table 'occurrence' allow to link the elements define in the 'source_location'
    table and the ones define in the 'node' table.
    """

    def __init__(self, elem_id: int = 0, source_location_id: int = 0):
        """Create a new Occurrence object.

        :param elem_id: The id of the element referenced by this occurrence
        :param source_location_id: The id of the source location referenced by this 
        occurrence
        """
        self.element_id = elem_id
        self.source_location_id = source_location_id


class ComponentAccessType(enum.Enum):
    """Type of ComponentAccess in the database.

    It can be used to add extra information regarding the visibility of elements (in the
    "Object-Oriented" sens).
    """

    NONE = 0
    PUBLIC = 1
    PROTECTED = 2
    PRIVATE = 3
    DEFAULT = 4
    TEMPLATE_PARAMETER = 5
    TYPE_PARAMETER = 6


class ComponentAccess(object):
    """Wrapper class for sourcetrail component_access table.

    ```sql
    CREATE TABLE component_access(
        node_id INTEGER NOT NULL,
        type INTEGER NOT NULL,
        PRIMARY KEY(node_id),
        FOREIGN KEY(node_id) REFERENCES node(id) ON DELETE CASCADE
    )
    ```

    The table 'component_access' allow to add information on the type
    of visibility of element in the 'node' table. For example, a java
    class that is set to public will have an entry in this table.
    """

    def __init__(
        self, node_id: int = 0, type_: ComponentAccessType = ComponentAccessType.NONE
    ):
        """Create a new ComponentAccess object.

        :param node_id: The id of the element
        :param type_: The type of the ComponentAccess
        """
        self.node_id = node_id
        self.type = type_


class Error(Element):
    """Wrapper class for sourcetrail error table.

    ```sql
    CREATE TABLE error(
        id INTEGER NOT NULL,
        message TEXT,
        fatal INTEGER NOT NULL,
        indexed INTEGER NOT NULL,
        translation_unit TEXT,
        PRIMARY KEY(id),
        FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE
    )
    ```

    The table 'error' holds the different error message produced during
    the parsing of the source files and are displayed in the UI.
    """

    def __init__(
        self,
        id_: int = 0,
        message: str = "",
        fatal: int = 0,
        indexed: int = 0,
        translation_unit: str = "",
    ):
        """Create a new Error object.

        :param id_: The id of the element
        :param message: The description of the error
        :param fatal: Indicate if this error is fatal or not (0 or 1)
        :param indexed: Indicate if this error occurs while indexing (0 or 1)
        :param translation_unit: Indicate in which translation unit the error occurs
        """
        super().__init__(id_)
        self.message = message
        self.fatal = fatal
        self.indexed = indexed
        self.translation_unit = translation_unit


class NameElement(object):
    """Basic component of the serialized_name field of the node table.

    This type does not represent directly a type in the database.
    """

    def __init__(self, prefix: str = "", name: str = "", postfix: str = ""):
        """Create a new NameElement object.

        :param prefix: The prefix of the element
        :param name: The name of the element
        :param postfix: The postfix of the element
        """
        self._prefix = prefix
        self._name = name
        self._postfix = postfix

    def __str__(self) -> str:
        """Return a textual description of this NameElement.

        :return: A description of this object
        """
        return "<NameElement prefix:%s, name: %s, postfix: %s>" % (
            self._prefix,
            self._name,
            self._postfix,
        )

    def get_prefix(self) -> str:
        """Return the prefix of this element.

        :return: The prefix of the element
        """
        return self._prefix

    def get_name(self) -> str:
        """Return the name of this element.

        :return: The name of the element
        """
        return self._name

    def get_postfix(self) -> str:
        """Return the postfix of this element.

        :return: The postfix of the element
        """
        return self._postfix

    def set_prefix(self, prefix: str) -> None:
        """Set the prefix of this element.

        :param prefix: The new prefix of the element
        :return: None
        """
        self._prefix = prefix

    def set_name(self, name: str) -> None:
        """Set the name of this element.

        :param name: The new name of the element
        :return: None
        """
        self._name = name

    def set_postfix(self, postfix: str) -> None:
        """Set the postfix of this element.

        :param postfix: The new postfix of the element
        :return: None
        """
        self._postfix = postfix


class NameHierarchy(object):
    """Hierarchy relationship between nodes.

    This type does not represent directly a type in the database and
    is stored in the 'serialized_name' field of the 'node' table.
    """

    # Delimiters for the serialized_name
    DELIMITER = "\t"
    META_DELIMITER = "\tm"
    NAME_DELIMITER = "\tn"
    PART_DELIMITER = "\ts"
    SIGNATURE_DELIMITER = "\tp"

    # Name delimiter type
    NAME_DELIMITER_FILE = "/"
    NAME_DELIMITER_CXX = "::"
    NAME_DELIMITER_JAVA = "."
    NAME_DELIMITER_UNKNOWN = "@"

    NAME_DELIMITERS = [
        NAME_DELIMITER_FILE,
        NAME_DELIMITER_CXX,
        NAME_DELIMITER_JAVA,
        NAME_DELIMITER_UNKNOWN,
    ]

    def __init__(self, delimiter: str, elements: list[NameElement]):
        """Create a new NameHierarchy object.

        :param delimiter: The delimiter of for this NameHierarchy, must be one of the
        NAME_DELIMITERS
        :param elements: A list of NameElement representing the hierarchy of this
        element
        :return: None
        """
        self._delimiter = delimiter
        self._elements = elements

    def __serialize(self, start: int, end: int) -> str:
        """Be used as a wrapper for serialize_range and serialize_name.

        The serialization process is the following:
            - Start with any of the NAME_DELIMITERS
            - Serialize the **first element** by:
                - Adding the name field concatenated with NAME_DELIMITER
                - Add the prefix concatenated with PART_DELIMITER
                - Add the postfix concatenated with SIGNATURE_DELIMITER
            - Remainders elements are concatenated in the same way that they
              are separated with a META_DELIMITER

        :param start: the starting position of the elements
        :param end: the ending position of the elements
        :return: The serialized name
        """
        result = self._delimiter + self.META_DELIMITER
        if not self._elements:
            # @Warning: This is not the same behavior as SourcetrailDB
            # We are returning an exception instead of an empty string
            raise SerializeException()

        elements = self._elements[start:end]
        for i, elem in enumerate(elements):
            if i > 0:
                result += self.NAME_DELIMITER

            result += elem.get_name() + self.PART_DELIMITER
            result += elem.get_prefix() + self.SIGNATURE_DELIMITER
            result += elem.get_postfix()
        return result

    def extend(self, element: NameElement) -> None:
        """Add a new element to a hierarchy.

        :param element: The new element to add
        """
        self._elements.append(element)

    def serialize_range(self, start: int, end: int) -> str:
        """Return a part of the serialized name.

        :param start: the starting position of the elements
        :param end: the ending position of the elements
        :return: The serialized name
        """
        return self.__serialize(start, end)

    def serialize_name(self) -> str:
        """Return the full serialized name.

        :return: The serialized name
        """
        return self.__serialize(0, self.size())

    def size(self) -> int:
        """Return the size of the NameHierarchy object.

        :return: The size of the NameHierarchy
        """
        return len(self._elements) if self._elements else 0

    @staticmethod
    def deserialize_name(serialized_name: str) -> "NameHierarchy":
        """Return prefix, name and suffix from a serialized name.

        :param serialized_name: A string that should start by one
        of the following:
            - NAME_DELIMITER_FILE
            - NAME_DELIMITER_CXX
            - NAME_DELIMITER_JAVA
            - NAME_DELIMITER_UNKNOWN
        And then be followed by at least 3 elements separated by
        the delimiter "DELIMITER".
        :return: The NameHierarchy corresponding to the deserialize_name
        """
        idx = serialized_name.find(NameHierarchy.META_DELIMITER)
        if idx == -1:
            # Invalid meta delimiter

            # @Warning: This is not the same behavior as SourcetrailDB
            # We are returning an exception instead of an empty NameHierarchy
            # return NameHierarchy(NameHierarchy.NAME_DELIMITER_UNKNOWN, None)
            raise DeserializeException()

        elements = list()
        result = NameHierarchy(serialized_name[0:idx], [])

        idx += len(NameHierarchy.META_DELIMITER)
        while idx < len(serialized_name):
            # Read name
            spos = serialized_name.find(NameHierarchy.PART_DELIMITER, idx)
            if spos == -1:
                # Invalid part delimiter

                # @Warning: This is not the same behavior as SourcetrailDB
                # We are returning an exception instead of an empty NameHierarchy
                # return NameHierarchy(NameHierarchy.NAME_DELIMITER_UNKNOWN, None)
                raise DeserializeException()

            name = serialized_name[idx:spos]
            spos += len(NameHierarchy.PART_DELIMITER)

            # Read prefix
            ppos = serialized_name.find(NameHierarchy.SIGNATURE_DELIMITER, spos)
            if ppos == -1:
                # Invalid signature delimiter

                # @Warning: This is not the same behavior as SourcetrailDB
                # We are returning an exception instead of an empty NameHierarchy
                # return NameHierarchy(NameHierarchy.NAME_DELIMITER_UNKNOWN, None)
                raise DeserializeException()

            prefix = serialized_name[spos:ppos]
            ppos += len(NameHierarchy.SIGNATURE_DELIMITER)

            # Read postfix
            npos = serialized_name.find(NameHierarchy.NAME_DELIMITER, ppos)
            if npos == -1:
                postfix = serialized_name[ppos:]
                idx = len(serialized_name)
            else:
                postfix = serialized_name[ppos:npos]
                idx = npos + len(NameHierarchy.NAME_DELIMITER)

            elements.append(NameElement(prefix, name, postfix))

        result._elements = elements
        return result
