from common     import PacketType, ServiceType, ConsumerAction
from ..iot_base import IOT_Base

class Consumer(IOT_Base) :
    def __init__(self, topic: str = ""):
        super().__init__(topic)

        self.initBrokerConnection()

        # Create data stream (will be sent to broker).
        if self.connected :
            self.start()

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
        print(data)


    def subscribeToSensor(self) :
        pass

    def subscribeToService(self) :
        pass

    def start(self) :
        pass