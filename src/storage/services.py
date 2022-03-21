from .host_services import HostService
from util           import RWLock

class ServiceTable :
    def __init__(self, neighbors) :
        self.lock      = RWLock()
        self.table     = {}

        # Keep list of neighbors for book keeping who is left to update.
        self.neighbors = neighbors


    def __str__(self) -> str:
        self.lock.reader_acquire()

        table_str = "\n".join([str(row) for row in self.table.values()])
        self.lock.reader_release()
        return table_str
    

    def __addHost(self, host, source, data) :
        self.table[host] = HostService(host, source, data, self.neighbors)


    def __updateHost(self, host, sender, data) :
        self.table[host].updateServices(data, sender)


    def dropHost(self, host) :
        del self.table[host]


    def createPacket(self, send_to=None) :
        # TODO: If dirty, don't send to node that made it dirty (sender of last update).
        # TODO: Check if there should be an update going to that node, need to send message if no.
        temp_table = {}

        self.lock.reader_acquire()

        for k, v in self.table.items() :
            if v.isDirty(send_to) :
                temp_table[k] = v.createPacket()
        
        self.lock.reader_release()

        print(f"Sending {send_to} the packet: {temp_table}")
        return temp_table, True


    def readPacket(self, data) :
        services = data["services"]
        sender   = data["sender"]

        self.lock.writer_acquire()

        for k, v in services.items() :
            if k not in self.table :
                self.__addHost(k, sender, v)
            
            else :
                self.__updateHost(k, sender, v)
        
        self.lock.writer_release()


    def __isDone(self) :
        return all(not v.isDirty() for v in self.table.values())


    def markNeighborUTD(self, neighbor) :
        self.lock.writer_acquire()

        for row in self.table.values() : row.done(neighbor)
        
        self.lock.writer_release()


    def addServiceToHost(self, host, service_name) :
        self.lock.writer_acquire()

        self.table[host].addService(service_name, host)

        self.lock.writer_release()
