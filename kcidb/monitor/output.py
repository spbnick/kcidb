"""Kernel CI reporting - monitor - output"""

import re
import base64
from email.message import EmailMessage
import kcidb.oo
from kcidb.monitor.misc import is_valid_firestore_id

# We like the "id" name
# pylint: disable=invalid-name

# A regex matching permitted notification message summary strings
NOTIFICATION_MESSAGE_SUMMARY_RE = re.compile(r"[^\x00-\x1f\x7f]*")

# A regex matching permitted subscription name strings
SUBSCRIPTION_RE = re.compile(r"([A-Za-z0-9][A-Za-z0-9_]*)?")


class NotificationMessage:
    """
    Message for a notification about a report object state.
    """
    def __init__(self, recipients, summary="", description="", id=""):
        """
        Initialize a notification message.

        Args:
            recipients:     List of e-mail addresses of notification message
                            recipients.
            summary:        Summary of the object state being notified about.
                            Must encode into 256 bytes of UTF-8 at most.
                            Must be a single-line string without control
                            characters.
            description:    Detailed description of the object state being
                            notified about.
                            Must encode into 4096 bytes of UTF-8 at most.
            id:             String identifier of the notification message.
                            Must encode into 256 bytes of UTF-8 at most.
                            The system will only send one notification with
                            the same ID for the same subscription for each
                            database object.
        """
        assert isinstance(recipients, list)
        assert all(isinstance(r, str) for r in recipients)
        assert isinstance(summary, str)
        assert NOTIFICATION_MESSAGE_SUMMARY_RE.fullmatch(summary)
        assert len(summary.encode()) <= 256
        assert isinstance(description, str)
        assert len(description.encode()) <= 4096
        assert isinstance(id, str)
        assert len(id.encode()) <= 256

        self.recipients = recipients
        self.summary = summary
        self.description = description
        self.id = id


class Notification:
    """
    Notification about a report object state.
    """

    @staticmethod
    def _to_id_part(string):
        """
        Encode a string for safe use as part of a notification ID.

        Args:
            string: The string to encode.

        Returns:
            The encoded string, usable as part of an ID.
        """
        return base64.b64encode(string.encode(), altchars=b'+-').decode()

    @staticmethod
    def _from_id_part(id_part):
        """
        Decode an ID part into the original string passed to _to_id_part()
        previously.

        Args:
            id: The ID part to decode.

        Returns:
            The decoded string.
        """
        return base64.b64decode(id_part, altchars=b'+-',
                                validate=True).decode()

    def __init__(self, obj_type_name, obj, subscription, message):
        """
        Initialize a notification.

        Args:
            obj_type_name:  Name of the object type (e.g. "revision") to
                            which the object notified about belongs.
            obj:            Object-oriented representation of the object
                            being notified about (an instance of
                            kcidb.oo.Object).
            subscription:   The name of the subscription which generated the
                            notification (e.g. the name of subscription
                            module).
                            Must consist only of latin letters, digits, and
                            underscores. Must not start with an underscore.
                            Must encode into 64 bytes of UTF-8 at most.
            message:        Notification message. An instance of
                            NotificationMessage.
        """
        assert isinstance(obj_type_name, str)
        assert obj_type_name
        assert isinstance(obj, kcidb.oo.Object)
        assert isinstance(subscription, str)
        assert SUBSCRIPTION_RE.fullmatch(subscription)
        assert len(subscription.encode()) <= 64
        assert isinstance(message, NotificationMessage)

        self.obj_type_name = obj_type_name
        self.obj = obj
        self.subscription = subscription
        self.message = message
        id = self.subscription + ":" + \
            self.obj_type_name + ":" + \
            Notification._to_id_part(repr(obj.get_id())) + ":" + \
            Notification._to_id_part(message.id)
        assert is_valid_firestore_id(id)
        self.id = id

    def render(self):
        """
        Render the notification as an e-mail message.

        Returns:
            An instance of email.message.EmailMessage with the notification
            ready to send, but missing the From header.
        """
        email = EmailMessage()
        email["Subject"] = self.message.summary + self.obj.summarize()
        email["To"] = ", ".join(self.message.recipients)
        email["X-KCIDB-Notification-ID"] = self.id
        email["X-KCIDB-Notification-Message-ID"] = self.message.id
        email.set_content(self.message.description + self.obj.describe())
        return email
