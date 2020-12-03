"""
Kernel CI report object-oriented (OO) data - I/O data with OO interface and a
few useful additions. The structure always corresponds to the latest I/O
schema.

The I/O data is converted to objects according to the following rules.

1. Version object is preserved as is to let the consumer know which I/O schema
   the OO data originated from.

2. Top-level object lists are transformed into dictionaries with keys being
   object's "id" properties, and values being the object data represented by
   instances of Node class, as follows.

    1. Each property in the I/O data will be converted to an attribute.
    2. Scalar values will be kept as they are.
    3. Both lists and dictionaries will be converted recursively.
    4. Lists will be kept as lists.
    5. Dictionaries will be converted, again, to instances of Node class,
       except values of "misc" keys, which will stay dictionaries.
    6. Top-level Node instances will also have additional attributes, all
       with names ending with an underscore, to separate them from pure I/O
       data:
        1. An attribute named after the owning object (if any) containing a
           reference to it. E.g. a "test" instance will have a "build_"
           attribute, pointing to its build.
        2. An attribute named after children collections (if any), containing
           a dictionary of children "id" properties and references to their
           Node instances. E.g. a "build" instance will have a "tests_"
           attribute pointing to its tests.
        3. Tests get "status_" attribute, with kcidb.oo.misc.Status enum
           values, which can be sorted by severity.
        4. Tests get "waived_" attribute, with kcidb.oo.misc.Waived enum
           values, which can be sorted by severity.
"""

from kcidb_io import schema
from kcidb.misc import LIGHT_ASSERTS
from kcidb.oo.misc import Node
from kcidb.oo.checkout import Node as Checkout
from kcidb.oo.build import Node as Build
from kcidb.oo.test import Node as Test
from kcidb.oo.test import NodeEnvironment as TestEnvironment
from kcidb.oo.data import Type, SCHEMA, Request, Source

__all__ = [
    "Node", "Checkout", "Build", "Test", "TestEnvironment",
    "from_io", "is_valid", "to_io", "remove_orphans", "apply_mask",
]

# A map of names of I/O data object lists and their OO classes
NODE_CLASS_MAP = dict(
    checkouts=Checkout,
    builds=Build,
    tests=Test
)


def _obj_list_from_io(oo_data, io_data, obj_list_name):
    """
    Convert I/O data for an object list and all its children to OO data.

    Args:
        oo_data:        The OO data to output the converted objects into.
        io_data:        The I/O data to get the original objects from.
        obj_list_name:  The name of the object list to convert.
    """
    assert isinstance(oo_data, dict)
    assert LIGHT_ASSERTS or schema.is_valid_latest(io_data)
    assert isinstance(obj_list_name, str)
    assert obj_list_name.endswith("s")
    obj_name = obj_list_name[:-1]
    child_list_name_list = schema.LATEST.tree[obj_list_name]

    # Convert all objects in this list, add child map attributes
    oo_obj_map = {
        io_obj['id']:
            NODE_CLASS_MAP.get(obj_list_name, Node)(
                io_obj, {n + "_": {} for n in child_list_name_list}
            )
        for io_obj in io_data.get(obj_list_name, [])
    }

    # For each child object list
    for child_list_name in child_list_name_list:
        # Convert all child objects
        _obj_list_from_io(oo_data, io_data, child_list_name)
        # For each child object
        for oo_child_id, oo_child in oo_data.get(child_list_name, {}).items():
            # Get the child's parent, if we can
            oo_obj_id = getattr(oo_child, obj_name + "_id")
            oo_obj = oo_obj_map.get(oo_obj_id, None)
            # Link parent from child
            setattr(oo_child, obj_name + "_", oo_obj)
            # Link child from parent, if any
            if oo_obj:
                getattr(oo_obj, child_list_name + "_")[oo_child_id] = oo_child

    # Output the converted object map, if not empty
    if oo_obj_map:
        oo_data[obj_list_name] = oo_obj_map


def from_io(io_data, copy=True):
    """
    Convert I/O data to OO data.

    Args:
        io_data:    The data to convert to objects.
        copy:       True, if the data should be copied before
                    referencing/modifying. False, if the data should be
                    referenced and modified in-place.
                    Optional, default is True.

    Returns:
        The converted OO data.
    """
    assert LIGHT_ASSERTS or schema.is_valid(io_data)
    io_data = schema.upgrade(io_data, copy)

    oo_data = dict(version=dict(major=io_data['version']['major'],
                                minor=io_data['version']['minor']))

    for obj_list_name in schema.LATEST.tree[""]:
        _obj_list_from_io(oo_data, io_data, obj_list_name)

    return oo_data


