import enum

class PacketType(str, enum.Enum) :
    IOT_REQUEST  = enum.auto()
    IOT_RESPONSE = enum.auto()
    IOT_END      = enum.auto()
    DBH_ADVERT   = enum.auto()
    DBH_NOT_DEAD = enum.auto()
