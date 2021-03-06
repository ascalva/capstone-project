import threading
import queue
import uuid
import json

from common import ServiceType, QueueMessage, PacketType, ServiceStatus, ConsumerAction, S


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

        device = DeviceInterface(data, self.localhost, self.__queue_ptr, res_w_services=services)

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


    def notifyOfResponse(self, data) :
        if "trans_id" not in data :
            return

        res_id = data["trans_id"]

        found_match = False
        for device in self.__devices_by_service.values() :
            found_match |= device.checkTransactionID(res_id, data)
        
        # print(f"!!! Transaction IDs match: {found_match}")
        return found_match


class DeviceInterface :
    def __init__(self, data, localhost, queue_ptr, res_w_services=None) -> None:
        self.localhost = localhost
        self.s_type    = data["service_type"]
        self.iot_host  = data["sender"]
        self.trans_id  = None
        # self.topic     = data["topic"]

        # Request queue and message queue (for outgoing messages).
        self.msg_queue  = queue_ptr

        # Queue response to IOT device.
        self.sendConfirmationMsg(w_services=res_w_services)

        if self.s_type == ServiceType.SERVICE :
            self.__wait_queue = queue.Queue()
            self.__return_msg = queue.Queue(maxsize=1)
            t = threading.Thread(target=self.checkOnQueue, daemon=True)
            t.start()

    
    def checkTransactionID(self, res_id, data) :
        if not isinstance(res_id, uuid.UUID) :
            res_id = uuid.UUID(res_id)
        
        if self.trans_id == res_id :
            self.__return_msg.put(data)
            return True
        
        return False


    def requestToConnect(self, data) :
        requestee = data["sender"]
        trans_id  = uuid.uuid4()
        msg = {
            "sender"   : self.localhost,
            "type"     : PacketType.IOT_RESPONSE,
            "trans_id" : trans_id.hex
        }

        if self.s_type == ServiceType.SERVICE :
            msg["broker"] = self.localhost
            msg["status"] = ServiceStatus.BUSY

            self.__wait_queue.put(
                (requestee, data)
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
            
            # Get the next request for service.
            requestee, params = self.__wait_queue.get()
            self.trans_id = uuid.uuid4()

            # Create and queue message for IoT device.
            msg = json.dumps({
                "sender"   : self.localhost,
                "type"     : PacketType.IOT_REQUEST,
                "trans_id" : self.trans_id.hex,
                "params"   : params
            }).encode(S.ENCODING)

            self.msg_queue.put(
                QueueMessage(message=msg, send_to=self.iot_host, trans_id=self.trans_id)
            )

            # Wait/Block until we get response from IoT device.
            iot_res = self.__return_msg.get()
            output  = iot_res["output"]

            # Create response with output for device that made the request.
            msg = json.dumps({
                "sender" : self.localhost,
                "type"   : PacketType.IOT_RESPONSE,
                "status" : ServiceStatus.DONE,
                "output" : output
            }).encode(S.ENCODING)

            self.msg_queue.put(
                QueueMessage(message=msg, send_to=requestee, trans_id=self.trans_id)
            )

            self.__wait_queue.task_done()
            self.__return_msg.task_done()
    

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
