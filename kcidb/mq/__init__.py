"""Kernel CI report message queue"""

import argparse
import json
import sys
from google.cloud import pubsub
from google.api_core.exceptions import DeadlineExceeded
from kcidb import io


class Publisher:
    """Kernel CI message queue publisher"""
    # pylint: disable=no-member

    @staticmethod
    def encode_data(io_data):
        """
        Encode JSON data, adhering to a version of I/O schema, into message
        data.

        Args:
            io_data:    JSON data to be encoded, adhering to an I/O schema
                        version.

        Returns
            The encoded message data.
        """
        assert io.schema.is_valid(io_data)
        return json.dumps(io.schema.upgrade(io_data)).encode()

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
                    Must adhere to a version of I/O schema.
        """
        assert io.schema.is_valid(data)
        self.client.publish(self.topic_path, Publisher.encode_data(data))


class Subscriber:
    """Kernel CI message queue subscriber"""
    # pylint: disable=no-member

    @staticmethod
    def decode_data(message_data):
        """
        Decode message data to extract the JSON data adhering to the latest
        I/O schema.

        Args:
            message_data:   The message data from the message queue
                            ("data" field of pubsub.types.PubsubMessage) to be
                            decoded.

        Returns
            The decoded JSON data adhering to the latest I/O schema.
        """
        data = json.loads(message_data.decode())
        return io.schema.upgrade(data, copy=False)

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
            * The JSON data from the message queue, adhering to the latest I/O
              schema.
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
        data = Subscriber.decode_data(message.message.data)
        assert io.schema.is_valid_latest(data)
        return message.ack_id, data

    def ack(self, ack_id):
        """
        Acknowledge reception of data.

        Args:
            ack_id: The ID received with the data to be acknowledged.
        """
        self.client.acknowledge(self.subscription_path, [ack_id])


def publisher_init_main():
    """Execute the kcidb-mq-publisher-init command-line tool"""
    description = \
        'kcidb-mq-publisher-init - Initialize a Kernel CI report publisher'
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
    publisher = Publisher(args.project, args.topic)
    publisher.init()


def publisher_cleanup_main():
    """Execute the kcidb-mq-publisher-cleanup command-line tool"""
    description = \
        'kcidb-mq-publisher-cleanup - Cleanup a Kernel CI report publisher'
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
    publisher = Publisher(args.project, args.topic)
    publisher.cleanup()


def publisher_publish_main():
    """Execute the kcidb-mq-publisher-publish command-line tool"""
    description = \
        'kcidb-mq-publisher-publish - ' \
        'Publish with a Kernel CI report publisher'
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
    data = io.schema.upgrade(data, copy=False)
    publisher = Publisher(args.project, args.topic)
    publisher.publish(data)


def subscriber_init_main():
    """Execute the kcidb-mq-subscriber-init command-line tool"""
    description = \
        'kcidb-mq-subscriber-init - Initialize a Kernel CI report subscriber'
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
    subscriber = Subscriber(args.project, args.topic, args.subscription)
    subscriber.init()


def subscriber_cleanup_main():
    """Execute the kcidb-mq-subscriber-cleanup command-line tool"""
    description = \
        'kcidb-mq-subscriber-cleanup - Cleanup a Kernel CI report subscriber'
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
    subscriber = Subscriber(args.project, args.topic, args.subscription)
    subscriber.cleanup()


def subscriber_pull_main():
    """Execute the kcidb-mq-subscriber-pull command-line tool"""
    description = \
        'kcidb-mq-subscriber-pull - Pull with a Kernel CI report subscriber'
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
    subscriber = Subscriber(args.project, args.topic, args.subscription)
    ack_id, data = subscriber.pull()
    json.dump(data, sys.stdout, indent=4, sort_keys=True)
    sys.stdout.flush()
    subscriber.ack(ack_id)