def _to_io(oo_data):
    """
    Convert OO data to I/O data, without validating the result.

    Args:
        oo_data:    The OO data to convert to I/O data.

    Returns:
        The converted, but unvalidated I/O data.
    """
    io_data = dict(version=dict(major=oo_data['version']['major'],
                                minor=oo_data['version']['minor']))

    for obj_list_name in schema.LATEST.tree:
        if obj_list_name:
            obj_list = [
                oo_obj.to_io()
                for oo_obj in oo_data.get(obj_list_name, {}).values()
            ]
            if obj_list:
                io_data[obj_list_name] = obj_list

    return io_data


def is_valid(oo_data):
    """
    Check that OO data is valid.

    Args:
        oo_data:    The OO data to check.

    Returns:
        True if the OO data is valid, false otherwise.
    """
    if not isinstance(oo_data, dict):
        return False

    required_keys = set(("version",))
    allowed_keys = \
        (set(schema.LATEST.tree.keys()) | set(("version",))) - set(("",))
    if not set(oo_data.keys()) & required_keys:
        return False
    if set(oo_data.keys()) > allowed_keys:
        return False

    # pylint: disable=fixme
    # TODO Validate tree node types and object links
    return schema.is_valid_latest(_to_io(oo_data))


def to_io(oo_data):
    """
    Convert OO data to I/O data.

    Args:
        oo_data:    The OO data to convert to I/O data.

    Returns:
        The converted I/O data.
    """
    io_data = _to_io(oo_data)
    assert LIGHT_ASSERTS or schema.is_valid_latest(io_data)
    return io_data


def _obj_list_remove_orphans(oo_data, obj_list_name):
    """
    Remove objects at least one parent missing from an object list in OO data,
    as well as from its child object lists.

    Args:
        oo_data:        The OO data to remove orphans from. Will be modified.
        obj_list_name:  The name of the object list to remove orphans from.
    """
    assert LIGHT_ASSERTS or is_valid(oo_data)
    assert isinstance(obj_list_name, str)
    assert obj_list_name.endswith("s")
    obj_name = obj_list_name[:-1]
    child_list_name_list = schema.LATEST.tree[obj_list_name]
    parent_list_name_list = [
        list_name
        for list_name, child_list_name_list in schema.LATEST.tree.items()
        if list_name and obj_list_name in child_list_name_list
    ]
    assert all(n.endswith("s") for n in parent_list_name_list)

    obj_list = oo_data.get(obj_list_name, {})

    # For each object in the list
    for obj_id, obj in list(obj_list.items()):
        # For each parent object list
        for parent_list_name in parent_list_name_list:
            # If a parent is missing
            if not getattr(obj, parent_list_name[:-1] + "_"):
                # Unlink from remaining parents
                # pylint: disable=redefined-outer-name
                for parent_list_name in parent_list_name_list:
                    parent = getattr(obj, parent_list_name[:-1] + "_")
                    if parent:
                        del getattr(parent, obj_list_name + "_")[obj_id]
                # Unlink from children
                for child_list_name in child_list_name_list:
                    for child_obj in \
                            getattr(obj, child_list_name + "_").values():
                        setattr(child_obj, obj_name + "_", None)
                # Remove object from the list
                del obj_list[obj_id]
                break

    # For each child object list
    for child_list_name in child_list_name_list:
        _obj_list_remove_orphans(oo_data, child_list_name)

    assert LIGHT_ASSERTS or is_valid(oo_data)


def remove_orphans(oo_data):
    """
    Remove non-root objects without parents from OO data.

    Args:
        oo_data:    The OO data to remove orphans from. Will be modified.

    Returns:
        The OO data with orphans removed.
    """
    assert LIGHT_ASSERTS or is_valid(oo_data)
    for obj_list_name in schema.LATEST.tree[""]:
        _obj_list_remove_orphans(oo_data, obj_list_name)
    assert LIGHT_ASSERTS or is_valid(oo_data)
    return oo_data


