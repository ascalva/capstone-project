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
    DONE  = enum.auto()


class ConsumerAction(str, enum.Enum) :
    
    # Request to communicate with local broker/ad node.
    JOIN    = enum.auto()

    # Request list of available services.
    LIST    = enum.auto()

    # Check if service exists.
    EXISTS  = enum.auto()

    # Used for requesting service/sensor data from remote ad nodes.
    REQUEST = enum.auto()
    