from typing     import Dict, Optional
from ..iot_base import IOT_Base

class Sensor(IOT_Base) :
    def __init__(self, topic: str = "temperature", data_file: Optional[str] = None):
        super().__init__(topic, data_file)

        # Create data stream (will be sent to broker).
        if self.connected :
            data_stream = self.createStream(data_file)
            self.run(data_stream)

