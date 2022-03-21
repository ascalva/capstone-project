import os
import json
import time
import logging
import paho.mqtt.client as mqtt
from random                import randrange, uniform
from typing                import Iterator, Dict
from .networking.discovery import Discovery

class Service :

    def __init__(self, topic: str = "temperature", data_file: str = None) :
        self.data_stream     = self.createStream(data_file)
        self.network         = Discovery()
        self.broker          = self.network.broker
        self.addr            = self.network.ip_addr

        self.connectToBroker(self.broker, topic)

    def connectToBroker(self, broker_hostname: str, topic: str) -> None : 
        self.client = mqtt.Client(topic)
        self.client.connect(broker_hostname)

    def createStream(self, data_file: str = None) -> Iterator[Dict[str, float]]:
        
        # Read specifc data as json, should be strucutured as list of dictionaries or
        # dictionaries with a list of data as a value for every key.
        if data_file is not None and os.path.exists(data_file) :
            with open(data_file, 'r') as f :
                data = iter(json.load(f))
                
        # Simulate data.
        else :
            data = iter(lambda: {"temperature" : uniform(20.0, 21.0)}, 1)

        return data

    def publishData(self, data: Dict[str, float]) -> bool : 
        print(f"Current temperature is {data['temperature']} degrees Celcius.")
        self.client.publish("Temperature", data["temperature"])

    def run(self, delay: int = 1) -> None :
        while (curr := next(self.data_stream, False)) :
            self.publishData(curr)
            time.sleep(delay)


def get_test_service() -> Service :
    broker_hostname = "dummy"
    topic           = "dummy_topic"
    filename        = "data.json"

    return Service(topic, filename)
