"""
Kernel CI SQLite report database schema.

Always corresponds to the latest I/O schema.
"""
import json
from enum import Enum


class Constraint(Enum):
    """A column's constraint"""
    PRIMARY_KEY = "PRIMARY KEY"
    NOT_NULL = "NOT NULL"


class Column:
    """A column description"""

    # Calm down, pylint: disable=redefined-builtin
    def __init__(self, type, constraint=None, pack=None, unpack=None):
        """
        Initialize the column description.

        Args:
            type:           The name of the SQLite type (affinity) to use for
                            this column.
            constraint:     The column's constraint.
                            A member of the Constraint enum, or None,
                            meaning no constraint.
            pack:           The function packing the JSON representation of
                            column's values into the SQLite representation.
            unpack:         The function unpacking the SQLite representation
                            of column's values into the JSON representation.
        """
        assert isinstance(type, str)
        assert constraint is None or isinstance(constraint, Constraint)
        assert pack is None or callable(pack)
        assert unpack is None or callable(unpack)
        self.type = type
        self.constraint = constraint
        self.pack = pack or (lambda x: x)
        self.unpack = unpack or (lambda x: x)

    def format_nameless_def(self):
        """
        Format the "column-def" part of SQLite's "CREATE TABLE" statement
        (https://sqlite.org/syntax/column-def.html) without the "column-name"
        part.

        Returns: The formatted (nameless) "column-def".
        """
        nameless_def = self.type
        if self.constraint:
            nameless_def += " " + self.constraint.value
        return nameless_def


class BoolColumn(Column):
    """A boolean column"""

    # Calm down, pylint: disable=redefined-builtin
    def __init__(self, constraint=None):
        """
        Initialize the column description.

        Args:
            constraint:     The column's constraint.
                            A member of the Constraint enum, or None,
                            meaning no constraint.
        """
        assert constraint is None or isinstance(constraint, Constraint)
        super().__init__(
            "INT", constraint=constraint,
            unpack=lambda x: bool(x) if x is not None else None
        )


class TextColumn(Column):
    """A text column"""

    # Calm down, pylint: disable=redefined-builtin
    def __init__(self, constraint=None, pack=None, unpack=None):
        """
        Initialize the column description.

        Args:
            constraint:     The column's constraint.
                            A member of the Constraint enum, or None,
                            meaning no constraint.
            pack:           The function packing the JSON representation of
                            column's values into the SQLite representation.
            unpack:         The function unpacking the SQLite representation
                            of column's values into the JSON representation.
        """
        assert constraint is None or isinstance(constraint, Constraint)
        assert pack is None or callable(pack)
        assert unpack is None or callable(unpack)
        super().__init__("TEXT", constraint=constraint,
                         pack=pack, unpack=unpack)


class JSONColumn(TextColumn):
    """A JSON-encoded column"""

    def __init__(self, constraint=None):
        """
        Initialize the column description.

        Args:
            constraint:     The column's constraint.
                            A member of the Constraint enum, or None,
                            meaning no constraint.
        """
        assert constraint is None or isinstance(constraint, Constraint)

        super().__init__(
            constraint=constraint,
            pack=lambda x: json.dumps(x) if x is not None else None,
            unpack=lambda x: json.loads(x) if x is not None else None)


# A map of table names to CREATE TABLE statements
TABLES = dict(
    checkouts=dict(
        columns={
            "id": TextColumn(constraint=Constraint.PRIMARY_KEY),
            "origin": TextColumn(constraint=Constraint.NOT_NULL),
            "tree_name": TextColumn(),
            "git_repository_url": TextColumn(),
            "git_commit_hash": TextColumn(),
            "git_commit_name": TextColumn(),
            "git_repository_branch": TextColumn(),
            "patchset_files": JSONColumn(),
            "patchset_hash": TextColumn(),
            "message_id": TextColumn(),
            "comment": TextColumn(),
            "publishing_time": TextColumn(),
            "start_time": TextColumn(),
            "contacts": JSONColumn(),
            "log_url": TextColumn(),
            "log_excerpt": TextColumn(),
            "valid": BoolColumn(),
            "misc": JSONColumn(),
        }
    ),
    builds=dict(
        columns={
            "checkout_id": TextColumn(constraint=Constraint.NOT_NULL),
            "id": TextColumn(constraint=Constraint.PRIMARY_KEY),
            "origin": TextColumn(constraint=Constraint.NOT_NULL),
            "comment": TextColumn(),
            "start_time": TextColumn(),
            "duration": Column("REAL"),
            "architecture": TextColumn(),
            "command": TextColumn(),
            "compiler": TextColumn(),
            "input_files": JSONColumn(),
            "output_files": JSONColumn(),
            "config_name": TextColumn(),
            "config_url": TextColumn(),
            "log_url": TextColumn(),
            "log_excerpt": TextColumn(),
            "valid": BoolColumn(),
            "misc": JSONColumn(),
        },
    ),
    tests=dict(
        columns={
            "build_id": TextColumn(constraint=Constraint.NOT_NULL),
            "id": TextColumn(constraint=Constraint.PRIMARY_KEY),
            "origin": TextColumn(constraint=Constraint.NOT_NULL),
            "environment.id": TextColumn(),
            "environment.comment": TextColumn(),
            "environment.misc": JSONColumn(),
            "path": TextColumn(),
            "comment": TextColumn(),
            "status": TextColumn(),
            "waived": BoolColumn(),
            "start_time": TextColumn(),
            "duration": Column("REAL"),
            "output_files": JSONColumn(),
            "misc": JSONColumn()
        },
    ),
)

