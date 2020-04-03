"""
Kernel CI notification spool.

The spool registers notifications, and doesn't allow registering the same
notification twice. It stores generated notification emails, so they can be
picked up and sent asynchronously and provides an interface for making sure
every notification email is sent, and sent only once (as well as possible).
"""

import datetime
import email
from google.cloud import firestore
from kcidb.misc import Notification, is_valid_firestore_id

# Because we like the "id" name
# pylint: disable=invalid-name,redefined-builtin


class Client:
    """Notification spool client"""

    @staticmethod
    def is_valid_id(value):
        """
        Check if a value is a valid notification ID.

        Args:
            value: The value to check.

        Returns:
            True if the value is a valid notification ID,
            False if not.
        """
        return is_valid_firestore_id(value)

    def __init__(self, pick_timeout=None):
        """
        Initialize a spool client.

        Args:
            pick_timeout:   A datetime.timedelta object specifying how long a
                            notification should be considered picked, by
                            default, or None, meaning 10 minutes.
        """
        assert pick_timeout is None or \
            isinstance(pick_timeout, datetime.timedelta)
        self.db = firestore.Client()
        self.parser = email.parser.BytesParser(policy=email.policy.SMTPUTF8)
        self.pick_timeout = pick_timeout or datetime.timedelta(minutes=10)

    def _get_coll(self):
        """
        Get a reference for the notification document collection.

        Returns:
            The notification document collection reference.
        """
        return self.db.collection("notifications")

    def _get_doc(self, id):
        """
        Get the notification document reference for specified ID.

        Args:
            id:         The ID of the notification to get the document
                        reference for. Must be a valid Firestore ID.

        Returns:
            The notification document reference.
        """
        return self._get_coll().document(id)

    def put(self, notification, timestamp=None):
        """
        Put a notification onto the spool, if it wasn't there already.

        Args:
            notification:   An instance of kcidb.misc.Notification to put onto
                            the spool.
            timestamp:      A datetime.datetime object specifying the
                            notification creation time, or None to use
                            datetime.datetime.now().

        Returns:
            True, if the notification was put onto the spool,
            False, if not (it was already there).
        """
        assert isinstance(notification, Notification)
        assert timestamp is None or isinstance(timestamp, datetime.datetime)

        @firestore.transactional
        def create_if_not_exists(transaction, doc, notification, timestamp):
            """Create notification document, if not exists, atomically"""
            # If the document already exists
            if doc.get(field_paths=[], transaction=transaction).exists:
                return False
            # Render message saving some space by using UTF-8 in headers
            message_string = notification.render(). \
                as_string(policy=email.policy.SMTPUTF8)
            # Store the notification
            doc.set(dict(
                created_at=(timestamp or datetime.datetime.now()),
                # Set to a definitely timed-out time, free for picking
                picked_until=datetime.datetime.min,
                message=message_string,
            ))
            return True

        return create_if_not_exists(self.db.transaction(),
                                    self._get_doc(notification.id),
                                    notification,
                                    timestamp)

    def pick(self, id, timestamp=None, timeout=None):
        """
        Pick a notification from the spool, for sending.
        A notification can only be picked by one client.

        Args:
            id:         The ID of the notification to pick.
                        Must be a valid Firestore ID.
            timestamp:  A datetime.datetime object specifying the picking
                        time, or None to use datetime.datetime.now().
            timeout:    A datetime.timedelta object specifying how long should
                        the notification stay picked, from the specified
                        timestamp. After that time, the notification becomes
                        free for picking again. None for the default
                        "pick_timeout" specified at initialization time.

        Returns:
            An email.message.EmailMessage object containing parsed
            notification message, ready for sending, or None if the
            notification was already picked, was invalid, or wasn't in the
            spool.
        """
        assert Client.is_valid_id(id)
        assert timestamp is None or isinstance(timestamp, datetime.datetime)
        assert timeout is None or isinstance(timeout, datetime.timedelta)
        if timestamp is None:
            timestamp = datetime.datetime.now()
        if timeout is None:
            timeout = self.pick_timeout

        @firestore.transactional
        def pick_if_not_picked(transaction, doc, timestamp):
            """Pick notification, if not picked yet"""
            # Get the document snapshot
            snapshot = doc.get(field_paths=["picked_until", "message"],
                               transaction=transaction)
            picked_until = snapshot.get("picked_until")
            text = snapshot.get("message")
            # If the document doesn't exist, has no "picked_until" field,
            # no "message" field, or the picking has not timed out yet
            if not picked_until or not text or picked_until > timestamp:
                return None
            # Parse the message
            message = self.parser.parsebytes(text)
            # Mark notification picked until timeout
            doc.update(dict(
                picked_at=timestamp,
                picked_until=timestamp + timeout,
            ))
            return message

        return pick_if_not_picked(self.db.transaction(),
                                  self._get_doc(id),
                                  timestamp)

    def ack(self, id, timestamp=None):
        """
        Acknowledge delivery of a notification picked from the spool.

        Args:
            id:         The ID of the notification to acknowledge.
                        Must have been picked previously by the same client.
            timestamp:  A datetime.datetime object specifying the
                        acknowledgment time, or None to use
                        datetime.datetime.now().
        """
        assert Client.is_valid_id(id)
        assert timestamp is None or isinstance(timestamp, datetime.datetime)
        if timestamp is None:
            timestamp = datetime.datetime.now()
        self._get_doc(id).update(dict(
            acked_at=timestamp,
            picked_until=datetime.datetime.max,
        ))

    def delete(self, id):
        """
        Remove a notification from the spool, regardless of its state.

        Args:
            id: The ID of the notification to remove.
        """
        assert Client.is_valid_id(id)
        self._get_doc(id).delete()

    def wipe(self, until=None):
        """
        Wipe notifications from the spool.

        Args:
            until:  A datetime.datetime object specifying the latest
                    creation time for removed notifications, or None
                    to use datetime.datetime.now().
        """
        assert until is None or isinstance(until, datetime.datetime)
        if until is None:
            until = datetime.datetime.now()
        for snapshot in \
            self._get_coll().where("created_at", "<=", until). \
                select([]).stream():
            snapshot.reference.delete()

    def unpicked(self, timestamp=None):
        """
        Retrieve IDs of notifications, which weren't picked for delivery yet.

        Args:
            timestamp:  A datetime.datetime object specifying the intended
                        pickup time, or None to use datetime.datetime.now().

        Yields:
            The ID of the next notification free for picking.
        """
        assert timestamp is None or isinstance(timestamp, datetime.datetime)
        if timestamp is None:
            timestamp = datetime.datetime.now()
        for snapshot in \
            self._get_coll().where("picked_until", "<", timestamp). \
                select([]).stream():
            id = snapshot.id
            assert Client.is_valid_id(id)
            yield id
