"""Database schema"""
from google.cloud.bigquery.schema import SchemaField as Field

# Resource record fields
RESOURCE_FIELDS = (
    Field("name", "STRING", description="Resource name"),
    Field("url", "STRING", description="Resource URL"),
)

# Test environment fields
ENVIRONMENT_FIELDS = (
    Field(
        "description", "STRING",
        description="Human-readable description of the environment",
    ),
    Field(
        "misc", "STRING",
        description="Miscellaneous extra data about the environment "
                    "in JSON format",
    ),
)

# A map of table names to "child" table names
# Empty "table" has top tables as children.
TABLE_CHILDREN_MAP = {
    "": ["revisions"],
    "revisions": ["builds"],
    "builds": ["tests"],
    "tests": []
}

# A map of table names to their BigQuery schemas
TABLE_MAP = dict(
    revisions=[
        Field(
            "origin", "STRING",
            description="The name of the CI system which submitted "
                        "the revision",
        ),
        Field(
            "origin_id", "STRING",
            description="Origin-unique revision ID",
        ),
        Field(
            "git_repository_url", "STRING",
            description="The URL of the Git repository which contains "
                        "the base code of the revision. The shortest "
                        "possible HTTPS URL.",
        ),
        Field(
            "git_repository_commit_hash", "STRING",
            description="The full commit hash of the revision's base code "
                        "in the Git repository",
        ),
        Field(
            "git_repository_commit_name", "STRING",
            description="A human-readable name of the commit containing the "
                        "base code of the revision, as would be output by "
                        "\"git describe\", at the discovery time."
        ),
        Field(
            "git_repository_branch", "STRING",
            description="The Git repository branch in which the commit with "
                        "the revision's base code was discovered."
        ),
        Field(
            "patch_mboxes", "RECORD", mode="REPEATED", fields=RESOURCE_FIELDS,
            description="List of mboxes containing patches applied "
                        "to the base code of the revision, in order of "
                        "application",
        ),
        Field(
            "message_id", "STRING",
            description="The value of the Message-ID header of the e-mail "
                        "message introducing this code revision, if any. "
                        "E.g. a message with the revision's patchset, or "
                        "a release announcement sent to a maillist.",
        ),
        Field(
            "description", "STRING",
            description="Human-readable description of the revision. "
                        "E.g. a release version, or the subject of a "
                        "patchset message.",
        ),
        Field(
            "publishing_time", "TIMESTAMP",
            description="The time the revision was made public",
        ),
        Field(
            "discovery_time", "TIMESTAMP",
            description="The time the revision was discovered by "
                        "the CI system",
        ),
        Field(
            "contacts", "STRING", mode="REPEATED",
            description="List of e-mail addresses of contacts concerned with "
                        "this revision, such as authors, reviewers, and mail "
                        "lists",
        ),
        Field(
            "log_url", "STRING",
            description="The URL of the log file of the attempt to construct "
                        "this revision from its parts. E.g. 'git am' output.",
        ),
        Field(
            "valid", "BOOL",
            description="True if the revision is valid, i.e. if its parts "
                        "could be combined. False if not, e.g. if its "
                        "patches failed to apply.",
        ),
        Field(
            "misc", "STRING",
            description="Miscellaneous extra data about the revision "
                        "in JSON format",
        ),
    ],
    builds=[
        Field(
            "revision_origin", "STRING",
            description="The name of the CI system which submitted "
                        "the revision",
        ),
        Field(
            "revision_origin_id", "STRING",
            description="Origin-unique revision ID",
        ),
        Field(
            "origin", "STRING",
            description="The name of the CI system which submitted "
                        "the build",
        ),
        Field(
            "origin_id", "STRING",
            description="Origin-unique build ID",
        ),
        Field(
            "description", "STRING",
            description="Human-readable description of the build",
        ),
        Field(
            "start_time", "TIMESTAMP",
            description="The time the build was started",
        ),
        Field(
            "duration", "NUMERIC",
            description="The number of seconds it took to complete the build",
        ),
        Field(
            "architecture", "STRING",
            description="Target architecture of the build",
        ),
        Field(
            "command", "STRING",
            description="Full shell command line used to make the build, "
                        "including environment variables",
        ),
        Field(
            "compiler", "STRING",
            description="Name and version of the compiler used to make the "
                        "build",
        ),
        Field(
            "input_files", "RECORD", mode="REPEATED", fields=RESOURCE_FIELDS,
            description="A list of build input files. E.g. configuration.",
        ),
        Field(
            "output_files", "RECORD", mode="REPEATED", fields=RESOURCE_FIELDS,
            description="A list of build output files: images, packages, etc.",
        ),
        Field(
            "config_name", "STRING",
            description="A name describing the build configuration options.",
        ),
        Field(
            "config_url", "STRING",
            description="The URL of the build configuration file.",
        ),
        Field(
            "log_url", "STRING",
            description="The URL of the build log file.",
        ),
        Field(
            "valid", "BOOL",
            description="True if the build is valid, i.e. if it could be "
                        "completed. False if not.",
        ),
        Field(
            "misc", "STRING",
            description="Miscellaneous extra data about the build "
                        "in JSON format",
        ),
    ],
    tests=[
        Field(
            "build_origin", "STRING",
            description="The name of the CI system which submitted "
                        "the tested build",
        ),
        Field(
            "build_origin_id", "STRING",
            description="Origin-unique ID of the tested build",
        ),
        Field(
            "origin", "STRING",
            description="The name of the CI system which submitted "
                        "the test run",
        ),
        Field(
            "origin_id", "STRING",
            description="Origin-unique test run ID",
        ),
        Field(
            "environment", "RECORD", fields=ENVIRONMENT_FIELDS,
            description="The environment the test ran in. "
                        "E.g. a host, a set of hosts, or a lab; "
                        "amount of memory/storage/CPUs, for each host; "
                        "process environment variables, etc.",
        ),
        Field(
            "path", "STRING",
            description="Dot-separated path to the node in the test "
                        "classification tree the executed test belongs to. "
                        "E.g. \"LTPlite.sem01\". The empty string, or the "
                        "absence of the property signify the root of the "
                        "tree, i.e. an abstract test.",
        ),
        Field(
            "description", "STRING",
            description="Human-readable description of the test run",
        ),
        Field(
            "status", "STRING",
            description="The test status, one of the following. "
                        "\"ERROR\" - the test is faulty, "
                        "the status of the tested code is unknown. "
                        "\"FAIL\" - the test has failed, the tested code is "
                        "faulty. "
                        "\"PASS\" - the test has passed, the tested code is "
                        "correct. "
                        "\"DONE\" - the test has finished successfully, "
                        "the status of the tested code is unknown. "
                        "\"SKIP\" - the test wasn't executed, "
                        "the status of the tested code is unknown. "
        ),
        Field(
            "waived", "BOOL",
            description="True if the test status should be ignored",
        ),
        Field(
            "start_time", "TIMESTAMP",
            description="The time the test run was started",
        ),
        Field(
            "duration", "NUMERIC",
            description="The number of seconds it took to run the test",
        ),
        Field(
            "output_files", "RECORD", mode="REPEATED", fields=RESOURCE_FIELDS,
            description="A list of test outputs: logs, dumps, etc.",
        ),
        Field(
            "misc", "STRING",
            description="Miscellaneous extra data about the test run "
                        "in JSON format",
        ),
    ]
)
