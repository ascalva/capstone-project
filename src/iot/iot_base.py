import os
import json
import socket
import paho.mqtt.client as mqtt

from networking import Discovery
from common     import PacketType, ServiceType
from abc        import ABC, abstractmethod


class IOT_Base(ABC) :

    def __init__(self, topic: str) :
        self.topic       = topic
        self.ad_node     = None
        self.broker_node = None
        self.connected   = False
        
        # Start probing network, find neighbors (potential ad/leader node).
        self.network     = Discovery()
        self.hostname    = os.environ.get("HOSTNAME", self.network.ip_addr)

        # Create socket for sending data and make it time out after 3 seconds.
        self.sock        = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", 8000))
        self.sock.settimeout(3)  


    def identifyBroker(self, msg_ = None) :
        msg  = json.dumps(msg_).encode("utf-8")
        data = None

        for n in self.network.neighbors :
            try :
                self.sock.sendto(msg, (n, 8000))

                # TODO: Might need a loop, in case iot device gets message from other iot.
                packet = self.sock.recv(1024)
                data   = json.loads(packet.decode("utf-8"))

                if "type" in data and data["type"] == PacketType.IOT_RESPONSE :
                    self.ad_node     = data["sender"]
                    self.broker_node = data["broker"]
                    self.connectToBroker()
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
        
        return data
        

    def connectToBroker(self) -> None : 
        try :
            self.client = mqtt.Client(self.topic)
            self.client.connect(self.broker_node)
            self.connected = True
        
        except Exception as err :
            print(err)


    @abstractmethod
    def initBrokerConnection(self) :
        pass

    @abstractmethod
    def start(self) :
        pass
