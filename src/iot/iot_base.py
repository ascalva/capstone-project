import os
import json
import time
import socket
import paho.mqtt.client as mqtt

from random     import randrange, uniform
from typing     import Iterator, Dict, Optional
from networking import Discovery
from common     import PacketType, ServiceType


class IOT_Base :

    def __init__(self, topic: str = "temperature", data_file: Optional[str] = None) :
        self.ad_node         = None
        self.broker_node     = None
        self.topic           = topic
        self.verbose         = False
        self.connected       = False
        
        # Start probing network, find neighbors (potential ad/leader node).
        self.network         = Discovery()
        self.hostname        = os.environ.get("HOSTNAME", self.network.ip_addr)


        # Create socket for sending data (TODO: create socket for receiving additional data).
        self.sock            = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", 8000))
        self.sock.settimeout(3)  # Time out after 3 seconds.

        # Identify leader node and broker.
        if self.identifyBroker() :
            self.connectToBroker()
            self.connected = True

            # Create data stream (will be sent to broker).
            # self.data_stream = self.createStream(data_file)
            # self.run()
        
        else :
            print(f"Failed to find broker, quitting now!")


    def identifyBroker(self) :
        found_broker = False

        msg = json.dumps({
            "type"         : PacketType.IOT_REQUEST_TO_PUBLISH, 
            "sender"       : self.hostname,
            "topic"        : self.topic,
            "service_type" : ServiceType.SENSOR
        }).encode("utf-8")

        for n in self.network.neighbors :
            try :
                if self.verbose : print(f"Trying neighbor {n}")
                self.sock.sendto(msg, (n, 8000))

                # TODO: Might need a loop, in case iot device gets message from other iot.
                packet = self.sock.recv(1024)
                data   = json.loads(packet.decode("utf-8"))

                if "type" in data and data["type"] == PacketType.IOT_RESPONSE :
                    self.ad_node     = data["sender"]
                    self.broker_node = data["broker"]
                    found_broker     = True

                    if self.verbose :
                        print("SUCCESS: Found suitable ad node!")
                        print(f"Got the goods:")
                        print(f" . |-> Ad:     {self.ad_node}")
                        print(f" . |-> Broker: {self.broker_node}")

                    break
            
            except socket.timeout as e :
                print("Connection timeout, moving on to next neighbor..")
                print(e)

            except socket.error as e :
                print("Socket error, something went wrong.")
                print(data)
                print(e)
            
            except json.JSONDecodeError as e :
                print("Error parsing JSON object.")
                print(e)
        
        return found_broker


    def connectToBroker(self) -> None : 
        self.client = mqtt.Client(self.topic)
        self.client.connect(self.broker_node)


    def createStream(self, data_file: Optional[str] = None) -> Iterator[Dict[str, float]]:
        
        # Read specifc data as json, should be strucutured as list of dictionaries or
        # dictionaries with a list of data as a value for every key.
        if data_file is not None and os.path.exists(data_file) :
            with open(data_file, 'r') as f :
                data = iter(json.load(f))
                
        # Simulate data.
        else :
            data = iter(lambda: {self.topic : uniform(20.0, 25.0)}, 1)

        return data


    def publishData(self, data: Dict[str, float]) -> None : 
        print(f"Current value of {self.topic} : {data[self.topic]}")
        # self.client.publish(self.topic, data[self.topic])


    def run(self, data_stream, delay: int = 3) -> None :
        while (curr := next(data_stream, {})) :
            self.publishData(curr)
            time.sleep(delay)
