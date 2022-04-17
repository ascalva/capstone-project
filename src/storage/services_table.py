import threading

from .host_services import HostService
from common         import RWLock

class ServiceTable :
    def __init__(self, neighbors, host) :
        self.lock      = threading.Lock()
        self.table     = {}

        # Keep list of neighbors for book keeping who is left to update.
        self.neighbors = neighbors

        # Initialize row for current host and unset dirty flag, no need to 
        # advertize empty list of services.
        self.__addHost(host, host, [])
        for n in self.neighbors :
            self.table[host].done(n)


    def __str__(self) -> str:
        self.lock.acquire()
        table_str  = "=========== TABLE ===========\n"
        table_str += "\n".join([str(row) for row in self.table.values()])
        table_str += "\n=============================\n"
        self.lock.release()
        return table_str
    

    def __addHost(self, host, source, data) :
        self.table[host] = HostService(host, source, data, self.neighbors)


    def __updateHost(self, host, sender, data) :
        self.table[host].updateServices(data, sender)


    def dropHost(self, host) :
        del self.table[host]

    
    def createPacketAll(self) :
        return {k : v.createPacket() for k, v in self.table.items()}


    def createPacket(self, send_to=None) :
        # TODO: If dirty, don't send to node that made it dirty (sender of last update).
        # TODO: Check if there should be an update going to that node, need to send message if no.
        temp_table = {}

        # self.lock.acquire()

        for k, v in self.table.items() :
            if v.isDirty(send_to) :
                temp_table[k] = v.createPacket()
        
        # self.lock.release()

        return temp_table, True


    def readPacket(self, data) :
        services = data["services"]
        sender   = data["sender"]

        self.lock.acquire()

        for k, v in services.items() :
            if k not in self.table :
                self.__addHost(k, sender, v)
            
            else :
                self.__updateHost(k, sender, v)
        
        self.lock.release()


    def markNeighborUTD(self, neighbor) :
        # self.lock.acquire()

        for row in self.table.values() : row.done(neighbor)
        
        # self.lock.release()


    def addServiceToHost(self, host, data) :
        self.lock.acquire()

        self.table[host].addService(data, host)

        self.lock.release()
