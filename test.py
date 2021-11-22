#!/usr/bin/env python3

import os
import logging
from traeger import Traeger
from dotenv import load_dotenv, find_dotenv
from time import sleep
from pprint import pprint as pp

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

load_dotenv(find_dotenv())

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
myThing = os.getenv("MYTHING")

t = Traeger(username, password)
pp(t)
while True:

#    for x in t.getStatus():
#        pp(x)

    t.sendCommand(myThing, "90")

    pp(t.treagerdata)
    pp(t.getStatus(myThing))
    sleep(10)

