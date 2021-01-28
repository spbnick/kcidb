"""Kernel CI reporting database - misc definitions"""

from abc import ABC, abstractmethod
import kcidb_io as io
import kcidb.oo.data as oo_data
from kcidb.misc import LIGHT_ASSERTS


class Overload(Exception):
    """Database cannot accept more data at the moment, try again later"""


class Driver(ABC):
    """An abstract Kernel CI report database driver"""

    # Calm down, we're abstract, pylint: disable=no-self-use

    # A (multiline) string documenting the format
    # of the database parameter string
    PARAMS_DOC = None

    @abstractmethod
    def __init__(self, params):
        """
        Initialize the Kernel CI report database driver.

        Args:
            params: A string containing parameters for accessing a database.
                    Or None, if not specified.
        """
        assert params is None or isinstance(params, str)

    @abstractmethod
    def get_schema_version(self):
        """
        Get the version of the I/O schema the database schema corresponds to,
        if any.

        Returns:
            Major and minor version numbers,
            or (None, None) if the database is uninitialized.
        """

    @abstractmethod
    def init(self):
        """
        Initialize the database. The database must be empty (uninitialized).
        """

    @abstractmethod
    def cleanup(self):
        """
        Cleanup (empty) the database, removing all data.
        The database must be initialized.
        """

    @abstractmethod
    def get_last_modified(self):
        """
        Get the time the data in the database was last modified.
        The database must be initialized.

        Returns:
            The datetime object representing the last modification time.
        """

    @abstractmethod
    def dump_iter(self, objects_per_report):
        """
        Dump all data from the database in object number-limited chunks.
        The database must be initialized.

        Args:
            objects_per_report: An integer number of objects per each returned
                                report data, or zero for no limit.

        Returns:
            An iterator returning report JSON data adhering to the latest I/O
            schema version, each containing at most the specified number of
            objects.
        """
        assert isinstance(objects_per_report, int)
        assert objects_per_report >= 0

    @abstractmethod
    def query_iter(self, ids, children, parents, objects_per_report):
        """
        Match and fetch objects from the database, in object number-limited
        chunks. The database must be initialized.

        Args:
            ids:                A dictionary of object list names, and lists
                                of IDs of objects to match.
            children:           True if children of matched objects should be
                                matched as well.
            parents:            True if parents of matched objects should be
                                matched as well.
            objects_per_report: An integer number of objects per each returned
                                report data, or zero for no limit.

        Returns:
            An iterator returning report JSON data adhering to the latest I/O
            schema version, each containing at most the specified number of
            objects.
        """
        assert isinstance(ids, dict)
        assert all(isinstance(k, str) and isinstance(v, list) and
                   all(isinstance(e, str) for e in v)
                   for k, v in ids.items())
        del children
        del parents
        assert isinstance(objects_per_report, int)
        assert objects_per_report >= 0

    @abstractmethod
    def oo_query(self, request_list):
        """
        Query raw object-oriented data from the database.
        The database must be initialized.

        Args:
            request_list:   A list of object branch requests
                            ("kcidb.oo.data.Request" instances) to fulfill.
        Returns:
            A dictionary of object type names and lists containing retrieved
            objects of the corresponding type.
        """
        assert isinstance(request_list, list)
        assert all(isinstance(r, oo_data.Request) for r in request_list)

    @abstractmethod
    def load(self, data):
        """
        Load data into the database.
        The database must be initialized.

        Args:
            data:   The JSON data to load into the database.
                    Must adhere to the latest version of the I/O schema.

        Raises:
            Overload - the database cannot accept any more data at the moment,
            try again later.
        """
        assert LIGHT_ASSERTS or io.schema.is_valid_latest(data)
