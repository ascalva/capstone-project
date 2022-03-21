class HostService :
    def __init__(self, host, source, services=None, neighbors=None) :
        self.host     = host
        self.services = set(services or [])

        # An object is dirty if it hasn't yet been shared with it's neighbors.
        self.dirty_table = {n : True for n in neighbors or []}
        
        # Neighbor that shared last update, 
        self.origin   = source
        self.done(self.origin)

        # TODO: Need garbage collector for stale services.
    

    def __str__(self) -> str:
        return f"row[{self.host}] : <{', '.join(self.createPacket())}>"
    

    def markDirtyExcept(self, host) :
        for neighbor in self.dirty_table.keys() :
            if neighbor != host :
                self.dirty_table[neighbor] = True


    def updateServices(self, data, sender) :
        if (services := set(data)) == self.services :
            return

        self.services = services
        self.origin   = sender

        self.markDirtyExcept(self.origin)
    

    def addService(self, service_name, host) :
        self.services.add(service_name)
        self.origin = host
        self.markDirtyExcept(self.origin)


    def isDirty(self, neighbor) :
        return self.dirty_table[neighbor]


    def done(self, neighbor) :
        self.dirty_table[neighbor] = False


    def getBroker(self) :
        return self.host + "broker"


    def createPacket(self) :
        return list(self.services)