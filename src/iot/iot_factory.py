from .types import Service, Sensor, Consumer

class IOT_Factory :
    def __init__(self) :
        self.__default = Sensor
        self.__select  = {
            "sensor"   : Sensor,
            "service"  : Service,
            "consumer" : Consumer
        }
    
    def __getitem__(self, type) :
        return self.__select.get(type.lower(), self.__default)
