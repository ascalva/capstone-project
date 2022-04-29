import os
import json
import socket
import paho.mqtt.client as mqtt

from networking import Discovery
from common     import PacketType, S
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
        self.sport       = 8000
        self.sock        = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", self.sport))
        self.sock.settimeout(3)  


    def identifyBroker(self, msg_ = None, connect = True, known_hub=None, hostname_hint=True) :
        msg  = json.dumps(msg_).encode("utf-8")
        data = None

        # NOTE: For testing purposes, don't need to try connecting to all devices
        #       in network. Speeds up the process when there are many local devices.
        known_hub = None
        if hostname_hint :
            known_hub = [self.hostname.split("_")[0] + "_"]

        for n in (known_hub or self.network.neighbors) :
            try :
                self.sock.sendto(msg, (n, self.sport))

                # TODO: Might need a loop, in case iot device gets message from other iot.
                packet = self.sock.recv(1024)
                data   = json.loads(packet.decode("utf-8"))

                if "type" in data and data["type"] == PacketType.IOT_RESPONSE :
                    self.ad_node     = data["sender"]
                    self.broker_node = data["broker"]
                    if connect : self.connectToBroker()
                    print("Found broker/ad node!")
                    break
            
            except socket.timeout as e :
                # print("Connection timeout, moving on to next neighbor..")
                # print(e)
                continue

            except socket.error as e :
                print("Socket error, something went wrong.")
                print(data)
                print(e)
            
            except json.JSONDecodeError as e :
                print("Error parsing JSON object.")
                print(e)
        
        return data
        

    def connectToBroker(self, broker_name=None) -> None : 
        try :
            self.client = mqtt.Client(self.topic)
            self.client.connect(broker_name or self.broker_node)
            self.connected = True
        
        except Exception as err :
            print(err)
    

    @staticmethod
    def invertDictOfLists(d) : 
        d_ = {}
        for k, v in d.items() :
            d_.update({v_elt["name"] : k for v_elt in v}) # TODO
        return d_
    

    @abstractmethod
    def initBrokerConnection(self) :
        pass

    @abstractmethod
    def start(self) :
        pass
