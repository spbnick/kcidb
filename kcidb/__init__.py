"""Kernel CI reporting"""

import argparse
import decimal
import json
import sys
from datetime import datetime
import yaml
import requests
import jsonschema
from google.cloud import bigquery
from google.api_core.exceptions import BadRequest
from kcidb import db_schema
from kcidb import io_schema
from kcidb import tests_schema


class DBClient:
    """Kernel CI report database client"""

    def __init__(self, dataset_name):
        """
        Initialize a Kernel CI report database client.

        Args:
            dataset_name:   The name of the Kernel CI dataset. The dataset
                            should be located within the Google Cloud project
                            specified in the credentials file pointed to by
                            GOOGLE_APPLICATION_CREDENTIALS environment
                            variable.
        """
        assert isinstance(dataset_name, str)
        self.client = bigquery.Client()
        self.dataset_ref = self.client.dataset(dataset_name)

    def init(self):
        """
        Initialize the database. The database must be empty.
        """
        for table_name, table_schema in db_schema.TABLE_MAP.items():
            table_ref = self.dataset_ref.table(table_name)
            table = bigquery.table.Table(table_ref, schema=table_schema)
            self.client.create_table(table)

    def cleanup(self):
        """
        Cleanup (empty) the database, removing all data.
        """
        for table_name, _ in db_schema.TABLE_MAP.items():
            table_ref = self.dataset_ref.table(table_name)
            self.client.delete_table(table_ref)

    def query(self):
        """
        Query data from the database.

        Returns:
            The JSON data from the database adhering to the I/O schema
            (kcidb.io_schema.JSON).
        """
        def convert_node(node):
            """
            Convert a retrieved data node (and all its children) to
            the JSON-compatible and schema-complying representation.

            Args:
                node:   The node to convert.

            Returns:
                The converted node.
            """
            if isinstance(node, decimal.Decimal):
                node = float(node)
            elif isinstance(node, datetime):
                node = node.isoformat()
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    node[index] = convert_node(value)
            elif isinstance(node, dict):
                for key, value in list(node.items()):
                    if value is None:
                        del node[key]
                    elif key == "misc":
                        node[key] = json.loads(value)
                    else:
                        node[key] = convert_node(value)
            return node

        data = dict(version=dict(major=io_schema.JSON_VERSION_MAJOR,
                                 minor=io_schema.JSON_VERSION_MINOR))
        for obj_list_name in db_schema.TABLE_MAP:
            job_config = bigquery.job.QueryJobConfig(
                default_dataset=self.dataset_ref)
            query_job = self.client.query(
                f"SELECT * FROM `{obj_list_name}`", job_config=job_config)
            data[obj_list_name] = [
                convert_node(dict(row.items())) for row in query_job
            ]

        io_schema.validate(data)

        return data

    def load(self, data):
        """
        Load data into the database.

        Args:
            data:   The JSON data to load into the database.
                    Must adhere to the I/O schema (kcidb.io_schema.JSON).
        """
        def convert_node(node):
            """
            Convert a submitted data node (and all its children) to
            the BigQuery storage-compatible representation.

            Args:
                node:   The node to convert.

            Returns:
                The converted node.
            """
            if isinstance(node, list):
                node = node.copy()
                for index, value in enumerate(node):
                    node[index] = convert_node(value)
            elif isinstance(node, dict):
                node = node.copy()
                for key, value in list(node.items()):
                    # Flatten the "misc" fields
                    if key == "misc":
                        node[key] = json.dumps(value)
                    else:
                        node[key] = convert_node(value)
            return node

        io_schema.validate(data)
        for obj_list_name in db_schema.TABLE_MAP:
            if obj_list_name in data:
                obj_list = convert_node(data[obj_list_name])
                job_config = bigquery.job.LoadJobConfig(
                    autodetect=False,
                    schema=db_schema.TABLE_MAP[obj_list_name])
                job = self.client.load_table_from_json(
                    obj_list,
                    self.dataset_ref.table(obj_list_name),
                    job_config=job_config)
                try:
                    job.result()
                except BadRequest:
                    raise Exception("".join([
                        f"ERROR: {error['message']}\n" for error in job.errors
                    ]))


