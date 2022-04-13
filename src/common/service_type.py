import enum

class ServiceType(str, enum.Enum) :
    SENSOR   = enum.auto()
    SERVICE  = enum.auto()
    CONSUMER = enum.auto()

    # TODO: Need to add hybrids:
    #         - Consumer-Sensor
    #         - Consumer-Service


class ServiceStatus(str, enum.Enum) :

    # Sent by IOT device when it's ready for new client.
    READY = enum.auto()
    BUSY  = enum.auto()

class ConsumerAction(str, enum.Enum) :
    JOIN    = enum.auto()
    LIST    = enum.auto()
    REQUEST = enum.auto()
    