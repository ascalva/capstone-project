import threading
import socket

from typing     import Dict, Optional
from common     import PacketType, ServiceType
from ..iot_base import IOT_Base


class Service(IOT_Base) :
    def __init__(self, topic: str, data_file: Optional[str] = None):
        super().__init__(topic)

        # TODO: create socket and thread for receiving additional data
    

    def initBrokerConnection(self) :
        msg = {
            "type"         : PacketType.IOT_REQUEST, 
            "service_type" : ServiceType.SERVICE,
            "sender"       : self.hostname,
            "topic"        : self.topic
        }
        _ = self.identifyBroker(msg)


    def start(self) :
        pass
