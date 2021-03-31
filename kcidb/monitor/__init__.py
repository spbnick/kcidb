"""Kernel CI reporting - monitor"""

import kcidb_io as io
from kcidb import oo
from kcidb.monitor import subscriptions, output, spool, misc
from kcidb.misc import LIGHT_ASSERTS

__all__ = [
    "subscriptions",
    "output",
    "spool",
    "misc",
    "match",
    "match_oo",
    "match_new_io",
]


# TODO: Remove once transitioned to the new ORM
def match_oo(oo_data, match_map=None):
    """
    Generate notifications for any subscriptions matching OO data.

    Args:
        oo_data:    The object-oriented (OO) representation of report data to
                    generate notifications for.
        match_map:  The map of subscription match functions: a dictionary with
                    OO data object list names and a list of tuples, each
                    containing the name of the subscription and a match
                    function.

                    Each function must accept an object from the corresponding
                    object list in OO data, and return an iterable producing
                    kcidb.monitor.output.NotificationMessage objects, or None,
                    which is equivalent to an empty iterable.

                    The default is a dictionary of matching functions from all
                    kcidb.monitor.subscriptions.* modules, where each is
                    called "match_<OBJ_NAME>", where "<OBJ_NAME>" is an object
                    list name without the "s" ending.

    Returns:
        The list of notifications: kcidb.monitor.output.Notification objects.
    """
    assert LIGHT_ASSERTS or oo.is_valid(oo_data)

    if match_map is None:
        match_map = subscriptions.MATCH_MAP
    notifications = []
    # For each object list and its subscription function list
    for obj_list_name, subscription_function_list in match_map.items():
        assert isinstance(obj_list_name, str)
        assert obj_list_name
        assert obj_list_name in io.schema.LATEST.tree
        assert isinstance(subscription_function_list, list)
        # For each subscription's name and its match function
        for subscription, function in subscription_function_list:
            assert isinstance(subscription, str)
            assert callable(function)
            # For each object in the OO data object list
            for obj in oo_data.get(obj_list_name, {}).values():
                # For each matched notification message, if any
                for message in function(obj) or []:
                    assert isinstance(message, output.NotificationMessage)
                    notifications.append(
                        output.Notification(obj_list_name, obj,
                                            subscription, message)
                    )
    return notifications


# TODO: Remove once transitioned to the new ORM
def match_new_io(base_io, new_io, match_map=None, copy=True):
    """
    Generate notifications for new I/O data being added to base I/O data.

    Args:
        base_io:    The existing (base) I/O data being added to, and possibly
                    referred to by the arriving (new) I/O data. Will be used
                    to complete the data being notified about. Can already
                    contain the new I/O data, it will be considered "new"
                    regardless.
        new_io:     The arriving (new) I/O data being added to the existing
                    (base) data. Can refer to the existing I/O data. The new
                    I/O data can already be added to the base I/O data,
                    anything in the new data will be considered "new"
                    regardless.
        match_map:  The map of subscription match functions: a dictionary with
                    OO data object list names and a list of tuples, each
                    containing the name of the subscription and a match
                    function.

                    Each function must accept an object from the corresponding
                    object list in OO data, and return an iterable producing
                    kcidb.monitor.output.NotificationMessage objects, or None,
                    which is equivalent to an empty iterable.

                    The default is a dictionary of matching functions from all
                    kcidb.subscriptions.* modules, where each is called
                    "match_<OBJ_NAME>", where "<OBJ_NAME>" is an object list
                    name without the "s" ending.
        copy:       True, if the data should be copied before
                    referencing/modifying. False, if the data could be
                    referenced and modified in-place.
                    Optional, default is True.

    Returns:
        The list of notifications: kcidb.monitor.output.Notification objects.
    """
    assert LIGHT_ASSERTS or io.schema.is_valid(base_io)
    assert LIGHT_ASSERTS or io.schema.is_valid(new_io)

    # Merge the new data into the base (*copy* new data as we'll need it)
    merged_io = io.merge(base_io, [new_io],
                         copy_target=copy, copy_sources=True)
    # Convert both to OO representation
    merged_oo = oo.from_io(merged_io, copy=False)
    new_oo = oo.from_io(new_io, copy=copy)
    # Remove all objects with missing parents from the merged data
    rooted_oo = oo.remove_orphans(merged_oo)
    # Delist everything except loaded or modified objects, but keep references
    masked_oo = oo.apply_mask(rooted_oo, new_oo)
    # Generate notifications
    return match_oo(masked_oo, match_map)


def match(oo_data, match_map=None):
    """
    Generate notifications for subscriptions matching supplied OO data.

    Args:
        oo_data:    A dictionary of object type names and lists containing
                    objects of the corresponding type. E.g. as returned by
                    kcidb.oo.Client.query().
        match_map:  The map of subscription match functions: a dictionary with
                    OO data object type names and a list of tuples, each
                    containing the name of the subscription and a match
                    function.

                    Each function must accept an object from the corresponding
                    object list in OO data, and return an iterable producing
                    kcidb.monitor.output.NotificationMessage objects, or None,
                    which is equivalent to an empty iterable.

                    The default is a dictionary of matching functions from all
                    kcidb.monitor.subscriptions.* modules, where each is
                    called "match_<OBJ_NAME>", where "<OBJ_NAME>" is an object
                    list name without the "s" ending.
    """
    assert isinstance(oo_data, dict)
    if match_map is None:
        match_map = subscriptions.MATCH_MAP
    assert isinstance(match_map, dict)
    assert set(oo_data) <= set(match_map)
    notifications = []
    # For each object list and its subscription function list
    for obj_type_name, subscription_function_list in match_map.items():
        assert isinstance(obj_type_name, str)
        assert obj_type_name
        assert isinstance(subscription_function_list, list)
        # For each subscription's name and its match function
        for subscription, function in subscription_function_list:
            assert isinstance(subscription, str)
            assert callable(function)
            # For each object in the OO data object list
            for obj in oo_data.get(obj_type_name, []):
                # For each matched notification message, if any
                for message in function(obj) or []:
                    assert isinstance(message, output.NotificationMessage)
                    notifications.append(
                        output.Notification(obj_type_name, obj,
                                            subscription, message)
                    )
    return notifications
