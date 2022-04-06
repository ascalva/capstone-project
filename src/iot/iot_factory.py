from .iot_sensor   import Sensor
from .iot_service  import Service
from .iot_consumer import Consumer

class IOT_Factory :
    def __init__(self) :
        self.__default = Sensor
        self.__select  = {
            "sensor"   : Sensor,
            "service"  : Service,
            "consumer" : Consumer
        }
    
    def __getitem__(self, type) :
        return self.__select.get(type, self.__default)
