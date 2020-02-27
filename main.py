"""Google Cloud Functions for Kernel CI reporting"""

import os
import sys
import json
import base64
import kcidb

DB_CLIENT = kcidb.DBClient(os.environ['KCIDB_DATASET'])


# pylint: disable=unused-argument
def kcidb_consume(event, context):
    """
    Consume KCIDB data from a Pub Sub subscription
    """
    data = kcidb.MQSubscriber.decode_data(base64.b64decode(event['data']))
    json.dump(data, sys.stdout)
    DB_CLIENT.load(data)
