"""
Kernel CI report raw object-oriented (OO) data - report data organized
into objects, but without the object-oriented interface.
"""

import re
import textwrap
import jsonschema
from kcidb.misc import LIGHT_ASSERTS

# We'll get to it, pylint: disable=too-many-lines


class Relation:
    """A parent/child relation between object types"""

    # It's OK, pylint: disable=too-few-public-methods
    def __init__(self, parent, child, ref_fields):
        """
        Initialize a relation.

        Args:
            parent:     The parent type.
            child:      The child type.
            ref_fields: A tuple containing the list of names of child fields,
                        containing values of parent's globally-identifying
                        fields (in the same order), and linking the two.
        """
        assert isinstance(parent, Type)
        assert isinstance(child, Type)
        assert isinstance(ref_fields, tuple)
        assert all(isinstance(ref_field, str) for ref_field in ref_fields)
        assert len(ref_fields) == len(parent.id_fields)
        self.parent = parent
        self.child = child
        self.ref_fields = ref_fields


class Type:
    """An object type"""

    def __init__(self, name, json_schema, id_fields):
        """
        Initialize an object type.

        Args:
            name:           The type name.
            json_schema:    The JSON schema describing the raw object data.
            id_fields:      A tuple containing the names of object fields
                            identifying it globally.
        """
        assert isinstance(name, str)
        assert isinstance(json_schema, dict)
        assert isinstance(id_fields, tuple) and \
               all(isinstance(f, str) for f in id_fields)

        # The name of this type
        self.name = name
        # The JSON schema for this type's raw data
        self.json_schema = json_schema
        # List of ID field names
        self.id_fields = id_fields
        # A list of all relations
        self.relations = []
        # A map of parent type names and their relations
        self.parents = {}
        # A map of child type names and their relations
        self.children = {}

    def add_relation(self, relation):
        """
        Add a relation of this object to another.

        Args:
            relation:   The relation to add.
                        Must have this type as either the parent or the child.
                        Must not have been added before.
        """
        assert isinstance(relation, Relation)
        assert self is relation.parent or self is relation.child
        assert relation not in self.relations
        self.relations.append(relation)
        if self is relation.parent:
            self.children[relation.child.name] = relation
        if self is relation.child:
            self.parents[relation.parent.name] = relation

    def validate(self, data):
        """
        Validate a type's data against its JSON schema.

        Args:
            data:   The data to validate.

        Returns:
            The validated (but unmodified) data.

        Raises:
            `jsonschema.exceptions.ValidationError`, if the data did not
            adhere to this type's JSON schema.
        """
        jsonschema.validate(instance=data, schema=self.json_schema,
                            format_checker=jsonschema.draft7_format_checker)
        return data

    def is_valid(self, data):
        """
        Check if a type's data is valid according to its JSON schema.

        Args:
            data:   The data to check.

        Returns:
            True if the data is valid, False otherwise.
        """
        try:
            self.validate(data)
            return True
        except jsonschema.exceptions.ValidationError:
            return False

    def get_id(self, data):
        """
        Retrieve a tuple of field values identifying an object globally, from
        its data.

        Args:
            data:   The object data to retrieve the IDs from.

        Returns:
            A tuple of values of object fields identifying it globally.
        """
        assert LIGHT_ASSERTS or self.is_valid(data)
        return tuple(data[field] for field in self.id_fields)


