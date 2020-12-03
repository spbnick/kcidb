"""
Kernel CI report database schema.

Always corresponds to the latest I/O schema.
"""
from google.cloud.bigquery.schema import SchemaField as Field

# Resource record fields
RESOURCE_FIELDS = (
    Field("name", "STRING", description="Resource name"),
    Field("url", "STRING", description="Resource URL"),
)

# Test environment fields
ENVIRONMENT_FIELDS = (
    Field(
        "comment", "STRING",
        description="A human-readable comment regarding the environment."
    ),
    Field(
        "misc", "STRING",
        description="Miscellaneous extra data about the environment "
                    "in JSON format",
    ),
)

# A map of table names to their BigQuery schemas
TABLE_MAP = dict(
    checkouts=[
        Field(
            "id", "STRING",
            description="Source code checkout ID",
        ),
        Field(
            "origin", "STRING",
            description="The name of the CI system which submitted "
                        "the checkout",
        ),
        Field(
            "tree_name", "STRING",
            description="The widely-recognized name of the sub-tree (fork) "
                        "of the main code tree where the checked out base "
                        "source code came from.",
        ),
        Field(
            "git_repository_url", "STRING",
            description="The URL of the Git repository which contains the "
                        "checked out base source code. The shortest "
                        "possible https:// URL, or, if that's not available, "
                        "the shortest possible git:// URL.",
        ),
        Field(
            "git_commit_hash", "STRING",
            description="The full commit hash of the checked out base source "
                        "code",
        ),
        Field(
            "git_commit_name", "STRING",
            description="A human-readable name of the commit containing the "
                        "checked out base source code, as would be output by "
                        "\"git describe\", at the checkout time."
        ),
        Field(
            "git_repository_branch", "STRING",
            description="The Git repository branch from which the commit "
                        "with the base source code was checked out."
        ),
        Field(
            "patchset_files", "RECORD", mode="REPEATED",
            fields=RESOURCE_FIELDS,
            description="List of patch files representing the patchset "
                        "applied to the checked out base source code, "
                        "in order of application. "
                        "Each linked file must be in a format accepted by "
                        "\"git apply\".",
        ),
        Field(
            "patchset_hash", "STRING",
            description="The patchset hash.\n"
                        "\n"
                        "A sha256 hash over newline-terminated sha256 hashes "
                        "of each patch from the patchset, in order. E.g. "
                        "generated with this shell command: \""
                        "sha256sum *.patch | cut -c-64 | sha256sum | "
                        "cut -c-64\".\n"
                        "\n"
                        "An empty string, if no patches were applied to the "
                        "checked out base source code.\n",
        ),
        Field(
            "message_id", "STRING",
            description="The value of the Message-ID header of the e-mail "
                        "message introducing the checked-out source code, "
                        "if any. E.g. a message with the applied patchset, "
                        "or a release announcement sent to a maillist.",
        ),
        Field(
            "comment", "STRING",
            description="A human-readable comment regarding the checkout. "
                        "E.g. the checked out release version, or the "
                        "subject of the message with the applied patchset."
        ),
        Field(
            "publishing_time", "TIMESTAMP",
            description="The time the checked out source code was made "
                        "public. E.g. the timestamp on a patch message, "
                        "a commit, or a tag.",
        ),
        Field(
            "start_time", "TIMESTAMP",
            description="The time the checkout was started.",
        ),
        Field(
            "contacts", "STRING", mode="REPEATED",
            description="List of e-mail addresses of contacts concerned with "
                        "the checked out source code, such as authors, "
                        "reviewers, and mail lists",
        ),
        Field(
            "log_url", "STRING",
            description="The URL of the log file of the checkout attempt. "
                        "E.g. 'git am' output.",
        ),
        Field(
            "log_excerpt", "STRING",
            description="A part of the log file of the checkout attempt most "
                        "relevant to its outcome.",
        ),
        Field(
            "valid", "BOOL",
            description="True if the checkout succeeded, i.e. if the source "
                        "code parts could be combined. False if not, e.g. if "
                        "the patches failed to apply.",
        ),
        Field(
            "misc", "STRING",
            description="Miscellaneous extra data about the checkout "
                        "in JSON format",
        ),
    ],
    builds=[
        Field(
            "checkout_id", "STRING",
            description="ID of the built source code checkout.",
        ),
        Field(
            "id", "STRING",
            description="Build ID",
        ),
        Field(
            "origin", "STRING",
            description="The name of the CI system which submitted "
                        "the build",
        ),
        Field(
            "comment", "STRING",
            description="A human-readable comment regarding the build"
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
            "log_excerpt", "STRING",
            description="A part of the log file of the build most relevant "
                        "to its outcome.",
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
            "build_id", "STRING",
            description="ID of the tested build",
        ),
        Field(
            "id", "STRING",
            description="Test run ID",
        ),
        Field(
            "origin", "STRING",
            description="The name of the CI system which submitted "
                        "the test run",
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
            "comment", "STRING",
            description="A human-readable comment regarding the test run"
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

# Queries for each type of raw object-oriented data
OO_QUERIES = dict(
    revision="SELECT\n"
             "   git_commit_hash,\n"
             "   patchset_hash,\n"
             "   ANY_VALUE(patchset_files) AS patchset_files,\n"
             "   ANY_VALUE(git_commit_name) AS git_commit_name,\n"
             "   ANY_VALUE(contacts) AS contacts\n"
             "FROM checkouts\n"
             "GROUP BY git_commit_hash, patchset_hash",
    checkout="SELECT\n"
             "   id,\n"
             "   ANY_VALUE(git_commit_hash) AS git_commit_hash,\n"
             "   ANY_VALUE(patchset_hash) AS patchset_hash,\n"
             "   ANY_VALUE(origin) AS origin,\n"
             "   ANY_VALUE(git_repository_url) AS "
             "git_repository_url,\n"
             "   ANY_VALUE(git_repository_branch) AS "
             "git_repository_branch,\n"
             "   ANY_VALUE(tree_name) AS tree_name,\n"
             "   ANY_VALUE(message_id) AS message_id,\n"
             "   ANY_VALUE(publishing_time) AS publishing_time,\n"
             "   ANY_VALUE(start_time) AS start_time,\n"
             "   ANY_VALUE(log_url) AS log_url,\n"
             "   ANY_VALUE(log_excerpt) AS log_excerpt,\n"
             "   ANY_VALUE(comment) AS comment,\n"
             "   ANY_VALUE(valid) AS valid,\n"
             "   ANY_VALUE(misc) AS misc\n"
             "FROM checkouts\n"
             "GROUP BY id",
    build="SELECT\n"
          "   id,\n"
          "   ANY_VALUE(checkout_id) AS checkout_id,\n"
          "   ANY_VALUE(origin) AS origin,\n"
          "   ANY_VALUE(start_time) AS start_time,\n"
          "   ANY_VALUE(duration) AS duration,\n"
          "   ANY_VALUE(architecture) AS architecture,\n"
          "   ANY_VALUE(command) AS command,\n"
          "   ANY_VALUE(compiler) AS compiler,\n"
          "   ANY_VALUE(input_files) AS input_files,\n"
          "   ANY_VALUE(output_files) AS output_files,\n"
          "   ANY_VALUE(config_name) AS config_name,\n"
          "   ANY_VALUE(config_url) AS config_url,\n"
          "   ANY_VALUE(log_url) AS log_url,\n"
          "   ANY_VALUE(log_excerpt) AS log_excerpt,\n"
          "   ANY_VALUE(comment) AS comment,\n"
          "   ANY_VALUE(valid) AS valid,\n"
          "   ANY_VALUE(misc) AS misc\n"
          "FROM builds\n"
          "GROUP BY id",
    test="SELECT\n"
         "   id,\n"
         "   ANY_VALUE(build_id) AS build_id,\n"
         "   ANY_VALUE(origin) AS origin,\n"
         "   ANY_VALUE(path) AS path,\n"
         "   ANY_VALUE(environment.comment) AS environment_comment,\n"
         "   ANY_VALUE(environment.misc) AS environment_misc,\n"
         "   ANY_VALUE(status) AS status,\n"
         "   ANY_VALUE(waived) AS waived,\n"
         "   ANY_VALUE(start_time) AS start_time,\n"
         "   ANY_VALUE(duration) AS duration,\n"
         "   ANY_VALUE(output_files) AS output_files,\n"
         "   ANY_VALUE(comment) AS comment,\n"
         "   ANY_VALUE(misc) AS misc\n"
         "FROM tests\n"
         "GROUP BY id",
)
