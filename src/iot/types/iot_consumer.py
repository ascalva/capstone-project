import time
import random
import json

from socket     import error as SocketException
from common     import PacketType, ServiceType, ServiceStatus, ConsumerAction, S
from ..iot_base import IOT_Base


class Consumer(IOT_Base) :
    def __init__(self, topic: str = ""):
        super().__init__(topic)

        # Output performance information.
        # self.output = open(f"./data/data/consumer_{self.hostname}.txt", 'w')

        self.consume_service_type = {
            ServiceType.SENSOR  : self.subscribeToSensor,
            ServiceType.SERVICE : self.subscribeToService
        }

        self.initBrokerConnection()

        # Create data stream (will be sent to broker).
        if self.ad_node is not None :
            # For testing
            s_type = ServiceType.SERVICE

            self.sock.settimeout(None)
            self.start(s_type)

        else :
            print(f"Failed to find broker, quitting now!")


    def initBrokerConnection(self):
        msg = {
            "type"          : PacketType.IOT_REQUEST,
            "service_type"  : ServiceType.CONSUMER,
            "consumer_type" : ConsumerAction.JOIN,
            "sender"        : self.hostname
        }
        
        # # NOTE: For testing purposes, don't need to try connecting to all devices
        # #       in network. Speeds up the process when there are many local devices.
        # known_hub = self.hostname.split("_")[0] + "_"

        data = self.identifyBroker(msg, connect=False)
        self.get_host_from_service = self.invertDictOfLists(data["services"])


    def subscribeToSensor(self) :
        def on_message(client, userdata, message) :
            print(f"Received message: {message.payload.decode(S.ENCODING)}")

        topic_to_sub = "temperature"
        topic_host   = self.get_host_from_service[topic_to_sub]

        msg = json.dumps({
            "type"          : PacketType.IOT_REQUEST,
            "service_type"  : ServiceType.CONSUMER,
            "consumer_type" : ConsumerAction.REQUEST,
            "sender"        : self.hostname,
            "topic"         : topic_to_sub
        }).encode(S.ENCODING)

        try :
            self.sock.sendto(msg, (topic_host, 8000))

            packet = self.sock.recv(1024)
            data   = json.loads(packet.decode(S.ENCODING))
            broker = data["broker"]
            self.connectToBroker(broker_name=broker)
        
        except SocketException as e :
            print(e)

        if self.connected :
            self.client.loop_start()
            self.client.on_message = on_message
            self.client.subscribe(topic_to_sub)

            time.sleep(20)


    def subscribeToService(self) :
        topic_to_sub = "average"
        topic_host   = self.get_host_from_service[topic_to_sub]

        # start_time = time.time()

        msg = json.dumps({
            "type"          : PacketType.IOT_REQUEST,
            "service_type"  : ServiceType.CONSUMER,
            "consumer_type" : ConsumerAction.REQUEST,
            "sender"        : self.hostname,
            "topic"         : topic_to_sub,
            "values"        : [1,2,3,4] # Test
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
        
        # total_time = time.time() - start_time
        # self.output.write(f"{total_time:.3f}\n")


    def start(self, s_type) :
        
        while True :
            self.consume_service_type[s_type]()