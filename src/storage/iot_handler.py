import threading
import queue
import uuid
import json

from common import ServiceType, QueueMessage, PacketType, ServiceStatus, ConsumerAction


class IOTHandler :
    def __init__(self, localhost, queue_ptr) -> None:
        self.lock        = threading.Lock()
        self.localhost   = localhost
        self.__queue_ptr = queue_ptr

        # NOTE: devices_by_hostname is a superset of devices_by_services.
        #       The only case when a IoT host's topic isn't added to services
        #       but is added to hostnames is when device is a consumer. In
        #       this case, the device isn't offering a service/sensor data.
        self.__devices_by_hostname = {}
        self.__devices_by_service  = {}
    
    
    def setServiceFuncPtr(self, ptr) :
        self.__get_services = ptr


    def handleRequest(self, data) :
        service_type = data["service_type"]

        # If request is from remote consumer, don't add device, only add to service queue.
        if ("consumer_type" in data) and (data["consumer_type"] == ConsumerAction.REQUEST) :
            self.requestToAccess(data)
            return
        
        # Add local device, and send list of services if consumer type.
        self.newDevice(data, send_service_list=(service_type == ServiceType.CONSUMER))
        

    def newDevice(self, data, send_service_list=False) :
        self.lock.acquire()

        host     = data["sender"]
        services = None

        # Don't bother adding if hostname of device already exists.
        # TODO: Might need to change if host can have multiple topics.
        if self.exists(host) : return
        
        # If true, we will send a list of services available with the response message to device.
        if send_service_list :
            services = self.__get_services()

        device = IOTDeviceInterface(data, self.localhost, self.__queue_ptr, res_w_services=services)

        # If device is a consumer, only add reference by hostname.
        # Otherwise, also add reference by topic/service name.
        if data["service_type"] != ServiceType.CONSUMER :
            topic = data["topic"]
            self.__devices_by_service[topic] = device
        self.__devices_by_hostname[host] = device

        self.lock.release()
    

    def requestToAccess(self, data) :
        self.lock.acquire()

        if self.exists(topic := data["topic"]) :
            self.__devices_by_service[topic].requestToConnect(data)
        
        else :
            # TODO: Send error message back to sender using queue.
            # self.serviceNotFoundMsg(data)
            pass

        self.lock.release()
    

    def serviceNotFoundMsg(self, data) :
        trans_id = uuid.uuid4()
        msg = json.dumps({
            "sender"   : self.localhost,
            "type"     : PacketType.IOT_RESPONSE,
            "trans_id" : trans_id.hex
        }).encode("utf-8")

        self.__queue_ptr.put(
            QueueMessage(
                message  = json.dumps(msg).encode("utf-8"), 
                send_to  = data["sender"], 
                trans_id = trans_id)
        )
        

    def exists(self, host) :
        return (host in self.__devices_by_hostname) \
            or (host in self.__devices_by_service)



class IOTDeviceInterface :
    def __init__(self, data, localhost, queue_ptr, res_w_services=None) -> None:
        self.localhost = localhost
        self.s_type    = data["service_type"]
        self.iot_host  = data["sender"]
        # self.topic     = data["topic"]

        # Request queue and message queue (for outgoing messages).
        # self.wait_queue = queue.Queue()
        self.msg_queue  = queue_ptr

        # Queue response to IOT device.
        self.sendConfirmationMsg(w_services=res_w_services)

        # TODO: Need to create thread that checks queue for waiting hosts.
        # TODO: Don't need thread if service is of sensor type.
        if self.s_type == ServiceType.SERVICE :
            self.wait_queue = queue.Queue()
            t = threading.Thread(target=self.checkOnQueue, daemon=True)
            # t.start()


    def requestToConnect(self, requestee, params = None) :
        trans_id = uuid.uuid4()
        msg = {
            "sender"   : self.localhost,
            "type"     : PacketType.IOT_RESPONSE,
            "trans_id" : trans_id.hex
        }

        if self.s_type == ServiceType.SERVICE :
            msg["broker"] = self.localhost
            msg["status"] = ServiceStatus.BUSY

            self.wait_queue.put(
                (requestee, params)
            )

        else :
            msg["broker"] = self.localhost + "broker"
            msg["status"] = ServiceStatus.READY

        self.msg_queue.put(
            QueueMessage(
                message  = json.dumps(msg).encode("utf-8"), 
                send_to  = requestee, 
                trans_id = trans_id)
        )


    def checkOnQueue(self) :
        while True :
            # TODO: Check with iot device that it's ready
            requestee, params = self.msg_queue.get()
    

    # TODO: Move into thread as first thing to do.
    def sendConfirmationMsg(self, w_services=None) :
        trans_id = uuid.uuid4()
        msg = json.dumps({
            "sender"   : self.localhost,
            "broker"   : self.localhost + "broker",
            "type"     : PacketType.IOT_RESPONSE,
            "trans_id" : trans_id.hex,
            "services" : w_services
        }).encode("utf-8")
        print(f"Received message from {self.iot_host}")
        print(" . |-> Message has been queued! ")

        self.msg_queue.put(
            QueueMessage(message=msg, send_to=self.iot_host, trans_id=trans_id)
        )
