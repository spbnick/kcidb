"""I/O schema"""

import jsonschema

# Major version number of JSON schema.
# Increases represent backward-incompatible changes.
# E.g. deleting or renaming a property, changing a property type, restricting
# values, making a property required, or adding a new required property.
JSON_VERSION_MAJOR = 1

# Minor version number of JSON schema.
# Increases represent backward-compatible changes.
# E.g. relaxing value restrictions, making a property optional, or adding a
# new optional property.
JSON_VERSION_MINOR = 1

# JSON schema for a named remote resource
JSON_RESOURCE = {
    "title": "resource",
    "description": "A named remote resource",
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description":
                "Resource name. Must be usable as a local file name for the "
                "downloaded resource.",
        },
        "url": {
            "type": "string",
            "format": "uri",
            "description":
                "Resource URL. Must point to the resource file directly, "
                "so it could be downloaded automatically.",
        },
    },
    "additionalProperties": False,
    "required": [
        "name",
        "url",
    ],
    "examples": [
        {
            "name": "console.log",
            "url":
                "https://artifacts.cki-project.org/pipelines/223563/logs/"
                "aarch64_host_1_console.log"
        },
        {
            "name": "kernel.tar.gz",
            "url":
                "https://artifacts.cki-project.org/pipelines/224569/"
                "kernel-stable-aarch64-"
                "a2fc8ee6676067f27d2f5c6e4d512adff3d9938c.tar.gz"
        }
    ]
}

# JSON schema for a code revision
JSON_REVISION = {
    "title": "revision",
    "description":
        "A revision of the tested code.\n"
        "\n"
        "Represents a way the tested source code could be obtained. E.g. "
        "checking out a particular commit from a git repo, and applying a "
        "set of patches on top.",
    "type": "object",
    "properties": {
        "origin": {
            "type": "string",
            "description":
                "The name of the CI system which submitted the revision",
            "pattern": "^[a-z0-9_]*$"
        },
        "origin_id": {
            "type": "string",
            "description": "Origin-unique revision ID",
        },
        "git_repository_url": {
            "type": "string",
            "format": "uri",
            "description":
                "The URL of the Git repository which contains the base code "
                "of the revision. The shortest possible HTTPS URL.",
        },
        "git_repository_commit_hash": {
            "type": "string",
            "description":
                "The full commit hash of the revision's base code "
                "in the Git repository",
        },
        "git_repository_commit_name": {
            "type": "string",
            "description":
                "A human-readable name of the commit containing the base "
                "code of the revision, as would be output by "
                "\"git describe\", at the discovery time."
        },
        "git_repository_branch": {
            "type": "string",
            "description":
                "The Git repository branch in which the commit with the "
                "revision's base code was discovered."
        },
        "patch_mboxes": {
            "type": "array",
            "description":
                "List of mboxes containing patches applied "
                "to the base code of the revision, in order of application",
            "items": JSON_RESOURCE,
        },
        "message_id": {
            "type": "string",
            "format": "email",
            "description":
                "The value of the Message-ID header of the e-mail message "
                "introducing this code revision, if any. E.g. a message with "
                "the revision's patchset, or a release announcement sent to "
                "a maillist.",
        },
        "description": {
            "type": "string",
            "description":
                "Human-readable description of the revision. "
                "E.g. a release version, or the subject of a patchset message."
        },
        "publishing_time": {
            "type": "string",
            "format": "date-time",
            "description":
                "The time the revision was made public. E.g. the timestamp "
                "on a patch message, a commit, or a tag.",
        },
        "discovery_time": {
            "type": "string",
            "format": "date-time",
            "description":
                "The time the revision was discovered by the CI system. "
                "E.g. the time the CI system found a patch message, or "
                "noticed a new commit or a new tag in a git repo.",
        },
        "contacts": {
            "type": "array",
            "description":
                "List of e-mail addresses of contacts concerned with "
                "this revision, such as authors, reviewers, and mail lists",
            "items": {
                "type": "string",
                "description":
                    "An e-mail address of a contact concerned with this "
                    "revision, e.g. an author, a reviewer, or a mail list, "
                    "as in https://tools.ietf.org/html/rfc5322#section-3.4"
            },
        },
        "log_url": {
            "type": "string",
            "format": "uri",
            "description":
                "The URL of the log file of the attempt to construct this "
                "revision from its parts. E.g. 'git am' output.",
        },
        "valid": {
            "type": "boolean",
            "description":
                "True if the revision is valid, i.e. if its parts could be "
                "combined. False if not, e.g. if its patches failed to apply."
        },
        "misc": {
            "type": "object",
            "description":
                "Miscellaneous extra data about the revision",
        },
    },
    "additionalProperties": False,
    "required": [
        "origin",
        "origin_id",
    ],
}

