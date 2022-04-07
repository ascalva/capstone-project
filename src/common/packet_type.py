import enum

class PacketType(str, enum.Enum) :
    
    ################## IOT-Related Message Types ######################

    # Request made by IOT to get remote broker hostname and subscribe to service.
    # IOT_REQUEST_TO_SUBSCRIBE  = enum.auto()

    # Request made by IOT to get broker hostname and start publishing.
    IOT_REQUEST               = enum.auto()

    # Lead node/hub response with broker hostname.
    IOT_RESPONSE              = enum.auto()

    # Message from IOT device/service notifying that it's done publishing.
    IOT_END                   = enum.auto()


    ############## Database Node-Related Message Types ################
    DBH_ADVERT                = enum.auto()
    DBH_NOT_DEAD              = enum.auto()

    DBH_HOST_UPDATE           = enum.auto()
    DBH_EDGE_UPDATE           = enum.auto()


    ########################## Error Messages #########################

    SERVICE_NOT_FOUND         = enum.auto()
    PARSING_ERROR             = enum.auto()