def _obj_list_apply_mask(output, base, mask, obj_list_name):
    """
    Mask an object list in "base" OO data, with the same object list in "mask"
    OO data, as well as their children object lists.

    Args:
        output: The output masked OO data.
        base:   The base OO data to mask.
        mask:   The mask OO data to mask with.
    """
    assert LIGHT_ASSERTS or is_valid(output)
    assert LIGHT_ASSERTS or is_valid(base)
    assert LIGHT_ASSERTS or is_valid(mask)
    assert isinstance(obj_list_name, str)
    assert obj_list_name.endswith("s")
    obj_name = obj_list_name[:-1]
    child_list_name_list = schema.LATEST.tree[obj_list_name]

    # Mask all objects in this list
    obj_map = {
        k: v
        for k, v in base.get(obj_list_name, {}).items()
        if k in mask.get(obj_list_name, {})
    }

    # For each child object list
    for child_list_name in child_list_name_list:
        # Mask all child objects
        _obj_list_apply_mask(output, base, mask, child_list_name)
        # For each masked child object
        for child in output.get(child_list_name, {}).values():
            # Add its parent to the masked output, if any
            obj = getattr(child, obj_name + "_")
            if obj:
                obj_map[obj.id] = obj

    # Output the masked object list, if not empty
    if obj_map:
        output[obj_list_name] = obj_map
    assert LIGHT_ASSERTS or is_valid(output)


def apply_mask(base, mask):
    """
    Given "base" OO data, and "mask" OO data, return a new OO data containing
    objects from "base", which have the same IDs as objects in "mask", or are
    their parents. Will keep links intact, i.e. the resulting OO data may
    reference less objects directly, from top object lists, than indirectly,
    via parent-child links.

    Args:
        base:   The base OO data to mask.
        mask:   The mask OO data to mask with.

    Returns:
        The masked OO data referencing objects from "base".
    """
    assert LIGHT_ASSERTS or is_valid(base)
    assert LIGHT_ASSERTS or is_valid(mask)

    output = dict(version=dict(major=base['version']['major'],
                               minor=base['version']['minor']))

    for obj_list_name in schema.LATEST.tree[""]:
        _obj_list_apply_mask(output, base, mask, obj_list_name)

    assert LIGHT_ASSERTS or is_valid(output)
    return output


class Object:
    """An object-oriented representation of a database object"""

    # Calm down, pylint: disable=redefined-builtin,invalid-name

    def __init__(self, client, type, data):
        """
        Initialize the representation.

        Args:
            client:     The object-oriented database client to query for
                        references.
            type:       The type of represented object.
                        Instance of kcidb.oo.data.Type.
            data:       The raw data of the object to represent.
        """
        assert isinstance(client, Client)
        assert isinstance(type, Type)
        assert LIGHT_ASSERTS or type.is_valid(data)
        self._client = client
        self._type = type
        self._data = data

    def get_id(self):
        """
        Retrieve a tuple of field values identifying the object globally.

        Returns:
            A tuple of values of object fields identifying it globally.
        """
        return self._type.get_id(self._data)

    def __hash__(self):
        return hash(self.get_id())

    def __eq__(self, other):
        return isinstance(other, Object) and self.get_id() == other.get_id()

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        id = self.get_id()
        if name in self._type.parents:
            response = self._client.query(
                Request.parse(
                    ">" + self._type.name + "%<" + name + "#",
                    [[id]]
                )
            )
            try:
                return response[name][0]
            except (KeyError, IndexError):
                return None
        if name.endswith("s"):
            child_type_name = name[:-1]
            if child_type_name in self._type.children:
                return self._client.query(
                    Request.parse(
                        ">" + self._type.name + "%>" + child_type_name + "#",
                        [[id]]
                    )
                )[child_type_name]
        raise AttributeError(f"Attribute {name!r} not found")


class Client:
    """Object-oriented data client"""

    def __init__(self, source):
        """
        Initialize the client.

        Args:
            source: Raw object-oriented data source, an instance of
                    kcidb.oo.data.Source.
        """
        assert isinstance(source, Source)
        self.source = source

    def query(self, request_list):
        """
        Retrieve objects specified via a request list.

        Args:
            request_list:   A list of object branch requests ("Request"
                            instances) to fulfill.
        Returns:
            A dictionary of object type names and lists containing retrieved
            objects of the corresponding type.
        """
        assert isinstance(request_list, list)
        assert all(isinstance(r, Request) for r in request_list)
        return {
            obj_type_name: [
                Object(self, SCHEMA.types[obj_type_name], obj_data)
                for obj_data in obj_data_list
            ]
            for obj_type_name, obj_data_list in
            self.source.oo_query(request_list).items()
        }