# Queries and their columns for each type of raw object-oriented data.
# Both should have columns in the same order.
# NOTE: Relying on dictionaries preserving order in Python 3.6+
OO_QUERIES = dict(
    revision=dict(
        statement="SELECT\n"
                  "   git_commit_hash,\n"
                  "   patchset_hash,\n"
                  "   patchset_files,\n"
                  "   git_commit_name,\n"
                  "   contacts\n"
                  "FROM checkouts\n"
                  "GROUP BY git_commit_hash, patchset_hash",
        columns=dict(
            git_commit_hash=TextColumn(),
            patchset_hash=TextColumn(),
            patchset_files=JSONColumn(),
            git_commit_name=TextColumn(),
            contacts=JSONColumn(),
        ),
    ),
    checkout=dict(
        statement="SELECT\n"
                  "   id,\n"
                  "   git_commit_hash,\n"
                  "   patchset_hash,\n"
                  "   origin,\n"
                  "   git_repository_url,\n"
                  "   git_repository_branch,\n"
                  "   tree_name,\n"
                  "   message_id,\n"
                  "   publishing_time,\n"
                  "   start_time,\n"
                  "   log_url,\n"
                  "   log_excerpt,\n"
                  "   comment,\n"
                  "   valid,\n"
                  "   misc\n"
                  "FROM checkouts\n"
                  "GROUP BY id",
        columns=dict(
            id=TextColumn(),
            git_commit_hash=TextColumn(),
            patchset_hash=TextColumn(),
            origin=TextColumn(),
            git_repository_url=TextColumn(),
            git_repository_branch=TextColumn(),
            tree_name=TextColumn(),
            message_id=TextColumn(),
            publishing_time=TextColumn(),
            start_time=TextColumn(),
            log_url=TextColumn(),
            log_excerpt=TextColumn(),
            comment=TextColumn(),
            valid=BoolColumn(),
            misc=JSONColumn(),
        ),
    ),
    build=dict(
        statement="SELECT\n"
                  "   id,\n"
                  "   checkout_id,\n"
                  "   origin,\n"
                  "   start_time,\n"
                  "   duration,\n"
                  "   architecture,\n"
                  "   command,\n"
                  "   compiler,\n"
                  "   input_files,\n"
                  "   output_files,\n"
                  "   config_name,\n"
                  "   config_url,\n"
                  "   log_url,\n"
                  "   log_excerpt,\n"
                  "   comment,\n"
                  "   valid,\n"
                  "   misc\n"
                  "FROM builds\n"
                  "GROUP BY id",
        columns=dict(
            id=TextColumn(),
            checkout_id=TextColumn(),
            origin=TextColumn(),
            start_time=TextColumn(),
            duration=Column("REAL"),
            architecture=TextColumn(),
            command=TextColumn(),
            compiler=TextColumn(),
            input_files=JSONColumn(),
            output_files=JSONColumn(),
            config_name=TextColumn(),
            config_url=TextColumn(),
            log_url=TextColumn(),
            log_excerpt=TextColumn(),
            comment=TextColumn(),
            valid=BoolColumn(),
            misc=JSONColumn(),
        ),
    ),
    test=dict(
        statement="SELECT\n"
                  "   id,\n"
                  "   build_id,\n"
                  "   origin,\n"
                  "   path,\n"
                  "   \"environment.comment\" AS environment_comment,\n"
                  "   \"environment.misc\" AS environment_misc,\n"
                  "   status,\n"
                  "   waived,\n"
                  "   start_time,\n"
                  "   duration,\n"
                  "   output_files,\n"
                  "   comment,\n"
                  "   misc\n"
                  "FROM tests\n"
                  "GROUP BY id",
        columns=dict(
            id=TextColumn(),
            build_id=TextColumn(),
            origin=TextColumn(),
            path=TextColumn(),
            environment_comment=TextColumn(),
            environment_misc=JSONColumn(),
            status=TextColumn(),
            waived=BoolColumn(),
            start_time=TextColumn(),
            duration=Column("REAL"),
            output_files=JSONColumn(),
            comment=TextColumn(),
            misc=JSONColumn(),
        ),
    ),
)
