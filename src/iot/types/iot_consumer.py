import time
import json

from socket     import error as SocketException
from common     import PacketType, ServiceType, ServiceStatus, ConsumerAction, S
from ..iot_base import IOT_Base


class Consumer(IOT_Base) :
    def __init__(self, topic: str = ""):
        super().__init__(topic)

        self.consume_service_type = {
            ServiceType.SENSOR  : self.subscribeToSensor,
            ServiceType.SERVICE : self.subscribeToService
        }

        self.initBrokerConnection()

        # Create data stream (will be sent to broker).
        if self.ad_node is not None :
            # For testing
            s_type = ServiceType.SENSOR
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

        data = self.identifyBroker(msg, connect=False)
        self.get_host_from_service = self.invertDictOfLists(data["services"])
        # print(data)


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
        topic_to_sub = ""
        topic_host   = self.get_host_from_service[topic_to_sub]

        msg = json.dumps({
            "type"          : PacketType.IOT_REQUEST,
            "service_type"  : ServiceType.CONSUMER,
            "consumer_type" : ConsumerAction.REQUEST,
            "sender"        : self.hostname,
            "topic"         : topic_to_sub
        }).encode(S.ENCODING)

        self.sock.sendto(msg, (topic_host, 8000))

        # Might timeout, need to check for that.
        while True :
            packet = self.sock.recv(S.PACKET_SIZE)
            data   = json.loads(packet.decode(S.ENCODING))

            if data["status"] == ServiceStatus.BUSY :
                continue

            if ("output" in data) and (data["output"] is not None):
                output = data["output"]
                print(f"OUTPUT OF SERVICE {topic_to_sub} : {output}")
                break


    def start(self, s_type) :
        self.consume_service_type[s_type]()