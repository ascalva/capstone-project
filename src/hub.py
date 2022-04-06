import socket
import threading
import time
import json
import os
import queue
import uuid

from dataclasses import dataclass
from networking  import Graph
from common      import PacketType, QueueMessage
from storage     import ServiceTable


class DBNode :

    def __init__(self, hostname, verbose=False) -> None:
        # TODO: Need to routinely check for updates to topology.
        # TODO: Need way of updating topology in the case of node failure.

        self.host    = hostname
        self.verbose = verbose
        self.graph   = Graph(self.host)
        self.table   = ServiceTable(self.graph.getNeighbors(), self.host)
        self.queue   = queue.Queue()
        self.sport   = 8000
        self.dport   = 8001

        # TODO: Switch to using TCP sockets instead of UDP sockets.
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
        trans_id = uuid.uuid4()
        msg = json.dumps({
            "sender"   : self.host,
            "broker"   : self.host + "broker",
            "type"     : PacketType.IOT_RESPONSE,
            "trans_id" : trans_id.hex
        }).encode("utf-8")
        print(f"Received message from {iot_hostname}")
        print(" . |-> Message has been queued! ")

        self.queue.put(
            QueueMessage(message=msg, send_to=iot_hostname, trans_id=trans_id)
        )
    
    def iotProcessReqToSub(self, data) :
        iot_hostname = data["sender"]

        services = {"host" : ["service_1"]}
        trans_id = uuid.uuid4()
        msg = json.dumps({
            "sender"   : self.host,
            "broker"   : self.host + "broker",
            "type"     : PacketType.IOT_RESPONSE,
            "trans_id" : trans_id.hex,
            "services" : services
        }).encode("utf-8")

        self.queue.put(
            QueueMessage(message=msg, send_to=iot_hostname, trans_id=trans_id)
        )

    
    def dbhProcessStillAlive(self, data) :
        sender = data["sender"]
        # print(f"Node {sender} is still alive.")
        

    def processPacket(self, packet) : 
        getProcessor = {
            PacketType.IOT_REQUEST_TO_PUBLISH   : lambda data : self.iotProcessReqToAdd(data),
            PacketType.IOT_REQUEST_TO_SUBSCRIBE : lambda data : self.iotProcessReqToSub(data),
            PacketType.IOT_RESPONSE             : lambda _ : _,
            PacketType.IOT_END                  : lambda _ : _,
            PacketType.DBH_NOT_DEAD             : lambda data : self.dbhProcessStillAlive(data),
            PacketType.DBH_ADVERT               : lambda data : self.table.readPacket(data)
        }

        data = json.loads(packet.decode("utf-8"))
        if self.verbose :
            print(f"Recieved from {data['sender']} the packet:")
            print(f"\t|-> Message type : {PacketType(data['type'])}")

            if "services" in data :
                print(f"\t|-> Service updates : {data['services']}")
            print()

        getProcessor[data["type"]](data)


    def sendStillAlive(self) :
        while True :
            time.sleep(10)

            for neighbor in self.graph.getNeighbors() :

                # Create still_alive message for every neighbor and add to queue.
                trans_id = uuid.uuid4()
                msg = json.dumps({
                    "sender" : self.host,
                    "type"   : PacketType.DBH_NOT_DEAD,
                    "trans_id" : trans_id.hex
                }).encode("utf-8")

                self.queue.put(
                    QueueMessage(message=msg, send_to=neighbor, trans_id=trans_id)
                )


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
            "message"  : f"hello from {self.host}",
            "trans_id" : uuid.uuid4().hex
        }

        # Don't send ads if no updates avaiable for neighbor, send still alive message instead.
        if not updateExists :
            message["type"] = PacketType.DBH_NOT_DEAD

        return bytes(json.dumps(message), "utf-8")


    def runAdverts(self) :
        # TODO: If we fail to send to a node, might need to be removed from neighbors/graph/everything.
        while True :
            time.sleep(5)
            if self.verbose : print(self.table)

            for neighbor in self.graph.getNeighbors() :

                try :
                    # Start transaction, don't release until complete.
                    self.table.lock.acquire()

                    # Prepare message, send, and update tracking to avoid redundant
                    # data replication/transmission.
                    message = self.prepareAdPacket(neighbor)
                    self.sock_send.sendto(message, (neighbor, self.sport))
                    self.table.markNeighborUTD(neighbor)

                except socket.error as e :
                    print(f"Error sending ad to {neighbor}: {e}")
                
                finally :
                    self.table.lock.release()
            
            # Send messages from queue.
            while not self.queue.empty() :
                data    = self.queue.get()
                send_to = data.send_to
                message = data.message

                try :
                    self.sock_send.sendto(message, (send_to, self.sport))
                
                except socket.error as e :
                    print(f"Error sending message from queue: {data}")

                self.queue.task_done()
    

    def run(self) :
        
        # Create thread for listening and thread of sending still_alive messages.
        thread_listen      = threading.Thread(target=self.listen,         daemon=True)
        thread_still_alive = threading.Thread(target=self.sendStillAlive, daemon=True)
        thread_listen.start()
        thread_still_alive.start()

        ######## TEST CODE ########
        if self.host == "A_" :
            # self.table._ServiceTable__addHost(self.host, self.host, ["pressure"])
            pass
        
        elif self.host == "B_" :
            # self.table._ServiceTable__addHost(self.host, self.host, ["baby_monitor"])
            pass

        self.runAdverts()


if __name__ == "__main__" :
    hostname = os.environ.get("HOSTNAME")
    verbose  = os.environ.get("VERBOSE_TABLE", "false") == "true"

    g = DBNode(hostname, verbose=verbose)
    g.run()