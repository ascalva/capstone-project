from typing   import Dict, Optional
from .iot_base import IOT_Base

class Service(IOT_Base) :
    def __init__(self, topic: str = "temperature", data_file: Optional[str] = None):
        super().__init__(topic, data_file)

        # TODO: Create thread for listening.
    
    def executeService(self) :
        pass
