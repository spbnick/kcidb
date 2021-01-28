"""Kernel CI reporting"""

import sys
import email
import logging
import jsonschema
import jq
import kcidb_io as io
from kcidb import db, mq, oo, monitor, tests, unittest, misc
from kcidb.misc import LIGHT_ASSERTS

__all__ = [
    "db", "mq", "oo", "monitor", "tests", "unittest",
    "io_schema",
    "Client",
    "submit_main",
    "query_main",
    "schema_main",
    "validate_main",
    "upgrade_main",
    "summarize_main",
    "describe_main",
    "notify_main",
    "merge_main",
    "count_main",
]

# pylint: disable=invalid-name,fixme
# TODO Remove once users switched to kcidb_io.schema
# Compatibility alias
io_schema = io.schema

# Module's logger
LOGGER = logging.getLogger(__name__)


class DatabaseNotInitialized(Exception):
    """Database is not initialized exception"""
    def __init__(self):
        super().__init__("Database is not initialized")


class Client:
    """Kernel CI reporting client"""

    def __init__(self, database=None, project_id=None, topic_name=None):
        """
        Initialize a reporting client

        Args:
            database:       The database specification string to use for
                            accessing the report database.
                            Can be None to have querying disabled.
            project_id:     ID of the Google Cloud project hosting the message
                            queue accepting submissions.
                            Can be None to have submitting disabled.
            topic_name:     Name of the message queue topic to publish
                            submissions to. The message queue should be
                            located within the specified Google Cloud project.
                            Can be None, to have submitting disabled.

        Raises:
            `kcidb.DatabaseNotInitialized` if the database is not
            initialized.
            `kcidb.db.IncompatibleSchema` if the database schema
            is incompatible with the latest I/O schema.
        """
        assert database is None or \
            isinstance(database, str) and database
        assert project_id is None or \
            isinstance(project_id, str) and project_id
        assert topic_name is None or \
            isinstance(topic_name, str) and topic_name
        if database is None:
            self.db_client = None
        else:
            self.db_client = db.Client(database)
            if not self.db_client.is_initialized():
                raise DatabaseNotInitialized()
        self.mq_publisher = \
            mq.Publisher(project_id, topic_name) if project_id and topic_name \
            else None

    def submit(self, data):
        """
        Submit reports.

        Args:
            data:   The JSON report data to submit.
                    Must adhere to a version of I/O schema.

        Returns:
            Submission ID string.

        Raises:
            `NotImplementedError`, if not supplied with a project ID or an MQ
            topic name at initialization time.
        """
        assert LIGHT_ASSERTS or io.schema.is_valid(data)
        if not self.mq_publisher:
            raise NotImplementedError
        return self.mq_publisher.publish(data)

    def submit_iter(self, data_iter, done_cb=None):
        """
        Submit reports returned by an iterator.

        Args:
            data_iter:  An iterator returning the JSON report data to submit.
                        Each must adhere to a version of I/O schema.
            done_cb:    A function to call when a report is successfully
                        submitted. Will be called with the submission ID of
                        each report returned by the iterator, in order.

        Raises:
            `NotImplementedError`, if not supplied with a project ID or an MQ
            topic name at initialization time.
        """
        if not self.mq_publisher:
            raise NotImplementedError
        return self.mq_publisher.publish_iter(data_iter, done_cb=done_cb)

    # We can live with this for now, pylint: disable=too-many-arguments
    def query_iter(self, ids=None,
                   children=False, parents=False,
                   objects_per_report=0):
        """
        Match and fetch reports, in object number-limited chunks.

        Args:
            ids:                A dictionary of object list names, and lists
                                of IDs of objects to match. None means empty
                                dictionary.
            children:           True if children of matched objects should be
                                matched as well.
            parents:            True if parents of matched objects should be
                                matched as well.
            objects_per_report: A positive integer number of objects per each
                                returned report, or zero for no limit.

        Returns:
            An iterator returning report JSON data adhering to the latest I/O
            schema version, each containing at most the specified number of
            objects.

        Raises:
            `NotImplementedError`, if not supplied with a dataset name at
            initialization time;
        """
        assert ids is None or isinstance(ids, dict)
        if ids is None:
            ids = dict()
        assert all(isinstance(k, str) and isinstance(v, list) and
                   all(isinstance(e, str) for e in v)
                   for k, v in ids.items())

        assert isinstance(objects_per_report, int)
        assert objects_per_report >= 0

        if not self.db_client:
            raise NotImplementedError

        return self.db_client.query_iter(ids=ids,
                                         children=children, parents=parents,
                                         objects_per_report=objects_per_report)

    def query(self, ids=None, children=False, parents=False):
        """
        Match and fetch report objects.

        Args:
            ids:        A dictionary of object list names, and lists of IDs of
                        objects to match. None means empty dictionary.
            children:   True if children of matched objects should be matched
                        as well.
            parents:    True if parents of matched objects should be matched
                        as well.

        Returns:
            The fetched JSON data adhering to the latest I/O schema version.

        Raises:
            `NotImplementedError`, if not supplied with a dataset name at
            initialization time;
        """
        assert ids is None or isinstance(ids, dict)
        if ids is None:
            ids = dict()
        assert all(isinstance(k, str) and isinstance(v, list) and
                   all(isinstance(e, str) for e in v)
                   for k, v in ids.items())

        if self.db_client:
            data = self.db_client.query(ids=ids,
                                        children=children, parents=parents)
        else:
            raise NotImplementedError

        assert LIGHT_ASSERTS or io.schema.is_valid_latest(data)
        return data


