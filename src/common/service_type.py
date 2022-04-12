import enum

class ServiceType(str, enum.Enum) :
    SENSOR   = enum.auto()
    SERVICE  = enum.auto()
    CONSUMER = enum.auto()


# class ServiceResponse(str, enum.Enum) :
    
#     # Sent for services acting as sensors, anyone can read.
#     BROKER_INVITE = enum.auto()

#     # Sent for services with critical section, must wait for turn.
#     WAIT          = enum.auto()

#     # Answer has arrived.
#     OUTPUT        = enum.auto()


class ServiceStatus(str, enum.Enum) :

    # Sent by IOT device when it's ready for new client.
    READY = enum.auto()
    BUSY  = enum.auto()

class ConsumerType(str, enum.Enum) :
    JOIN    = enum.auto()
    LIST    = enum.auto()
    REQUEST = enum.auto()
    