class Schema:
    """A repository of recognized object types"""

    def __init__(self, types):
        """
        Initialize the schema.

        Args:
            types:  A dictionary of type descriptions. Keys being type names
                    and values being dictionaries with two entries:
                        * "json_schema" - a JSON schema for object data,
                        * "id_fields" - a tuple of names of the object fields
                                        identifying it globally,
                        * "children" - the optional dictionary of names of
                                       child types and tuples containing
                                       names of fields with values of parent's
                                       identifying fields ("id_fields"),
                                       in the same order.
        """
        assert isinstance(types, dict)
        assert all(
            isinstance(name, str) and
            isinstance(info, dict) and
            "json_schema" in info and
            isinstance(info["json_schema"], dict) and
            "id_fields" in info and
            isinstance(info["id_fields"], tuple) and
            all(isinstance(f, str) for f in info["id_fields"]) and
            ("children" not in info or (
                isinstance(info["children"], dict) and
                all(
                    isinstance(name, str) and
                    name in types and
                    isinstance(ref_fields, tuple) and
                    all(isinstance(f, str) for f in ref_fields)
                    for name, ref_fields in info["children"].items()
                )
            ))
            for name, info in types.items()
        )

        # Create types and build the JSON schema
        self.types = {}
        self.json_schema = dict(
            type="object",
            additionalProperties=False,
            properties={},
        )
        for name, info in types.items():
            self.types[name] = Type(name, info["json_schema"],
                                    info["id_fields"])
            self.json_schema["properties"][name] = dict(
                type="array",
                items=info["json_schema"]
            )

        # Create and register relations
        self.relations = []
        for name, info in types.items():
            # We like our "type", pylint: disable=redefined-builtin
            type = self.types[name]
            for child_name, ref_fields in info.get("children", {}).items():
                try:
                    child_type = self.types[child_name]
                except KeyError:
                    raise Exception(f"Couldn't find child {child_name!r} "
                                    f"of type {name!r}") from None
                relation = Relation(type, child_type, ref_fields)
                self.relations.append(relation)
                type.add_relation(relation)
                child_type.add_relation(relation)

    def validate(self, data):
        """
        Validate raw object-oriented data against the schema.

        Args:
            data:   The data to validate.

        Returns:
            The validated data.

        Raises:
            `jsonschema.exceptions.ValidationError`, if the data did not
            match the schema.
        """
        jsonschema.validate(instance=data, schema=self.json_schema,
                            format_checker=jsonschema.draft7_format_checker)
        return data

    def is_valid(self, data):
        """
        Check if a raw object-oriented data is valid according to the schema.

        Args:
            data:   The data to check.

        Returns:
            True if the data is valid, False otherwise.
        """
        try:
            self.validate(data)
            return True
        except jsonschema.exceptions.ValidationError:
            return False


# The schema of the raw object-oriented data
# TODO Fill in actual object schemas
SCHEMA = Schema(dict(
    revision=dict(
        json_schema=dict(type="object"),
        id_fields=("git_commit_hash", "patchset_hash"),
        children=dict(
            checkout=("git_commit_hash", "patchset_hash",)
        ),
    ),
    checkout=dict(
        json_schema=dict(type="object"),
        id_fields=("id",),
        children=dict(
            build=("checkout_id",)
        ),
    ),
    build=dict(
        json_schema=dict(type="object"),
        id_fields=("id",),
        children=dict(
            test=("build_id",),
        ),
    ),
    test=dict(
        json_schema=dict(type="object"),
        id_fields=("id",),
    ),
))


# A (verbose) regular expression pattern matching an unquoted ID field
_REQUEST_STRING_ID_FIELD_UNQUOTED_PATTERN = """
    [\x30-\x39\x41-\x5a\x61-\x7a_:/.?%+-]+
"""

_REQUEST_STRING_ID_FIELD_UNQUOTED_RE = re.compile(
    _REQUEST_STRING_ID_FIELD_UNQUOTED_PATTERN,
    re.ASCII | re.VERBOSE
)

# A (verbose) regular expression pattern matching characters which can
# appear unescaped in a quoted ID field
_REQUEST_STRING_ID_FIELD_QUOTED_UNESC_CHAR_PATTERN = """
    # Anything printable except doublequote/backslash
    [\x5d-\x7e\x20-\x21\x23-\x5b]
"""

# A (verbose) regular expression pattern matching characters which must be
# backslash-escaped when appearing in a quoted ID field
_REQUEST_STRING_ID_FIELD_QUOTED_ESC_CHAR_PATTERN = """
    # Doublequote/backslash
    ["\\\\]
"""

# A (verbose) regular expression pattern matching a quoted ID field
_REQUEST_STRING_ID_FIELD_QUOTED_PATTERN = f"""
    "
        (?:
            {_REQUEST_STRING_ID_FIELD_QUOTED_UNESC_CHAR_PATTERN} |
            \\\\ {_REQUEST_STRING_ID_FIELD_QUOTED_ESC_CHAR_PATTERN}
        )*
    "
"""

# A (verbose) regular expression pattern matching an ID field
_REQUEST_STRING_ID_FIELD_PATTERN = f"""
    (?:
        {_REQUEST_STRING_ID_FIELD_UNQUOTED_PATTERN} |
        {_REQUEST_STRING_ID_FIELD_QUOTED_PATTERN}
    )
"""