def submit_main():
    """Execute the kcidb-submit command-line tool"""
    sys.excepthook = misc.log_and_print_excepthook
    description = \
        'kcidb-submit - Submit Kernel CI reports, print submission IDs'
    parser = misc.ArgumentParser(description=description)
    parser.add_argument(
        '-p', '--project',
        help='ID of the Google Cloud project containing the message queue',
        required=True
    )
    parser.add_argument(
        '-t', '--topic',
        help='Name of the message queue topic to publish to',
        required=True
    )
    args = parser.parse_args()
    client = Client(project_id=args.project, topic_name=args.topic)

    def print_submission_id(submission_id):
        print(submission_id, file=sys.stdout)
        sys.stdout.flush()

    client.submit_iter(
        (io.schema.upgrade(io.schema.validate(data), copy=False)
         for data in misc.json_load_stream_fd(sys.stdin.fileno())),
        done_cb=print_submission_id
    )


def query_main():
    """Execute the kcidb-query command-line tool"""
    sys.excepthook = misc.log_and_print_excepthook
    description = \
        "kcidb-query - Query Kernel CI reports"
    parser = db.QueryArgumentParser(description=description)
    args = parser.parse_args()
    client = Client(database=args.database)
    query_iter = client.query_iter(
        ids=dict(checkouts=args.checkout_ids,
                 builds=args.build_ids,
                 tests=args.test_ids),
        parents=args.parents,
        children=args.children,
        objects_per_report=args.objects_per_report
    )
    misc.json_dump_stream(
        query_iter, sys.stdout, indent=args.indent, seq=args.seq
    )


def schema_main():
    """Execute the kcidb-schema command-line tool"""
    sys.excepthook = misc.log_and_print_excepthook
    description = 'kcidb-schema - Output latest I/O JSON schema'
    parser = misc.OutputArgumentParser(description=description)
    args = parser.parse_args()
    misc.json_dump(io.schema.LATEST.json, sys.stdout,
                   indent=args.indent, seq=args.seq)


def validate_main():
    """Execute the kcidb-validate command-line tool"""
    sys.excepthook = misc.log_and_print_excepthook
    description = 'kcidb-validate - Validate I/O JSON data'
    parser = misc.ArgumentParser(description=description)
    parser.parse_args()

    for data in misc.json_load_stream_fd(sys.stdin.fileno()):
        io.schema.validate(data)


def upgrade_main():
    """Execute the kcidb-upgrade command-line tool"""
    sys.excepthook = misc.log_and_print_excepthook
    description = 'kcidb-upgrade - Upgrade I/O JSON data to latest schema'
    parser = misc.OutputArgumentParser(description=description)
    args = parser.parse_args()

    misc.json_dump_stream(
        (
            io.schema.upgrade(io.schema.validate(data), copy=False)
            for data in misc.json_load_stream_fd(sys.stdin.fileno())
        ),
        sys.stdout, indent=args.indent, seq=args.seq
    )


def count_main():
    """Execute the kcidb-count command-line tool"""
    sys.excepthook = misc.log_and_print_excepthook
    description = 'kcidb-count - Count number of objects in I/O JSON data'
    parser = misc.ArgumentParser(description=description)
    parser.parse_args()

    for data in misc.json_load_stream_fd(sys.stdin.fileno()):
        print(io.count(io.schema.validate(data)), file=sys.stdout)
        sys.stdout.flush()


