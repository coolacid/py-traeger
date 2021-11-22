#!/usr/bin/env python3

import os
import json
import logging
from traeger import Traeger
from dotenv import load_dotenv, find_dotenv
from time import sleep
from pprint import pprint as pp
from datetime import datetime
from elasticsearch import Elasticsearch


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

load_dotenv(find_dotenv())
es_logger = logging.getLogger('elasticsearch')
es_logger.setLevel(logging.WARNING)

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
myThing = os.getenv("MYTHING")
es = Elasticsearch(os.getenv("ELASTIC"))

def toElastic(client, userdata, message):
    if message.topic.startswith("prod/thing/update/"):
        data = json.loads(message.payload)
        data.pop("custom_cook")
        data['timestamp'] = datetime.utcnow()
        res = es.index(index="test-index", doc_type="_doc", body=data)
        print(f"Got Update for {myThing}")

t = Traeger(username, password)
t.message_callback_add(f'prod/thing/update/{myThing}', toElastic)

while True:
    t.sendCommand(myThing, "90")
    status = t.getStatus(myThing)
    if status and status['status']['connected']:
        sleep(10)
    else:
        sleep(120)