# JSON schema for a build of a revision
JSON_BUILD = {
    "title": "build",
    "description": "A build of a revision",
    "type": "object",
    "properties": {
        "revision_origin": {
            "type": "string",
            "description":
                "The name of the CI system which submitted the built revision",
            "pattern": "^[a-z0-9_]*$"
        },
        "revision_origin_id": {
            "type": "string",
            "description":
                "Origin-unique ID of the built revision. The revision must "
                "be valid for the build to be considered valid.",
        },
        "origin": {
            "type": "string",
            "description":
                "The name of the CI system which submitted the build",
            "pattern": "^[a-z0-9_]*$"
        },
        "origin_id": {
            "type": "string",
            "description": "Origin-unique build ID",
        },
        "description": {
            "type": "string",
            "description":
                "Human-readable description of the build"
        },
        "start_time": {
            "type": "string",
            "format": "date-time",
            "description":
                "The time the build was started",
        },
        "duration": {
            "type": "number",
            "description":
                "The number of seconds it took to complete the build",
        },
        "architecture": {
            "type": "string",
            "description":
                "Target architecture of the build",
            "pattern": "^[a-z0-9_]*$"
        },
        "command": {
            "type": "string",
            "description":
                "Full shell command line used to make the build, "
                "including environment variables",
        },
        "compiler": {
            "type": "string",
            "description":
                "Name and version of the compiler used to make the build",
        },
        "input_files": {
            "type": "array",
            "description":
                "A list of build input files. E.g. configuration.",
            "items": JSON_RESOURCE,
        },
        "output_files": {
            "type": "array",
            "description":
                "A list of build output files: images, packages, etc.",
            "items": JSON_RESOURCE,
        },
        "config_name": {
            "type": "string",
            "description":
                "A name describing the build configuration options.",
        },
        "config_url": {
            "type": "string",
            "format": "uri",
            "description":
                "The URL of the build configuration file.",
        },
        "log_url": {
            "type": "string",
            "format": "uri",
            "description":
                "The URL of the build log file.",
        },
        "valid": {
            "type": "boolean",
            "description":
                "True if the build is valid, i.e. if it could be completed. "
                "False if not.",
        },
        "misc": {
            "type": "object",
            "description":
                "Miscellaneous extra data about the build",
        },
    },
    "additionalProperties": False,
    "required": [
        "revision_origin",
        "revision_origin_id",
        "origin",
        "origin_id",
    ],
}

# JSON schema for a test run on a build
JSON_TEST = {
    "title": "test",
    "description":
        "A test run against a build.\n"
        "\n"
        "Could represent a result of execution of a test suite program, a "
        "result of one of the tests done by the test suite program, as well "
        "as a summary of a collection of test suite results.\n"
        "\n"
        "Each test run should normally have a dot-separated test \"path\" "
        "specified in the \"path\" property, which could identify a specific "
        "test within a test suite (e.g. \"LTPlite.sem01\"), a whole test "
        "suite (e.g. \"LTPlite\"), or the summary of all tests for a build "
        "("" - the empty string).",
    "type": "object",
    "properties": {
        "build_origin": {
            "type": "string",
            "description":
                "The name of the CI system which submitted the tested build",
            "pattern": "^[a-z0-9_]*$"
        },
        "build_origin_id": {
            "type": "string",
            "description":
                "Origin-unique ID of the tested build. The build must be "
                "valid for the test run to be considered valid.",
        },
        "origin": {
            "type": "string",
            "description":
                "The name of the CI system which submitted the test run",
            "pattern": "^[a-z0-9_]*$"
        },
        "origin_id": {
            "type": "string",
            "description": "Origin-unique ID of the test run",
        },
        "environment": {
            "type": "object",
            "description":
                "The environment the test ran in. "
                "E.g. a host, a set of hosts, or a lab; "
                "amount of memory/storage/CPUs, for each host; "
                "process environment variables, etc.",
            "properties": {
                "description": {
                    "type": "string",
                    "description":
                        "Human-readable description of the environment"
                },
                "misc": {
                    "type": "object",
                    "description":
                        "Miscellaneous extra data about the environment",
                },
            },
            "additionalProperties": False,
        },
        "path": {
            "type": "string",
            "description":
                "Dot-separated path to the node in the test classification "
                "tree the executed test belongs to. E.g. \"LTPlite.sem01\". "
                "The empty string signifies the root of the tree, i.e. all "
                "tests for the build, executed by the origin CI system.",
            "pattern": "^[.a-zA-Z0-9_-]*$"
        },
        "description": {
            "type": "string",
            "description":
                "Human-readable description of the test run"
        },
        "status": {
            "type": "string",
            "description":
                "The test status, one of the following. "
                "\"ERROR\" - the test is faulty, "
                "the status of the tested code is unknown. "
                "\"FAIL\" - the test has failed, the tested code is faulty. "
                "\"PASS\" - the test has passed, the tested code is correct. "
                "\"DONE\" - the test has finished successfully, "
                "the status of the tested code is unknown. "
                "\"SKIP\" - the test wasn't executed, "
                "the status of the tested code is unknown.\n"
                "\n"
                "The status names above are listed in priority order "
                "(highest to lowest), which could be used for producing a "
                "summary status for a collection of test runs, e.g. for all "
                "testing done on a build, based on results of executed test "
                "suites. The summary status would be the highest priority "
                "status across all test runs in a collection.",
            "enum": ["ERROR", "FAIL", "PASS", "DONE", "SKIP"],
        },
        "waived": {
            "type": "boolean",
            "description":
                "True if the test status should be ignored.\n"
                "\n"
                "Could be used for reporting test results without affecting "
                "the overall test status and alerting the contacts concerned "
                "with the tested code revision. For example, for collecting "
                "test reliability statistics when the test is first "
                "introduced, or is being fixed.",
        },
        "start_time": {
            "type": "string",
            "format": "date-time",
            "description":
                "The time the test run was started",
        },
        "duration": {
            "type": "number",
            "description":
                "The number of seconds it took to run the test",
        },
        "output_files": {
            "type": "array",
            "description":
                "A list of test outputs: logs, dumps, etc.",
            "items": JSON_RESOURCE,
        },
        "misc": {
            "type": "object",
            "description":
                "Miscellaneous extra data about the test run",
        },
    },
    "additionalProperties": False,
    "required": [
        "build_origin",
        "build_origin_id",
        "origin",
        "origin_id",
    ],
}

