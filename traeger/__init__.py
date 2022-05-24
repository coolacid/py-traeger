import boto3
import requests
import logging
import json
from urllib.parse import urlparse
from time import time
from dacite import from_dict
from traeger.dataclass import TreagerData
import paho.mqtt.client as mqtt

logger = logging.getLogger('traegerpy')

class Traeger:
    Cognito_ClientId = "2fuohjtqv1e63dckp5v84rau0j"
    API_Endpoint = "1ywgyc65d1"
    Topics = {
                "updates": "prod/thing/update/",
             }

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.access_token_expires = 0
        self.mqtt_url_expires = 0
        self.treagerdata = {}
        self.things = {}
        self.callbacks = {}

        # Do an initial login, and get our information
        self.login()
        initial_data = self.get_data()
        self.familyName = initial_data['familyName']
        self.fullName = initial_data['fullName']
        self.givenName = initial_data['givenName']

        self.thing_list = {}
        for item in initial_data['things']:
            self.thing_list[item['thingName']] = item

        # Setup some mqtt bits
        self.mqtt_client = mqtt.Client(transport = "websockets")
        self.mqtt_client.tls_set()
        self.mqtt_client.on_connect = self.mqtt_on_connect
        self.mqtt_client.on_message = self.mqtt_on_message
        self.mqtt_client.on_disconnect = self.mqtt_on_disconnect
        self.mqtt_connect()

    def __repr__(self):
        things = []
        for item in self.thing_list.values():
            things.append(f"{item['thingName']} - {item['friendlyName']}")
        return f"Traeger: {self.fullName} - Smokers: {things}"

    def login(self):
        self.client = boto3.client("cognito-idp", region_name="us-west-2")
        response = self.client.initiate_auth( ClientId=self.Cognito_ClientId, AuthFlow="USER_PASSWORD_AUTH", AuthParameters={"USERNAME": self.username, "PASSWORD": self.password},)
        self.access_token_expires = time() + response["AuthenticationResult"]["ExpiresIn"]
        self.token = response["AuthenticationResult"]["IdToken"]

    def get_data(self):
        if time() >= self.access_token_expires:
            self.login()
        r = requests.get(f"https://{self.API_Endpoint}.execute-api.us-west-2.amazonaws.com/prod/users/self", headers = {'authorization': self.token})
        return r.json()

    # MQTT Bits
    # Callbacks: https://pypi.org/project/paho-mqtt/#callbacks
    def mqtt_on_connect(self, client, userdata, flags, rc):
        self.mqtt_subscribe()
        logger.info("MQTT Connected")

    def mqtt_on_message(self, client, userdata, message):
        logger.debug("Received message '" + str(message.payload) + "' on topic '"
            + message.topic + "' with QoS " + str(message.qos))

        if message.topic.startswith(self.Topics["updates"]):
            grill_id = message.topic[len(self.Topics["updates"]):].lower()
            self.things[grill_id] = json.loads(message.payload)
            self.treagerdata[grill_id] = from_dict(data_class = TreagerData, data = json.loads(message.payload))

        if self.callbacks[message.topic]:
            for callback in self.callbacks[message.topic]:
                callback(client, userdata, message)

    def mqtt_on_disconnect(self, client, userdata, rc):
        logger.info("MQTT Disconnected")
        self.mqtt_connect()

    def get_mqtt_url(self):
        if time() >= self.access_token_expires:
            self.login()
        r = requests.post(f"https://{self.API_Endpoint}.execute-api.us-west-2.amazonaws.com/prod/mqtt-connections", headers = {'authorization': self.token})
        response = r.json()
        self.mqtt_url_expires = time() + response["expirationSeconds"]
        self.mqtt_url = response['signedUrl']
        return self.mqtt_url

    def message_callback_add(self, sub, callback):
        if sub not in self.callbacks:
            self.callbacks[sub] = []
        self.callbacks[sub].append(callback)

    def mqtt_connect(self):
        if time() >= self.mqtt_url_expires:
            self.get_mqtt_url()
        mqtt_parts = urlparse(self.mqtt_url)
        headers = {
            "Host": "{0:s}".format(mqtt_parts.netloc),
        }
        self.mqtt_client.ws_set_options(path="{}?{}".format(mqtt_parts.path, mqtt_parts.query), headers=headers)
        self.mqtt_client.connect(mqtt_parts.netloc, 443)
        self.mqtt_client.loop_start()

    def mqtt_subscribe(self):
        # Subscribe all the grills
        for item in self.thing_list:
            self.mqtt_client.subscribe(f"{self.Topics['updates']}{item}")

    # Commands

    def getStatus(self, thingName = None):
        if thingName is None:
            # Return a generator of grills if the grill is in things
            return (self.things[i.lower()] for i in self.thing_list if i.lower() in self.things)
        else:
            if thingName.lower() in self.things:
                return self.things[thingName.lower()]
        logger.info(f"{thingName} not found in things.")

    def sendCommand(self, thingName, command, *args):
        # Check to see if we know the thingName exists
        if thingName.lower() not in self.things:
            logger.error(f"Unknown thingName: {thingName}")
            return None

        if time() >= self.access_token_expires:
            self.login()
        parsedCommand = {'command': "90"}
        r = requests.post(f"https://{self.API_Endpoint}.execute-api.us-west-2.amazonaws.com/prod/things/{thingName}/commands", 
                    headers = {'authorization': self.token},
                    json = parsedCommand,
                )
