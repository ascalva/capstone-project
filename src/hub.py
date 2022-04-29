import socket
import threading
import time
import json
import os
import queue
import uuid

from networking  import Graph
from common      import PacketType, QueueMessage, ServiceType, S
from storage     import ServiceTable, IOTHandler


class DBNode :

    def __init__(self, hostname, verbose=False) -> None:
        # TODO: Need to routinely check for updates to topology.
        # TODO: Need way of updating topology in the case of node failure.

        self.host    = hostname
        self.verbose = verbose
        self.queue   = queue.Queue()
        self.graph   = Graph(self.host)
        self.table   = ServiceTable(self.graph.getNeighbors(), self.host)
        self.iot_db  = IOTHandler(self.host, self.queue)
        
        # Not ideal, but pass in function to get most up-to-date list of services.
        # This is used when handling consumer requests.
        self.iot_db.setServiceFuncPtr(self.table.createPacketAll)

        # Setup sockets for communication.
        self.sport   = S.SOURCE_PORT
        self.dport   = S.DESTINATION_PORT

        self.sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_recv.bind(("", self.sport))

        self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_send.bind(("", self.dport))

        
    def iotProcessReq(self, data) :

        # If IOT device is service or sensor, add to current host's 
        # services (will be broadcasted to neighbors).
        if data["service_type"] != ServiceType.CONSUMER :
            self.table.addServiceToHost(self.host, data)

        self.iot_db.handleRequest(data)
        

    def iotProcessRes(self, data) :
        self.iot_db.notifyOfResponse(data)

    
    def dbhProcessStillAlive(self, data) :
        sender = data["sender"]
        # print(f"Node {sender} is still alive.")
        

    def processPacket(self, packet) : 
        getProcessor = {
            PacketType.IOT_REQUEST   : lambda data : self.iotProcessReq(data),
            PacketType.IOT_RESPONSE  : lambda data : self.iotProcessRes(data),
            PacketType.DBH_NOT_DEAD  : lambda data : self.dbhProcessStillAlive(data),
            PacketType.DBH_ADVERT    : lambda data : self.table.readPacket(data)
        }

        data = json.loads(packet.decode(S.ENCODING))
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
                }).encode(S.ENCODING)

                self.queue.put(
                    QueueMessage(message=msg, send_to=neighbor, trans_id=trans_id)
                )


    def listen(self) :
        print(f"## Started listening, ready to accept connections!")
        while True :
            try :
                data = self.sock_recv.recv(S.PACKET_SIZE)
                self.processPacket(data)

            except socket.error as error :
                print(error)
            
            # Error parsing JSON data.
            except ValueError as error :
                print(error)


    def runAdverts(self) :
        # TODO: If we fail to send to a node, might need to be removed 
        # from neighbors/graph/everything.
        while True :
            time.sleep(2)
            if self.verbose : print(self.table)

            for neighbor in self.graph.getNeighbors() :

                # Start transaction, don't release until complete.
                self.table.lock.acquire()

                # Prepare message, send, and update tracking to avoid redundant
                # data replication/transmission.
                services, _ = self.table.createPacket(neighbor)
                trans_id    = uuid.uuid4()

                message = json.dumps({
                    "type"     : PacketType.DBH_ADVERT,
                    "services" : services,
                    "sender"   : self.host,
                    "message"  : f"hello from {self.host}",
                    "trans_id" : trans_id.hex
                }).encode(S.ENCODING)

                # self.sock_send.sendto(message, (neighbor, self.sport))
                self.queue.put(
                    QueueMessage(message=message, send_to=neighbor, trans_id=trans_id)
                )

                self.table.markNeighborUTD(neighbor)
                self.table.lock.release()
            

    def sendQueueMessages(self) :
        while True :
            data    = self.queue.get()
            send_to = data.send_to
            message = data.message

            try :
                self.sock_send.sendto(message, (send_to, self.sport))

            except socket.error as e :
                print(f"Error sending message from queue: {data}")

            self.queue.task_done()


    def run(self) :
        
        # Create threads for listening, sending service ads, and sending still alive messages.
        thread_listen      = threading.Thread(target=self.listen,         daemon=True)
        thread_still_alive = threading.Thread(target=self.sendStillAlive, daemon=True)
        thread_send_ads    = threading.Thread(target=self.runAdverts,     daemon=True)

        thread_listen.start()
        thread_still_alive.start()
        thread_send_ads.start()

        # Start reading queue and sending messages.
        self.sendQueueMessages()


if __name__ == "__main__" :
    hostname = os.environ.get("HOSTNAME")
    verbose  = os.environ.get("VERBOSE_TABLE", "false") == "true"

    g = DBNode(hostname, verbose=verbose)
    g.run()