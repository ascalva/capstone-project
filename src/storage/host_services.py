from itertools         import chain
from common            import ServiceType
from .service_metadata import ServiceMetadata

class HostService :
    def __init__(self, host, source, services=None, neighbors=None) :
        self.host     = host
        self.services = set(self.bulkCast(services) or [])

        # An object is dirty if it hasn't yet been shared with it's neighbors.
        self.dirty_table = {n : True for n in neighbors or []}
        
        # Neighbor that shared last update, 
        self.origin   = source
        self.done(self.origin)

        # TODO: Need garbage collector for stale services.
    

    def __str__(self) -> str:
        return f"row[{self.host}] : <{', '.join(self.servicesToStr())}>"
    

    def markDirtyExcept(self, host) :
        for neighbor in self.dirty_table.keys() :
            if neighbor != host :
                self.dirty_table[neighbor] = True


    def updateServices(self, data, sender) :
        if (services := set(self.bulkCast(data))) == self.services :
            return

        self.services = services
        self.origin   = sender

        self.markDirtyExcept(self.origin)
    

    def addService(self, data, host) :
        service_name = data["topic"]
        service_type = ServiceType(data["service_type"])
        new_service  = ServiceMetadata(service_name, service_type)

        if "depends_on" in data :
            # TODO: Need to verify that services that are depended on exist.
            new_service.setDependance(data["depends_on"])

        self.services.add(new_service)
        self.origin = host
        self.markDirtyExcept(self.origin)


    def isDirty(self, neighbor) :
        return self.dirty_table[neighbor]


    def done(self, neighbor) :
        self.dirty_table[neighbor] = False


    def getBroker(self) :
        return self.host + "broker"


    def createPacket(self) :
        return list(map(lambda s : s.toJSON(), self.services))

    
    def servicesToStr(self) :
        return list(map(lambda s : str(s), self.services))

    
    def bulkCast(self, services) :
        return [ServiceMetadata.fromJSON(s) for s in services]

    def getEdges(self) :
        return list(chain.from_iterable(s.getEdges() for s in self.services))