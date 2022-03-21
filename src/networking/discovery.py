import subprocess
import ipaddress
import time

class Discovery:

    def __init__(self) -> None:
        self.getSubnet()
        self.routingTable = None


    def __shellCommand(self, command: str) -> str :
        ret = subprocess.run(command, capture_output=True, shell=True)

        return ret.stdout.decode("utf-8").strip()


    def getSubnet(self) -> None :
        command = "ip addr show dev eth0 | grep 'inet' | awk '{print $2}'"
        subnet  = self.__shellCommand(command)
        
        # Parse string and extract addresses.
        try:
            ip_addr = subnet.split("/")[0]

            # Gateways always configured to have last byte equal '1'.
            gateway = ".".join(ip_addr.split(".")[:3] + ["1"])

            # Local broker always configured to have last byte equal "2".
            broker  = ".".join(ip_addr.split(".")[:3] + ["2"])

            # Will raise ValueError exception if not actual address.
            _       = ipaddress.ip_address(ip_addr)

        except ValueError as error:
            print(error)
            return

        self.subnet  = subnet
        self.ip_addr = ip_addr
        self.gateway = gateway
        self.broker  = broker

        print(f"subnet:  {self.subnet}")
        print(f"ip_addr: {self.ip_addr}")
        print(f"gateway: {self.gateway}")
    

    def getNeighbors(self) -> None :

        # Exclude gateway IP and current device's IP from scan.
        # Exclude IPs of current device, gateway, and local broker.
        exclude_ips = ",".join([self.gateway, self.broker, self.ip_addr])
        command     = f"nmap -sn {self.subnet} --exclude {exclude_ips} | grep 'Nmap scan report'"
        ret         = self.__shellCommand(command)

        print(ret)

        # TODO: Parse IP's and update routing table.
    

    def run(self) -> None :
        while True :
            self.getNeighbors()
            time.sleep(5)


if __name__ == "__main__" :
    net = Discovery()
    # net.getNeighbors()
    net.run()