def summarize_main():
    """Execute the kcidb-summarize command-line tool"""
    sys.excepthook = misc.log_and_print_excepthook
    description = 'kcidb-summarize - Output summaries of report objects'
    parser = misc.ArgumentParser(description=description)
    parser.add_argument(
        'obj_list_name',
        metavar='LIST',
        choices={n for n in io.schema.LATEST.tree if n},
        help='Name of the object list to output (%(choices)s)'
    )
    parser.add_argument(
        'ids',
        metavar='ID',
        nargs='*',
        default=[],
        help='ID of the object to limit output to'
    )
    args = parser.parse_args()
    for io_data in misc.json_load_stream_fd(sys.stdin.fileno()):
        io_data = io.schema.upgrade(io.schema.validate(io_data), copy=False)
        oo_data = oo.from_io(io_data)
        obj_map = oo_data.get(args.obj_list_name, {})
        for obj_id in args.ids or obj_map:
            if obj_id in obj_map:
                print(obj_map[obj_id].summarize(), file=sys.stdout)
                sys.stdout.flush()


def describe_main():
    """Execute the kcidb-describe command-line tool"""
    sys.excepthook = misc.log_and_print_excepthook
    description = 'kcidb-describe - Output descriptions of report objects'
    parser = misc.ArgumentParser(description=description)
    parser.add_argument(
        'obj_list_name',
        metavar='LIST',
        choices={n for n in io.schema.LATEST.tree if n},
        help='Name of the object list to output (%(choices)s)'
    )
    parser.add_argument(
        'ids',
        metavar='ID',
        nargs='*',
        default=[],
        help='ID of the object to limit output to'
    )
    args = parser.parse_args()
    for io_data in misc.json_load_stream_fd(sys.stdin.fileno()):
        io_data = io.schema.upgrade(io.schema.validate(io_data), copy=False)
        oo_data = oo.from_io(io_data)
        obj_map = oo_data.get(args.obj_list_name, {})
        for obj_id in args.ids or obj_map:
            if obj_id in obj_map:
                sys.stdout.write(obj_map[obj_id].describe())
                sys.stdout.write("\x00")
                sys.stdout.flush()


def merge_main():
    """Execute the kcidb-merge command-line tool"""
    sys.excepthook = misc.log_and_print_excepthook
    description = 'kcidb-merge - Upgrade and merge I/O data sets'
    parser = misc.OutputArgumentParser(description=description)
    args = parser.parse_args()

    sources = [
        io.schema.validate(data)
        for data in misc.json_load_stream_fd(sys.stdin.fileno())
    ]
    merged_data = io.merge(io.new(), sources,
                           copy_target=False, copy_sources=False)
    misc.json_dump(merged_data, sys.stdout, indent=args.indent, seq=args.seq)


def notify_main():
    """Execute the kcidb-notify command-line tool"""
    sys.excepthook = misc.log_and_print_excepthook
    description = 'kcidb-notify - Generate notifications for new I/O data'
    parser = misc.ArgumentParser(description=description)
    parser.add_argument(
        'base',
        metavar='BASE_FILE',
        nargs='?',
        help='Path to a JSON file with base I/O data'
    )
    args = parser.parse_args()

    base = io.new()
    if args.base is not None:
        try:
            with open(args.base, "r") as json_file:
                base_reports = [
                    io.schema.validate(data)
                    for data in misc.json_load_stream_fd(json_file.fileno())
                ]
                base = io.merge(base, base_reports,
                                copy_target=False, copy_sources=False)
        except (jq.JSONParseError,
                jsonschema.exceptions.ValidationError) as err:
            raise Exception("Failed reading base file") from err

    try:
        for new in misc.json_load_stream_fd(sys.stdin.fileno()):
            new = io.schema.validate(new)
            for notification in monitor.match_new_io(base, new):
                sys.stdout.write(
                    notification.render().
                    as_string(policy=email.policy.SMTPUTF8)
                )
                sys.stdout.write("\x00")
                sys.stdout.flush()
            base = io.merge(base, [new],
                            copy_target=False, copy_sources=False)
    except (jq.JSONParseError,
            jsonschema.exceptions.ValidationError) as err:
        raise Exception("Failed reading new I/O data") from err
