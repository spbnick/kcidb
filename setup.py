#!/usr/bin/env python3
# Copyright (c) 2018 Red Hat, Inc. All rights reserved. This copyrighted
# material is made available to anyone wishing to use, modify, copy, or
# redistribute it subject to the terms and conditions of the GNU General
# Public License v.2 or later.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
"""Install kcidb using setuptools."""
import setuptools

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name="kcidb",
    version="9",
    python_requires=">=3.6",
    author="kernelci.org",
    author_email="kernelci@groups.io",
    description="KCIDB = Linux Kernel CI reporting tools",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/kernelci/kcidb",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 1 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GPLv2+",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Topic :: Database :: Front-Ends",
    ],
    # Must match requirements.txt.
    # Let's make that easier, pylint: disable=line-too-long
    install_requires=[
        "google-cloud-bigquery",
        "google-cloud-pubsub<2.0.0dev",
        "google-cloud-firestore",
        "google-cloud-secret-manager<2.0.0dev",
        "jsonschema[format]",
        "requests",
        "pyyaml",
        "jinja2",
        "python-dateutil",
        "jq@git+https://github.com/spbnick/jq.py.git@1.1.2.post1",
        "kcidb-io@git+https://github.com/kernelci/kcidb-io.git@8190c1f5bee4140bc91cd1432191ca8d2acb9107",  # noqa: E501
    ],
    extras_require=dict(
        dev=[
            "flake8",
            "pylint",
            "yamllint",
            "pytest",
        ],
    ),
    entry_points=dict(
        console_scripts=[
            "kcidb-schema = kcidb:schema_main",
            "kcidb-validate = kcidb:validate_main",
            "kcidb-upgrade = kcidb:upgrade_main",
            "kcidb-count = kcidb:count_main",
            "kcidb-merge = kcidb:merge_main",
            "kcidb-submit = kcidb:submit_main",
            "kcidb-query = kcidb:query_main",
            "kcidb-summarize = kcidb:summarize_main",
            "kcidb-describe = kcidb:describe_main",
            "kcidb-notify = kcidb:notify_main",
            "kcidb-db-init = kcidb.db:init_main",
            "kcidb-db-cleanup = kcidb.db:cleanup_main",
            "kcidb-db-load = kcidb.db:load_main",
            "kcidb-db-dump = kcidb.db:dump_main",
            "kcidb-db-query = kcidb.db:query_main",
            "kcidb-db-oo-query = kcidb.db:oo_query_main",
            "kcidb-db-oo-query-help = kcidb.db:oo_query_help_main",
            "kcidb-db-complement = kcidb.db:complement_main",
            "kcidb-mq-publisher-init = kcidb.mq:publisher_init_main",
            "kcidb-mq-publisher-cleanup = kcidb.mq:publisher_cleanup_main",
            "kcidb-mq-publisher-publish = kcidb.mq:publisher_publish_main",
            "kcidb-mq-subscriber-init = kcidb.mq:subscriber_init_main",
            "kcidb-mq-subscriber-cleanup = kcidb.mq:subscriber_cleanup_main",
            "kcidb-mq-subscriber-pull = kcidb.mq:subscriber_pull_main",
            "kcidb-tests-validate = kcidb.tests:validate_main",
            "kcidb-monitor-spool-wipe = kcidb.monitor.spool:wipe_main",
        ]
    ),
    package_data={
        "": ["*.j2"],
    },
)
