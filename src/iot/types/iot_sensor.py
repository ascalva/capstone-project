import os
import time
import json

from random     import randrange, uniform
from typing     import Dict, Optional, Iterator
from common     import PacketType, ServiceType
from ..iot_base import IOT_Base


class Sensor(IOT_Base) :
    def __init__(self, topic: str, data_file: Optional[str] = None):
        super().__init__(topic)
        self.verbose = False

        self.initBrokerConnection()

        # Create data stream (will be sent to broker).
        if self.connected :
            self.start(data_file)

        else :
            print(f"Failed to find broker, quitting now!")


    def initBrokerConnection(self) :
        msg = {
            "type"         : PacketType.IOT_REQUEST, 
            "service_type" : ServiceType.SENSOR,
            "sender"       : self.hostname,
            "topic"        : self.topic
        }

        # Could do something with the packet data?
        _ = self.identifyBroker(msg)
    

    def start(self, data_file) :
        delay       = 3
        data_stream = self.createStream(data_file)

        while (curr := next(data_stream, {})) :
            self.publishData(curr)
            time.sleep(delay)


    def createStream(self, data_file: Optional[str] = None) -> Iterator[Dict[str, float]]:
        
        # Read specifc data as json, should be strucutured as list of dictionaries or
        # dictionaries with a list of data as a value for every key.
        if data_file is not None and os.path.exists(data_file) :
            with open(data_file, 'r') as f :
                data = iter(json.load(f))
                
        # Simulate data.
        else :
            data = iter(lambda: {self.topic : uniform(20.0, 25.0)}, 1)

        # self.data_stream = data
        return data


    def publishData(self, data: Dict[str, float]) -> None : 
        if self.verbose : 
            print(f"Current value of {self.topic} : {data[self.topic]}")
        self.client.publish(self.topic, data[self.topic])
