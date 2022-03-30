import os
import json
import time
import socket
import paho.mqtt.client as mqtt

from random               import randrange, uniform
from typing               import Iterator, Dict
from networking.discovery import Discovery
from networking           import PacketType


class Service :

    def __init__(self, topic: str = "temperature", data_file: str = None) :
        self.ad_node         = None
        self.broker_node     = None
        self.topic           = topic
        
        # Start probing network, find neighbors (potential ad/leader node).
        self.network         = Discovery()
        self.hostname        = os.environ.get("HOSTNAME", self.network.ip_addr)

        # Create data stream (will be sent to broker).
        self.data_stream     = self.createStream(data_file)

        # Create socket for sending data (TODO: create socket for receiving additional data).
        self.sock            = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", 8000))
        self.sock.settimeout(3)  # Time out after 3 seconds.

        # Identify leader node and broker.
        self.identifyBroker()
        self.connectToBroker()


    def identifyBroker(self) :
        msg = json.dumps({
            "type"   : PacketType.IOT_REQUEST_TO_PUBLISH, 
            "sender" : self.hostname,
            "topic"  : self.topic
        }).encode("utf-8")

        for n in self.network.neighbors :
            try :
                print(f"Trying neighbor {n}")
                self.sock.sendto(msg, (n, 8000))

                # TODO: Might need a loop, in case iot device gets message from other iot.
                packet = self.sock.recv(1024)
                data   = json.loads(packet.decode("utf-8"))

                if "type" in data and data["type"] == PacketType.IOT_RESPONSE :
                    print("SUCCESS: Found suitable ad node!")
                    self.ad_node     = data["sender"]
                    self.broker_node = data["broker"]
                    print(f"Got the goods:")
                    print(f" . |-> Ad:     {self.ad_node}")
                    print(f" . |-> Broker: {self.broker_node}")
                    break
            
            except socket.timeout as e :
                print("Connection timeout, moving on to next neighbor..")
                print(e)

            except socket.error as e :
                print("Socket error, something went wrong.")
                print(e)
            
            except json.JSONDecodeError as e :
                print("Error parsing JSON object.")
                print(e)


    def connectToBroker(self) -> None : 
        self.client = mqtt.Client(self.topic)
        self.client.connect(self.broker_node)


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


if __name__ == "__main__" :
    topic = os.environ.get("TOPIC", "")
    iot   = Service(topic=topic)