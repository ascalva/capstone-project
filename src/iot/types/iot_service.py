import json
import threading
import socket

from typing         import Dict, Optional
from common         import PacketType, ServiceType, S
from ..iot_base     import IOT_Base
from ..service_base import ServiceBase


class Service(IOT_Base, ServiceBase) :
    def __init__(self, topic: str, data_file: Optional[str] = None):
        super().__init__(topic)

        self.initBrokerConnection()

        if self.ad_node is not None :
            self.start()
        
        else :
            print(f"Failed to find broker, quitting now!")


    def initBrokerConnection(self) :
        msg = {
            "type"         : PacketType.IOT_REQUEST, 
            "service_type" : ServiceType.SERVICE,
            "sender"       : self.hostname,
            "topic"        : self.topic
        }
        _ = self.identifyBroker(msg)


    def executeService(self, params):
        # TEST: Params consists of values that need to be averaged.
        values = params["values"]

        return sum(values) / len(values)


    def start(self) :

        while True :
            try :
                packet   = self.sock.recv(S.PACKET_SIZE)
                data     = json.loads(packet.decode(S.ENCODING))
                sender   = data["sender"]
                trans_id = data["trans_id"]
                params   = data["params"]

                print("## Got request ##")
                msg = json.dumps({
                    "type"         : PacketType.IOT_RESPONSE,
                    "service_type" : ServiceType.SERVICE,
                    "sender"       : self.hostname,
                    "trans_id"     : trans_id,
                    "output"       : self.executeService(params)
                }).encode(S.ENCODING)

                self.sock.sendto(msg, (sender, self.sport))
                print("## Sent back response ##")
            
            # Socket does have a timeout, ignore timeout and try again.
            except socket.timeout as e :
                pass

            # Actual error, leave loop and exit.
            except socket.error as e :
                print("!!! Socket error: ")
                print(e)
                break
            
            # Ignore packets that don't have proper json objects.
            except json.JSONDecodeError as e :
                print("!!! Error parsing JSON object: ")
                print(e)
            
            # Ignore packets that don't have correct fields in json.
            except KeyError as e :
                print("!!! Key not found in recieved dictionary: ")
                print(e)
            