# A (verbose) regular expression pattern matching an ID (ID field list)
_REQUEST_STRING_ID_PATTERN = f"""
    {_REQUEST_STRING_ID_FIELD_PATTERN}
    (?:
        \\s*
        ,
        \\s*
        {_REQUEST_STRING_ID_FIELD_PATTERN}
    )*
"""

# A (verbose) regular expression pattern matching an ID list
_REQUEST_STRING_ID_LIST_PATTERN = f"""
    {_REQUEST_STRING_ID_PATTERN}
    (?:
        \\s*
        ;
        \\s*
        {_REQUEST_STRING_ID_PATTERN}
    )*
"""

# A (verbose) regular expression pattern matching an ID list spec
_REQUEST_STRING_SPEC_ID_LIST_PATTERN = f"""
    \\[
        \\s*
        {_REQUEST_STRING_ID_LIST_PATTERN}
        \\s*
    \\]
"""

# A (verbose) regular expression pattern matching a spec
_REQUEST_STRING_SPEC_PATTERN = f"""
    (?:
        # ID list placeholder
        % |
        # Inline ID list
        {_REQUEST_STRING_SPEC_ID_LIST_PATTERN}
    )
"""

# A (verbose) regular expression pattern matching a "request" part of the
# request string. Matching group names correspond to component ABNF rules.
_REQUEST_STRING_PATTERN = f"""
    \\s*
    # Relation
    (?P<relation>
        [<>]
    )
    \\s*
    # Type
    (?P<type>
        # Type name
        [a-z0-9_]+ |
        # Type branch wildcard
        [*]
    )
    \\s*
    # ID list specification
    (?P<spec>
        {_REQUEST_STRING_SPEC_PATTERN}
    )?
    \\s*
    # Loading scope
    (?P<load>
        [#$]
    )?
    \\s*
"""

# A regular expression matching a "request" part of the request string
# Matching group names correspond to component ABNF rules.
_REQUEST_STRING_RE = re.compile(
    _REQUEST_STRING_PATTERN,
    re.ASCII | re.VERBOSE
)


