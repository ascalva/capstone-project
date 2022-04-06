import threading
import queue
from networking import ServiceType, QueueMessage

class IOTHandler :
    def __init__(self, data, localhost, queue_ptr) -> None:
        self.iot_devices = {}
        self.lock        = threading.Lock()
        self.localhost   = localhost
        self.queue_ptr   = queue_ptr


    def newDevice(self, data) :
        self.lock.acquire()

        host = data["sender"]
        self.iot_devices[host] = IOTDeviceInterface(data, self.localhost, self.queue_ptr)

        self.lock.release()
    
    
    def updateAsFree(self, iot_host) :
        pass
    

class IOTDeviceInterface :
    def __init__(self, data, localhost, queue_ptr) -> None:
        self.localhost = localhost
        self.iot_host  = data["sender"]
        self.topic     = data["topic"]
        self.s_type    = data["service_type"]
        _              = data["type"]

        # Request queue and message queue (for outgoing messages).
        self.wait_queue = queue.Queue()
        self.msg_queue  = queue_ptr

        # TODO: Need to create thread that checks queue for waiting hosts.
        # TODO: Don't need thread if service is of sensor type.
        if self.s_type == ServiceType.BY_REQUEST :
            t = threading.Thread(target=self.checkOnQueue, daemon=True)
            # t.start()


    def requestToConnect(self, requestee, params = None) :
        if self.s_type == ServiceType.BY_REQUEST :
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