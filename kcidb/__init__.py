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
from google.cloud import pubsub
from google.api_core.exceptions import BadRequest
from google.api_core.exceptions import DeadlineExceeded
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

    @staticmethod
    def _unpack_node(node):
        """
        Unpack a retrieved data node (and all its children) to
        the JSON-compatible and schema-complying representation.

        Args:
            node:   The node to unpack.

        Returns:
            The unpacked node.
        """
        if isinstance(node, decimal.Decimal):
            node = float(node)
        elif isinstance(node, datetime):
            node = node.isoformat()
        elif isinstance(node, list):
            for index, value in enumerate(node):
                node[index] = DBClient._unpack_node(value)
        elif isinstance(node, dict):
            for key, value in list(node.items()):
                if value is None:
                    del node[key]
                elif key == "misc":
                    node[key] = json.loads(value)
                else:
                    node[key] = DBClient._unpack_node(value)
        return node

    def query(self):
        """
        Query data from the database.

        Returns:
            The JSON data from the database adhering to the I/O schema
            (kcidb.io_schema.JSON).
        """

        data = dict(version=dict(major=io_schema.JSON_VERSION_MAJOR,
                                 minor=io_schema.JSON_VERSION_MINOR))
        for obj_list_name in db_schema.TABLE_MAP:
            job_config = bigquery.job.QueryJobConfig(
                default_dataset=self.dataset_ref)
            query_job = self.client.query(
                f"SELECT * FROM `{obj_list_name}`", job_config=job_config)
            data[obj_list_name] = [
                DBClient._unpack_node(dict(row.items())) for row in query_job
            ]

        io_schema.validate(data)

        return data

    @staticmethod
    def _pack_node(node):
        """
        Pack a loaded data node (and all its children) to
        the BigQuery storage-compatible representation.

        Args:
            node:   The node to pack.

        Returns:
            The packed node.
        """
        if isinstance(node, list):
            node = node.copy()
            for index, value in enumerate(node):
                node[index] = DBClient._pack_node(value)
        elif isinstance(node, dict):
            node = node.copy()
            for key, value in list(node.items()):
                # Flatten the "misc" fields
                if key == "misc":
                    node[key] = json.dumps(value)
                else:
                    node[key] = DBClient._pack_node(value)
        return node

    def load(self, data):
        """
        Load data into the database.

        Args:
            data:   The JSON data to load into the database.
                    Must adhere to the I/O schema (kcidb.io_schema.JSON).
        """
        io_schema.validate(data)
        for obj_list_name in db_schema.TABLE_MAP:
            if obj_list_name in data:
                obj_list = DBClient._pack_node(data[obj_list_name])
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


class MQPublisher:
    """Kernel CI message queue publisher"""
    # pylint: disable=no-member

    @staticmethod
    def encode_data(io_data):
        """
        Encode JSON data adhering to the I/O schema (kcidb.io_schema.JSON)
        into message data.

        Args:
            io_data:    JSON data adhering to the I/O schema
                        (kcidb.io_schema.JSON) to be encoded.

        Returns
            The encoded message data.
        """
        io_schema.validate(io_data)
        return json.dumps(io_data).encode("utf-8")

    def __init__(self, project_id, topic_name):
        """
        Initialize a Kernel CI message queue publisher.

        Args:
            project_id:         ID of the Google Cloud project to which the
                                message queue belongs.
            topic_name:         Name of the message queue topic to publish to.
        """
        self.client = pubsub.PublisherClient()
        self.topic_path = self.client.topic_path(project_id, topic_name)

    def init(self):
        """
        Initialize publishing setup.
        """
        self.client.create_topic(self.topic_path)

    def cleanup(self):
        """
        Cleanup publishing setup.
        """
        self.client.delete_topic(self.topic_path)

    def publish(self, data):
        """
        Publish data to the message queue.

        Args:
            data:   The JSON data to publish to the message queue.
                    Must adhere to the I/O schema (kcidb.io_schema.JSON).
        """
        io_schema.validate(data)
        self.client.publish(self.topic_path, MQPublisher.encode_data(data))


