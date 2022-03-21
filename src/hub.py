import socket
import threading
import time
import json
import os

from networking import Graph
from storage    import ServiceTable
from common     import PacketType


class DBNode :

    def __init__(self, hostname, port) -> None:
        # TODO: Need to routinely check for updates to topology.
        # TODO: Need way of updating topology in the case of node failure.

        self.graph  = Graph(hostname)
        self.host   = hostname
        self.table  = ServiceTable(self.graph.getNeighbors())
        self.sport  = 8000
        self.dport  = 8001

        self.sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_recv.bind(("", self.sport))

        self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_send.bind(("", self.dport))

        
    def processPacket(self, packet) : 
        getProcessor = {
            PacketType.IOT_REQUEST  : lambda _ : _,
            PacketType.IOT_RESPONSE : lambda _ : _,
            PacketType.IOT_END      : lambda _ : _,
            PacketType.DBH_NOT_DEAD : lambda _ : _,
            PacketType.DBH_ADVERT   : lambda data : self.table.readPacket(data)
        }

        data = json.loads(packet.decode("utf-8"))
        getProcessor[data["type"]](data)


    def listen(self) :
        size = 1024

        while True :
            try :
                data = self.sock_recv.recv(size)
                self.processPacket(data)

            except socket.error as error :
                print(error)
            
            # Error parsing JSON data.
            except ValueError as error :
                print(error)


    def prepareAdPacket(self, send_to) :
        services, updateExists = self.table.createPacket(send_to)

        message = {
            "type"     : PacketType.DBH_ADVERT,
            "services" : services,
            "sender"   : self.host,
            "message"  : f"hello from {self.host}"
        }

        # Don't send ads if no updates avaiable for neighbor, send still alive message instead.
        if not updateExists :
            message["type"] = PacketType.DBH_NOT_DEAD

        return bytes(json.dumps(message), "utf-8")


    def runAdverts(self) :
        # TODO: If we fail to send to a node, might need to be removed from neighbors/graph/everything.
        while True :
            time.sleep(5)

            for neighbor in self.graph.getNeighbors() :

                # Prepare message, send, and update tracking to avoid redundant
                # data replication/transmission.
                message = self.prepareAdPacket(neighbor)
                self.sock_send.sendto(message, (neighbor, self.sport))
                self.table.markNeighborUTD(neighbor)


    def run(self) :
        t = threading.Thread(target=self.listen)
        t.start()

        ######## TEST CODE ########
        if self.host == "A_" :
            self.table.addHost(self.host, self.host, ["temperature", "pressure"])
            self.runAdverts()
        
        elif self.host == "B_" :
            time.sleep(2)
            self.table.addHost(self.host, self.host, ["baby_monitor"])
            self.runAdverts()

        else :
            while True :
                print("=========== TABLE ===========")
                print(self.table)
                print("=============================\n")

                time.sleep(2)


if __name__ == "__main__" :
    hostname = os.environ.get("HOSTNAME")
    port     = 8080

    g = DBNode(hostname, port)
    g.run()