import socket
import threading
import time
import json
import os
import queue

from dataclasses import dataclass
from networking  import Graph, PacketType
from storage     import ServiceTable


class DBNode :

    @dataclass
    class QueueMessage :
        message : bytes
        send_to : str

    def __init__(self, hostname, port) -> None:
        # TODO: Need to routinely check for updates to topology.
        # TODO: Need way of updating topology in the case of node failure.

        self.host   = hostname
        self.graph  = Graph(self.host)
        self.table  = ServiceTable(self.graph.getNeighbors())
        self.queue  = queue.Queue()
        self.sport  = 8000
        self.dport  = 8001

        self.sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_recv.bind(("", self.sport))

        self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_send.bind(("", self.dport))

        
    def iotProcessReqToAdd(self, data) :
        service_name = data["topic"]
        iot_hostname = data["sender"]
        
        # Add to current host's services, will be broadcasted to neighbors.
        self.table.addServiceToHost(self.host, service_name)

        # Create response message and add to queue.
        msg = json.dumps({
            "sender" : self.host,
            "broker" : self.host + "broker",
            "type"   : PacketType.IOT_RESPONSE
        }).encode("utf-8")

        self.queue.put(
            self.QueueMessage(message=msg, send_to=iot_hostname)
        )
        

    def processPacket(self, packet) : 
        getProcessor = {
            PacketType.IOT_REQUEST_TO_PUBLISH   : lambda data : self.iotProcessReqToAdd(data),
            PacketType.IOT_REQUEST_TO_SUBSCRIBE : lambda _ : _,
            PacketType.IOT_RESPONSE             : lambda _ : _,
            PacketType.IOT_END                  : lambda _ : _,
            PacketType.DBH_NOT_DEAD             : lambda _ : _,
            PacketType.DBH_ADVERT               : lambda data : self.table.readPacket(data)
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
            
            # Send messages from queue.
            while not self.queue.empty() :
                data    = self.queue.get()
                send_to = data.send_to
                message = data.message

                self.sock_send.sendto(message, (send_to, self.sport))
                self.queue.task_done()



    def run(self) :
        t = threading.Thread(target=self.listen, daemon=True)
        t.start()

        ######## TEST CODE ########
        if self.host == "A_" :
            self.table._ServiceTable__addHost(self.host, self.host, ["temperature", "pressure"])
            self.runAdverts()
        
        elif self.host == "B_" :
            time.sleep(2)
            self.table._ServiceTable__addHost(self.host, self.host, ["baby_monitor"])
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