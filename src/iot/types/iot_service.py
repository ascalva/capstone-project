import json
import threading
import socket
import time

from typing         import Dict, Optional
from common         import PacketType, ServiceType, S, ConsumerAction, ServiceStatus
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


    # NOTE: Test code
    def subscribeToService(self, topic_to_sub, topic_host, value) :
        # topic_to_sub = "times_2"
        # topic_host   = "C_"

        start_time = time.time()

        msg = json.dumps({
            "type"          : PacketType.IOT_REQUEST,
            "service_type"  : ServiceType.CONSUMER,
            "consumer_type" : ConsumerAction.REQUEST,
            "sender"        : self.hostname,
            "topic"         : topic_to_sub,
            "values"        : value
        }).encode(S.ENCODING)

        self.sock.sendto(msg, (topic_host, 8000))

        # Might timeout, need to check for that.
        while True :
            packet = self.sock.recv(S.PACKET_SIZE)
            data   = json.loads(packet.decode(S.ENCODING))
            # print(f"Received packet: {data}")

            if "status" not in data :
                print("Status not in data")
                print(data)
                continue

            if data["status"] == ServiceStatus.BUSY :
                continue

            if ("output" in data) and (data["output"] is not None):
                output = data["output"]
                # print(f"OUTPUT OF SERVICE {topic_to_sub} : {output}")
                break
        return output

    def executeService(self, params):
        # TEST: Params consists of values that need to be averaged.
        values = params["values"]
        output = None
        
        if "A_" in self.hostname :
            output = sum(values) / len(values)

            topic_to_sub = "times_2"
            topic_host   = "C_"
            output = self.subscribeToService(topic_to_sub, topic_host, output)
        
        elif "C_" in self.hostname :
            output = values * 2

            topic_to_sub = "power_2"
            topic_host   = "D_"
            output = self.subscribeToService(topic_to_sub, topic_host, output)
        
        elif "D_" in self.hostname :
            output = values ** 2

        return output


    def start(self) :

        while True :
            try :
                packet   = self.sock.recv(S.PACKET_SIZE)

                # start_time = time.time()
                data     = json.loads(packet.decode(S.ENCODING))
                sender   = data["sender"]
                trans_id = data["trans_id"]
                params   = data["params"]

                msg = json.dumps({
                    "type"         : PacketType.IOT_RESPONSE,
                    "service_type" : ServiceType.SERVICE,
                    "sender"       : self.hostname,
                    "trans_id"     : trans_id,
                    "output"       : self.executeService(params)
                }).encode(S.ENCODING)

                self.sock.sendto(msg, (sender, self.sport))
                # total_time = time.time() - start_time
                # print(f"Completed request in {total_time:.2f} seconds")
                
            
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
            