class Request:
    """A specification of a branch of objects to query from a data source"""

    # No, it's OK, pylint: disable=too-many-arguments,too-few-public-methods
    def __init__(self, base, child, obj_type, obj_id_list, load):
        """
        Initialize an object branch request.

        Args:
            base:           The request for objects this request is to be
                            based on, or None, meaning the request is based on
                            the root object.
            child:          True if this is a request for a base's child type,
                            False if it's for a parent type.
            obj_type:       The type (kcidb.oo.data.Type) of requested objects.
            obj_id_list:    The list of IDs of the objects to limit the
                            request to, or None to not limit the objects by
                            IDs.
            load:           True, if the objects should be loaded and
                            returned. False, if they should only be used as a
                            reference.
        """
        assert base is None or isinstance(base, Request)
        assert isinstance(child, bool)
        assert isinstance(obj_type, Type)
        obj_id_fields = obj_type.id_fields
        assert obj_id_list is None or \
               isinstance(obj_id_list, list) and \
               all(
                    len(obj_id) == len(obj_id_fields) and
                    all(isinstance(part, (str, type(None))) for part in obj_id)
                    for obj_id in obj_id_list
               )
        assert isinstance(load, bool)
        assert base is not None or child
        assert base is None or (
            (
                child and
                obj_type.name in base.obj_type.children
            ) or
            (
                not child and
                base.obj_type.name in obj_type.children
            )
        )

        self.base = base
        self.child = child
        self.obj_type = obj_type
        self.obj_id_list = None if obj_id_list is None else obj_id_list.copy()
        self.load = load

    def __eq__(self, other):
        return \
            isinstance(other, Request) and \
            self.base == other.base and \
            self.child == other.child and \
            self.obj_type == other.obj_type and \
            self.obj_id_list == other.obj_id_list and \
            self.load == other.load

    @staticmethod
    def _format_id_field(id_field):
        """
        Format an ID field for a string representation of a request.

        Args:
            id_field:   The ID field to format.

        Returns:
            The formatted (quoted or unquoted) ID field.
        """
        # If we can leave the field unquoted
        if re.fullmatch(id_field, _REQUEST_STRING_ID_FIELD_UNQUOTED_PATTERN):
            return id_field
        part_re = re.compile(f"""
            ({_REQUEST_STRING_ID_FIELD_QUOTED_UNESC_CHAR_PATTERN}*) |
            ({_REQUEST_STRING_ID_FIELD_QUOTED_ESC_CHAR_PATTERN})
        """, re.ASCII | re.VERBOSE)
        parts = []
        pos = 0
        while True:
            match = part_re.match(id_field, pos)
            unesc, esc = match.group(1, 2)
            pos = match.end()
            if unesc:
                parts.append(unesc)
            elif esc:
                parts += ["\\", esc]
            elif pos < len(id_field):
                raise Exception(
                    f"ID field cannot be represented in a request string: "
                    f"{id_field}"
                )
            else:
                break
        return "".join(parts)

    @staticmethod
    def _format_id_list_spec(obj_id_list):
        """
        Format an ID list spec for a string representation of a request.

        Args:
            obj_id_list:    The list of IDs to format as a spec,
                            or None if missing.

        Returns:
            The string representation of the ID list spec,
            or empty string if not specified.
        """
        if obj_id_list is None:
            return ""
        return "[" + "; ".join(
            ", ".join(
                Request._format_id_field(obj_id_field)
                for obj_id_field in obj_id
            )
            for obj_id in obj_id_list
        ) + "]"

    def __repr__(self):
        string = ""
        if self.base is not None:
            string += repr(self.base) + " "
        string += "> " if self.child else "< "
        string += self.obj_type.name
        string += Request._format_id_list_spec(self.obj_id_list)
        if self.load:
            string += "#"
        return string

    @staticmethod
    def _expand_parents(schema, base_list, obj_type_expr, obj_id_list, load):
        """
        Expand a single level of parents into a list of requests, for a parsed
        request specification.

        Args:
            schema:         An object type schema to use.
            base_list:      The list of requests to base created requests on.
                            Empty list means requests shouldn't be based on
                            anything (based on the "root" type).
            obj_type_expr:  Object type expression, one of:
                            "*" - all parent types,
                            or a name of the specific parent type.
            obj_id_list:    List of object IDs to limit the request to,
                            or None to not limit the request.
            load:           True, if expanded requests should be marked for
                            loading, False if not.

        Returns:
            A list of requests expanded from the specification, referencing
            the supplied bases.
        """
        assert isinstance(schema, Schema)
        assert isinstance(base_list, list)
        assert all(isinstance(base, Request) for base in base_list)
        assert isinstance(obj_type_expr, str)
        assert obj_id_list is None or \
            (isinstance(obj_id_list, list) and
             all(isinstance(obj_id, tuple) and
                 all(isinstance(part, str) for part in obj_id)
                 for obj_id in obj_id_list))
        assert isinstance(load, bool)

        request_list = []
        # For each base
        for base in base_list:
            base_request_list = []
            # For each base's parent relation
            for obj_type_name, relation in base.obj_type.parents.items():
                if obj_type_expr in ("*", obj_type_name):
                    base_request_list.append(
                        Request(base, False, relation.parent,
                                obj_id_list, load)
                    )
            # If couldn't find any parents
            if not base_request_list:
                if obj_type_expr == "*":
                    base_request_list.append(base)
                else:
                    raise Exception(
                        f"Cannot find parent type {obj_type_expr!r}"
                    )
            request_list += base_request_list
        return request_list

    @staticmethod
    def _expand_children(schema, base_list, obj_type_expr, obj_id_list, load):
        """
        Expand a single level of children into a list of requests, for a parsed
        request specification.

        Args:
            schema:         An object type schema to use.
            base_list:      The list of requests to base created requests on.
                            Empty list means requests shouldn't be based on
                            anything (based on the "root" type).
            obj_type_expr:  Object type expression, one of:
                            "*" - all children types,
                            or a name of the specific child type.
            obj_id_list:    List of object IDs to limit the request to,
                            or None to not limit the request.
            load:           True, if expanded requests should be marked for
                            loading, False if not.

        Returns:
            A list of requests expanded from the specification, referencing
            the supplied bases.
        """
        assert isinstance(schema, Schema)
        assert isinstance(base_list, list)
        assert all(isinstance(base, Request) for base in base_list)
        assert isinstance(obj_type_expr, str)
        assert obj_id_list is None or \
            (isinstance(obj_id_list, list) and
             all(isinstance(obj_id, tuple) and
                 all(isinstance(part, (str, type(None))) for part in obj_id)
                 for obj_id in obj_id_list))
        assert isinstance(load, bool)

        request_list = []
        # If we are based on some objects
        if base_list:
            # For each base
            for base in base_list:
                # Start with an empty per-base request list
                base_request_list = []
                # For each base's child relation
                for obj_type_name, relation in base.obj_type.children.items():
                    if obj_type_expr in ("*", obj_type_name):
                        base_request_list.append(
                            Request(base, True, relation.child,
                                    obj_id_list, load)
                        )
                # If couldn't find any children
                if not base_request_list:
                    if obj_type_expr == "*":
                        base_request_list.append(base)
                    else:
                        raise Exception(
                            f"Cannot find child type {obj_type_expr!r}"
                        )
                request_list += base_request_list
        # Else we're not based on anything (based on root)
        else:
            for obj_type_name, obj_type in schema.types.items():
                if obj_type_expr in ("*", obj_type_name):
                    request_list.append(
                        Request(None, True, obj_type, obj_id_list, load)
                    )
            if obj_type_expr != "*" and not request_list:
                raise Exception(
                    f"Cannot find type {obj_type_expr!r}"
                )
        return request_list

    @staticmethod
    def _expand(schema, base_list, child, obj_type_expr, obj_id_list, load):
        """
        Expand a parsed request specification into a list of requests.

        Args:
            schema:         An object type schema to use.
            base_list:      The list of requests to base created requests
                            on. Empty list means requests shouldn't be
                            based on anything (based on the "root" object).
            child:          True if the created requests are for children
                            of the specified bases. False for parents.
            obj_type_expr:  Object type expression, one of:
                            "*" - all children/parents,
                            or a name of the specific type.
            obj_id_list:    List of object IDs to limit the request to,
                            or None to not limit the request.
            load:           True, if expanded requests should be marked
                            for loading, False if not.

        Returns:
            A list of requests expanded from the specification, referencing
            the supplied bases.
        """
        assert isinstance(base_list, list)
        assert all(isinstance(base, Request) for base in base_list)
        assert isinstance(child, bool)
        assert isinstance(obj_type_expr, str)
        assert obj_id_list is None or \
            (isinstance(obj_id_list, list) and
             all(isinstance(obj_id, tuple) and
                 all(isinstance(part, (str, type(None))) for part in obj_id)
                 for obj_id in obj_id_list))
        assert load in (None, "#", "$")

        # Start with an empty request list
        request_list = []

        # While we can expand
        while True:
            if child:
                request_list = Request._expand_children(
                    schema, base_list, obj_type_expr,
                    obj_id_list, load == "#")
            else:
                request_list = Request._expand_parents(
                    schema, base_list, obj_type_expr,
                    obj_id_list, load == "#")
            # If we are done expanding
            if not obj_type_expr == "*" or request_list == base_list:
                break
            # Rebase for next expansion step
            base_list = request_list

        # If asked to load only the furthest children/objects
        if load == "$":
            for request in request_list:
                request.load = True

        return request_list

    @staticmethod
    def _parse_id(string, pos):
        """
        Parse an ID string from a request.

        Args:
            string: The ID string to parse.
                    Must start with a string formatted according to "id" ABNF
                    rule, possibly followed by whitespace, and optionally
                    anything but a comma.
            pos:    The position to start parsing at.

        Returns:
            A tuple containing parsed ID fields, and the stopping position at
            the end of whitespace following the ID.
        """
        assert LIGHT_ASSERTS or re.match(_REQUEST_STRING_ID_PATTERN,
                                         string[pos:],
                                         re.ASCII | re.VERBOSE)
        id_fields = []

        # NOTE: Not handling failures here, we're expecting a valid string
        while True:
            # If it's a quoted field
            if string[pos] == '"':
                pos += 1
                id_field_chars = []
                while True:
                    char = string[pos]
                    pos += 1
                    if char == '"':
                        break
                    if char == '\\':
                        char = string[pos]
                        pos += 1
                    id_field_chars.append(char)
                id_field = "".join(id_field_chars)
            # Else it's an unquoted field
            else:
                match = _REQUEST_STRING_ID_FIELD_UNQUOTED_RE.match(
                            string, pos)
                pos = match.end()
                id_field = match.group(0)
            # Add the field to the ID
            id_fields.append(id_field)
            # Skip whitespace
            while pos < len(string) and string[pos].isspace():
                pos += 1
            # If it's not an ID field separator
            if pos >= len(string) or string[pos] != ',':
                break
            # Skip ID field separator
            pos += 1
            # Skip whitespace
            while string[pos].isspace():
                pos += 1

        return tuple(id_fields), pos

    @staticmethod
    def _parse_id_list(string):
        """
        Parse an ID list from a request string, stopping at a closing bracket.

        Args:
            string: The ID list string to parse.
                    Must be formatted according to "id_list" ABNF rule.

        Returns:
            A list containing ID field tuples parsed from the string.
        """
        assert LIGHT_ASSERTS or re.fullmatch(_REQUEST_STRING_ID_LIST_PATTERN,
                                             string, re.ASCII | re.VERBOSE)
        # NOTE: Not handling failures here, we're expecting a valid string
        id_list = []
        pos = 0
        while True:
            # We like our "id", pylint: disable=redefined-builtin,invalid-name
            # Parse next ID
            id, pos = Request._parse_id(string, pos)
            id_list.append(id)
            # Stop, if we ran out of IDs
            if pos >= len(string) or string[pos] != ';':
                break
            # Skip ID separator
            pos += 1
            # Skip whitespace
            while string[pos].isspace():
                pos += 1
        return id_list

    @staticmethod
    def _parse_spec(string, obj_id_list_list):
        """
        Parse an optional ID list specification from a request string,
        possibly consuming an element from the supplied object ID list list.

        Args:
            string:             The ID list specification string to parse,
                                or None, meaning the request had no ID list
                                specification.
            obj_id_list_list:   The list of object ID lists to retrieve ID
                                lists for placeholders from, or None, meaning
                                no list was supplied with the request string.
                                Not modified.

        Returns:
            Two items:
                * the retrieved object ID list, or None, if no specification
                  was provided with the request;
                * the list of object ID lists, possibly with the first element
                  removed, if it was consumed by a placeholder.

        Raises:
            Exception with a message, if there were no, or not enough ID
            lists, when required.
        """
        assert string is None or (
            isinstance(string, str) and (
                LIGHT_ASSERTS or
                re.fullmatch(_REQUEST_STRING_SPEC_PATTERN,
                             string, re.ASCII | re.VERBOSE)
            )
        )

        # NOTE: Not handling failures here, we're expecting a valid string
        if string is None:
            return None, obj_id_list_list
        if string == "%":
            if obj_id_list_list is None:
                raise Exception(
                    "No ID list list specified to substitute the placeholder"
                )
            try:
                return obj_id_list_list[0], obj_id_list_list[1:]
            except IndexError:
                raise Exception("Not enough ID lists specified") from None
        # Parse the ID list inside brackets
        return Request._parse_id_list(string[1:-1].strip()), obj_id_list_list

    STRING_DOC = textwrap.dedent("""\
        The request string is a series of request specifications, each
        consisting of a relation character, followed by object type
        specification, followed by the optional ID list specification,
        followed by the optional loading specification. It could be described
        using ABNF:

        whitespace = %x09-0d / %x20 ; Whitespace characters
        relation = ">" /    ; Children of all directly-preceding types,
                            ; or root types, if there's nothing on the left.
                   "<"      ; Parents of all directly-preceding types
        type = name /       ; A parent/child type with specified name
               "*"          ; Furthest parents/children of the types on the
                            ; left, or types themselves which have none.
        name_char = %x30-39 / %x61-7a / "_"
                            ; Lower-case letters, numbers, underscore
        name = 1*name_char  ; Type name
        id_field_unquoted_char = %x30-39 / %x41-5a / %x61-7a /
                                 "_" / ":" / "/" / "." / "?" / "%" / "+" / "-"
                            ; Characters permitted in unquoted ID fields:
                            ; letters, numbers, misc characters
        id_field_quoted_token = (%x20-21 / %x23-5b / %x5d-7e) /
                                "\\" (%x22 / %x5c)
                            ; Character sequences allowed in quoted ID fields:
                            ; anything printable except backslash or
                            ; doublequote, or backslash-escaped
                            ; backslash/doublequote.
        id_field = 1*id_field_unquoted_char /
                   %x22 *id_field_quoted_token %x22
                            ; Quoted/unquoted ID field
        id = id_field *(*whitespace "," *whitespace id)
                            ; ID (a sequence of ID fields)
        id_list = id *(*whitespace ";" *whitespace id_list)
                            ; A list of IDs
        spec = "%" /        ; ID list placeholder.
                            ; Consumes one ID list from the
                            ; separately-supplied list of ID lists to limit
                            ; objects of the types traversed by this request
                            ; specification. Each object type gets the same ID
                            ; list. Not allowed, if the list of ID lists isn't
                            ; supplied.
               "[" *whitespace id_list *whitespace "]"
                            ; Inline ID list
        load = "#" /        ; Load and return objects of all types traversed
                            ; by this request specification.
               "$"          ; Load and return objects of only the furthest
                            ; types traversed by this request specification.
        request = *whitespace relation *whitespace type
                  [*whitespace spec] [*whitespace load]
        request_string = 1*request *whitespace

        Examples:
            >build%#            Load builds with IDs from the first of a
                                separately-specified list of ID lists (if
                                supplied).
            >build%$            The same.
            >build[redhat:1077837]
                                Load a build with ID "redhat:1077837".
            >checkout%>build#   Load builds of checkouts with IDs from
                                the first element of separately-specified list
                                of ID lists (if supplied).
            >test%<build#       Load builds of tests with IDs from the first
                                element of separately-specified list of ID
                                lists (if supplied).
            >test[redhat:1077834_0; redhat:1077834_1]<build#
                                Load builds of tests with IDs
                                "redhat:1077834_0" and "redhat:1077834_1".
            >test%<*#           Load tests with IDs from the first element of
                                separately-specified list of ID lists (if
                                supplied), and all their parents.
            >test%<*$           Load only the furthest (the ultimate) parents
                                of tests with IDs from the optional ID list
                                list, or tests themselves, if they have no
                                parent types.
            >revision%#>*#      Load revisions with IDs from the optional ID
                                list list, and all their children, if any.
            >revision[c763deac7ff, 932e2d61add]#>*#
                                Load the revision with ID
                                (c763deac7ff, 932e2d61add),
                                and all its children, if any.
            >test%<*$>*#        Load the root objects containing tests with
                                the IDs from the optional ID list list, along
                                with all their children.
            >*#                 Load everything in the database.
            >*$                 Load objects of all childless types.
    """)

    @staticmethod
    def parse(string, obj_id_list_list=None, schema=None):
        """
        Parse a request string and its parameter IDs into a chain of Request
        objects. See kcidb.oo.data.Request.STRING_DOC for documentation on
        request strings.

        Args:
            string:             The request string.
            obj_id_list_list:   A list of ID lists to use to filter the
                                requested objects with, in the order specified
                                in the request string. Each ID is a tuple
                                with ID column value strings. If not
                                specified, or specified as None, ID list
                                placeholders are not allowed in the request
                                string.
            schema:             An object type schema to use, or None to use
                                kcidb.oo.data.SCHEMA.

        Returns:
            A list of trailing request objects parsed from the request string.
        """
        assert isinstance(string, str)
        assert obj_id_list_list is None or (
            isinstance(obj_id_list_list, list) and
            all(
                isinstance(obj_id_list, list) and
                all(isinstance(obj_id, tuple) for obj_id in obj_id_list)
                for obj_id_list in obj_id_list_list
            )
        )
        assert schema is None or isinstance(schema, Schema)
        if schema is None:
            schema = SCHEMA

        request_list = []
        pos = 0
        while pos < len(string):
            match = _REQUEST_STRING_RE.match(string, pos)
            if not match:
                raise Exception(f"Invalid request string {string!r} "
                                f"at position {pos}: {string[pos:]!r}")
            relation, obj_type_expr, spec, load = \
                match.group("relation", "type", "spec", "load")
            obj_id_list, obj_id_list_list = Request._parse_spec(
                spec, obj_id_list_list
            )
            try:
                request_list = Request._expand(
                    schema, request_list, relation == ">",
                    obj_type_expr, obj_id_list, load
                )
            except Exception as exc:
                raise Exception(
                    f"Failed expanding request specification "
                    f"at position {pos}: {string[pos:]!r}"
                ) from exc
            pos = match.end()
        if obj_id_list_list:
            raise Exception(
                f"Too many ID lists specified for request {string!r}"
            )
        return request_list


class Source:
    """An abstract source of raw object-oriented (OO) data"""

    # It's OK, pylint: disable=too-few-public-methods
    def oo_query(self, request_list):
        """
        Retrieve raw data for objects specified via a request list.

        Args:
            request_list:   A list of object branch requests ("Request"
                            instances) to fulfill.
        Returns:
            A dictionary of object type names and lists containing retrieved
            raw data of the corresponding type.
        """
        raise NotImplementedError