# JSON schema for I/O data
JSON = {
    "title": "kcidb",
    "description":
        "Kernel CI report data. To be submitted to/queried from the common "
        "report database.\n"
        "\n"
        "Objects in the data are identified and linked together using two "
        "properties: \"origin\" and \"origin_id\". The former is a string "
        "identifying the CI system which submitted the object. The latter "
        "is a string generated by the origin CI system, identifying that "
        "object uniquely among all objects of the same type, coming from "
        "that CI system.\n"
        "\n"
        "Any of the immediate properties (except \"version\") can be missing "
        "or be an empty list with each submission/query, but only complete "
        "data stored in the database should be considered valid.\n"
        "\n"
        "E.g. a test run referring to a non-existent build is allowed "
        "into/from the database, but would only appear in reports once both "
        "the build and its revision are present.\n"
        "\n"
        "No special meaning apart from \"data is missing\" is attached to "
        "any immediate or deeper properties being omitted, when they're not "
        "required, and no default values should be assumed for them.\n"
        "\n"
        "Extra free-form data can be stored under \"misc\" fields associated "
        "with various objects throughout the schema, if necessary. That data "
        "could later be used as the basis for defining new properties to "
        "house it.",
    "type": "object",
    "properties": {
        "version": {
            "oneOf": [
                {
                    "type": "string",
                    "description":
                        "Version of the schema the data complies to.\n"
                        "\n"
                        "Must be a string representing two unsigned integer "
                        "numbers: major and minor, separated by a dot. If "
                        "both the dot and the minor number are omitted, the "
                        "minor number is assumed to be zero.\n"
                        "\n"
                        "Increases in major version number represent changes "
                        "which are not backward-compatible, such as renaming "
                        "a property, or changing a type of property, which "
                        "existing software versions cannot handle.\n"
                        "\n"
                        "Increases in minor version number represent changes "
                        "which are backward-compatible, such as relaxing "
                        "value restrictions, or making a property optional.",
                    "pattern": "^1(\\.0)?$"
                },
                {
                    "type": "object",
                    "properties": {
                        "major": {
                            "type": "integer",
                            "const": JSON_VERSION_MAJOR,
                            "description":
                                "Major number of the schema version.\n"
                                "\n"
                                "Increases represent backward-incompatible "
                                "changes. E.g. deleting or renaming a "
                                "property, changing a property type, "
                                "restricting values, making a property "
                                "required, or adding a new required "
                                "property.",
                        },
                        "minor": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": JSON_VERSION_MINOR,
                            "description":
                                "Minor number of the schema version.\n"
                                "\n"
                                "Increases represent backward-compatible "
                                "changes. E.g. relaxing value restrictions, "
                                "making a property optional, or adding a new "
                                "optional property.",
                        }
                    },
                    "additionalProperties": False,
                    "required": [
                        "major",
                    ],
                },
            ],
        },
        "revisions": {
            "description": "List of code revisions",
            "type": "array",
            "items": JSON_REVISION,
        },
        "builds": {
            "description": "List of builds",
            "type": "array",
            "items": JSON_BUILD,
        },
        "tests": {
            "description": "List of test runs",
            "type": "array",
            "items": JSON_TEST,
        },
    },
    "additionalProperties": False,
    "required": [
        "version",
    ]
}


def validate(io_data):
    """
    Validate I/O data with its schema.

    Args:
        io_data:    The I/O data to validate.

    Return:
        The validated I/O data.

    Raises:
        `jsonschema.exceptions.ValidationError` if the instance
            is invalid
    """
    jsonschema.validate(instance=io_data, schema=JSON)
    return io_data
