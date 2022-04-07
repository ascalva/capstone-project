import threading
import queue
import uuid
import json

from common import ServiceType, QueueMessage, PacketType


class IOTHandler :
    def __init__(self, localhost, queue_ptr) -> None:
        self.lock        = threading.Lock()
        self.localhost   = localhost
        self.__queue_ptr = queue_ptr
        self.__devices   = {}


    def handleRequest(self, data) :
        service_type = data["service_type"]

        if service_type in [ServiceType.SENSOR, ServiceType.SERVICE] :
            self.newDevice(data)
        
        elif service_type == ServiceType.CONSUMER :
            self.requestToAccess(data)
        
        else :
            # TODO: Figure out what to do in this scenario.
            pass


    def newDevice(self, data) :
        self.lock.acquire()

        host = data["sender"]
        self.__devices[host] = IOTDeviceInterface(data, self.localhost, self.__queue_ptr)

        self.lock.release()
    

    def requestToAccess(self, data) :
        self.lock.acquire()

        host = data["sender"]
        self.__devices[host].requestToConnect(data)

        self.lock.release()
    

    def isFree(self, host) :
        pass
    

class IOTDeviceInterface :
    def __init__(self, data, localhost, queue_ptr) -> None:
        self.localhost = localhost
        self.iot_host  = data["sender"]
        self.topic     = data["topic"]
        self.s_type    = data["service_type"]

        # Request queue and message queue (for outgoing messages).
        self.wait_queue = queue.Queue()
        self.msg_queue  = queue_ptr

        # Queue response to IOT device.
        self.sendConfirmationMsg()

        # TODO: Need to create thread that checks queue for waiting hosts.
        # TODO: Don't need thread if service is of sensor type.
        if self.s_type == ServiceType.SERVICE :
            t = threading.Thread(target=self.checkOnQueue, daemon=True)
            # t.start()


    def requestToConnect(self, requestee, params = None) :
        if self.s_type == ServiceType.SERVICE :
            # TODO: Add to queue 
            # TODO: Respond with wait message.
            pass
        

        else :
            # Respond with with broker msg.
            pass


    def checkOnQueue(self) :
        while True :
            # TODO: Check with iot device that it's ready
            pass
    

    # TODO: Move into thread as first thing to do.
    def sendConfirmationMsg(self) :
        trans_id = uuid.uuid4()
        msg = json.dumps({
            "sender"   : self.localhost,
            "broker"   : self.localhost + "broker",
            "type"     : PacketType.IOT_RESPONSE,
            "trans_id" : trans_id.hex
        }).encode("utf-8")
        print(f"Received message from {self.iot_host}")
        print(" . |-> Message has been queued! ")

        self.msg_queue.put(
            QueueMessage(message=msg, send_to=self.iot_host, trans_id=trans_id)
        )