class Client:
    """Kernel CI reporting client"""

    def __init__(self, dataset_name):
        """
        Initialize a reporting client

        Args:
            dataset_name:   The name of the Kernel CI dataset. The dataset
                            should be located within the Google Cloud project
                            specified in the credentials file pointed to by
                            GOOGLE_APPLICATION_CREDENTIALS environment
                            variable.
        """
        self.db_client = DBClient(dataset_name)

    def submit(self, data):
        """
        Submit reports.

        Args:
            data:   The JSON report data to submit.
                    Must adhere to the I/O schema (kcidb.io_schema.JSON).
        """
        self.db_client.load(data)

    def query(self):
        """
        Query reports.

        Returns:
            The JSON report data adhering to the I/O schema
            (kcidb.io_schema.JSON).
        """
        self.db_client.query()


def submit_main():
    """Execute the kcidb-submit command-line tool"""
    description = \
        'kcidb-submit - Submit Kernel CI reports'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-d', '--dataset',
        help='Dataset name',
        required=True
    )
    args = parser.parse_args()
    data = json.load(sys.stdin)
    io_schema.validate(data)
    client = DBClient(args.dataset)
    client.load(data)


def query_main():
    """Execute the kcidb-query command-line tool"""
    description = \
        'kcidb-query - Query Kernel CI reports'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-d', '--dataset',
        help='Dataset name',
        required=True
    )
    args = parser.parse_args()
    client = DBClient(args.dataset)
    json.dump(client.query(), sys.stdout, indent=4, sort_keys=True)


def db_query_main():
    """Execute the kcidb-db-query command-line tool"""
    description = \
        'kcidb-db-query - Query reports from Kernel CI report database'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-d', '--dataset',
        help='Dataset name',
        required=True
    )
    args = parser.parse_args()
    client = DBClient(args.dataset)
    json.dump(client.query(), sys.stdout, indent=4, sort_keys=True)


def db_load_main():
    """Execute the kcidb-db-load command-line tool"""
    description = \
        'kcidb-db-load - Load reports into Kernel CI report database'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-d', '--dataset',
        help='Dataset name',
        required=True
    )
    args = parser.parse_args()
    data = json.load(sys.stdin)
    io_schema.validate(data)
    client = DBClient(args.dataset)
    client.load(data)


def db_init_main():
    """Execute the kcidb-db-init command-line tool"""
    description = 'kcidb-db-init - Initialize a Kernel CI report database'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-d', '--dataset',
        help='Dataset name',
        required=True
    )
    args = parser.parse_args()
    client = DBClient(args.dataset)
    client.init()


def db_cleanup_main():
    """Execute the kcidb-db-cleanup command-line tool"""
    description = 'kcidb-db-cleanup - Cleanup a Kernel CI report database'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-d', '--dataset',
        help='Dataset name',
        required=True
    )
    args = parser.parse_args()
    client = DBClient(args.dataset)
    client.cleanup()


def schema_main():
    """Execute the kcidb-schema command-line tool"""
    description = 'kcidb-schema - Output I/O JSON schema'
    parser = argparse.ArgumentParser(description=description)
    parser.parse_args()
    json.dump(io_schema.JSON, sys.stdout, indent=4, sort_keys=True)


def validate_main():
    """Execute the kcidb-validate command-line tool"""
    description = 'kcidb-validate - Validate I/O JSON data'
    parser = argparse.ArgumentParser(description=description)
    parser.parse_args()

    try:
        data = json.load(sys.stdin)
    except json.decoder.JSONDecodeError as err:
        print(err, file=sys.stderr)
        return 1

    try:
        io_schema.validate(data)
    except jsonschema.exceptions.ValidationError as err:
        print(err, file=sys.stderr)
        return 2
    return 0


def tests_validate_main():
    """Execute the kcidb-tests-validate command-line tool"""
    description = 'kcidb-tests-validate - Validate test catalog YAML'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-u", "--urls",
        action='store_true',
        help="Verify URLs in the catalog are accessible"
    )
    args = parser.parse_args()

    try:
        catalog = yaml.safe_load(sys.stdin)
    except yaml.YAMLError as err:
        print(err, file=sys.stderr)
        return 1

    try:
        tests_schema.validate(catalog)
    except jsonschema.exceptions.ValidationError as err:
        print(err, file=sys.stderr)
        return 2

    if args.urls:
        try:
            for test in catalog.values():
                requests.head(test['home']).raise_for_status()
        except requests.RequestException as err:
            print(err, file=sys.stderr)
            return 3

    return 0