class MQSubscriber:
    """Kernel CI message queue subscriber"""
    # pylint: disable=no-member

    @staticmethod
    def decode_data(message_data):
        """
        Decode message data to extract the JSON data adhering to the I/O
        schema (kcidb.io_schema.JSON).

        Args:
            message_data:   The message data from the message queue
                            ("data" field of pubsub.types.PubsubMessage) to be
                            decoded.

        Returns
            The decoded JSON data adhering to the I/O schema
            (kcidb.io_schema.JSON).
        """
        return io_schema.validate(json.loads(message_data.decode("utf-8")))

    def __init__(self, project_id, topic_name, subscription_name):
        """
        Initialize a Kernel CI message queue subscriber.

        Args:
            project_id:         ID of the Google Cloud project to which the
                                message queue belongs.
            topic_name:         Name of the message queue topic to subscribe
                                to.
            subscription_name:  Name of the subscription to use.
        """
        self.client = pubsub.SubscriberClient()
        self.subscription_path = \
            self.client.subscription_path(project_id, subscription_name)
        self.topic_path = self.client.topic_path(project_id, topic_name)

    def init(self):
        """
        Initialize subscription setup.
        """
        self.client.create_subscription(self.subscription_path,
                                        self.topic_path)

    def cleanup(self):
        """
        Cleanup subscription setup.
        """
        self.client.delete_subscription(self.subscription_path)

    def pull(self):
        """
        Pull published data from the message queue.

        Returns:
            Two values:
            * The ID to use when acknowledging the reception of the data.
            * The JSON data from the message queue, adhering to the I/O schema
              (kcidb.io_schema.JSON).
        """
        while True:
            try:
                # Setting *some* timeout, because infinite timeout doesn't
                # seem to be supported
                response = self.client.pull(self.subscription_path, 1,
                                            timeout=300)
                if response.received_messages:
                    break
            except DeadlineExceeded:
                pass
        message = response.received_messages[0]
        data = MQSubscriber.decode_data(message.message.data)
        return message.ack_id, io_schema.validate(data)

    def ack(self, ack_id):
        """
        Acknowledge reception of data.

        Args:
            ack_id: The ID received with the data to be acknowledged.
        """
        self.client.acknowledge(self.subscription_path, [ack_id])


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


def publisher_init_main():
    """Execute the kcidb-publisher-init command-line tool"""
    description = \
        'kcidb-publisher-init - Initialize a Kernel CI report publisher'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-p', '--project',
        help='ID of the Google Cloud project with the message queue',
        required=True
    )
    parser.add_argument(
        '-t', '--topic',
        help='Name of the message queue topic to create',
        required=True
    )
    args = parser.parse_args()
    publisher = MQPublisher(args.project, args.topic)
    publisher.init()


def publisher_cleanup_main():
    """Execute the kcidb-publisher-cleanup command-line tool"""
    description = \
        'kcidb-publisher-cleanup - Cleanup a Kernel CI report publisher'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-p', '--project',
        help='ID of the Google Cloud project with the message queue',
        required=True
    )
    parser.add_argument(
        '-t', '--topic',
        help='Name of the message queue topic to remove',
        required=True
    )
    args = parser.parse_args()
    publisher = MQPublisher(args.project, args.topic)
    publisher.cleanup()


def publisher_publish_main():
    """Execute the kcidb-publisher-publish command-line tool"""
    description = \
        'kcidb-publisher-publish - Publish with a Kernel CI report publisher'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-p', '--project',
        help='ID of the Google Cloud project with the message queue',
        required=True
    )
    parser.add_argument(
        '-t', '--topic',
        help='Name of the message queue topic to publish to',
        required=True
    )
    args = parser.parse_args()
    data = json.load(sys.stdin)
    io_schema.validate(data)
    publisher = MQPublisher(args.project, args.topic)
    publisher.publish(data)


def subscriber_init_main():
    """Execute the kcidb-subscriber-init command-line tool"""
    description = \
        'kcidb-subscriber-init - Initialize a Kernel CI report subscriber'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-p', '--project',
        help='ID of the Google Cloud project with the message queue',
        required=True
    )
    parser.add_argument(
        '-t', '--topic',
        help='Name of the subscription\'s message queue topic',
        required=True
    )
    parser.add_argument(
        '-s', '--subscription',
        help='Name of the subscription to create',
        required=True
    )
    args = parser.parse_args()
    subscriber = MQSubscriber(args.project, args.topic, args.subscription)
    subscriber.init()


def subscriber_cleanup_main():
    """Execute the kcidb-subscriber-cleanup command-line tool"""
    description = \
        'kcidb-subscriber-cleanup - Cleanup a Kernel CI report subscriber'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-p', '--project',
        help='ID of the Google Cloud project with the message queue',
        required=True
    )
    parser.add_argument(
        '-t', '--topic',
        help='Name of the subscription\'s message queue topic',
        required=True
    )
    parser.add_argument(
        '-s', '--subscription',
        help='Name of the subscription to remove',
        required=True
    )
    args = parser.parse_args()
    subscriber = MQSubscriber(args.project, args.topic, args.subscription)
    subscriber.cleanup()


def subscriber_pull_main():
    """Execute the kcidb-subscriber-pull command-line tool"""
    description = \
        'kcidb-subscriber-pull - Pull with a Kernel CI report subscriber'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-p', '--project',
        help='ID of the Google Cloud project with the message queue',
        required=True
    )
    parser.add_argument(
        '-t', '--topic',
        help='Name of the subscription\'s message queue topic',
        required=True
    )
    parser.add_argument(
        '-s', '--subscription',
        help='Name of the subscription to pull from',
        required=True
    )
    args = parser.parse_args()
    subscriber = MQSubscriber(args.project, args.topic, args.subscription)
    ack_id, data = subscriber.pull()
    json.dump(data, sys.stdout, indent=4, sort_keys=True)
    sys.stdout.flush()
    subscriber.ack(ack_id)


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
