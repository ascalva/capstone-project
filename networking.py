import subprocess
import ipaddress
import time

class Networking:

    def __init__(self) -> None:
        pass

    def getSubnet(self) -> None :
        command = "ip addr show dev eth0 | grep 'inet' | awk '{print $2}'"
        out     = subprocess.run(command, capture_output=True, shell=True)
        
        # Parse string and extract addresses.
        try:
            subnet  = out.stdout.decode("utf-8").strip()
            ip_addr = subnet.split("/")[0]

            # Gateways always configured to have last byte equal '1'.
            gateway = ".".join(ip_addr.split(".")[:3] + ["1"])

            # Will raise ValueError exception if not actual address.
            _       = ipaddress.ip_address(ip_addr)

        except ValueError as error:
            print(error)
            return

        self.subnet  = subnet
        self.ip_addr = ip_addr
        self.gateway = gateway

        print(f"subnet:  {self.subnet}")
        print(f"ip_addr: {self.ip_addr}")
        print(f"gateway: {self.gateway}")
    

    def getNeighbors(self) -> None :

        # Exclude gateway IP and current device's IP from scan.
        exclude_ips = ",".join([self.gateway, self.ip_addr])
        command     = f"nmap -sn {self.subnet} --exclude {exclude_ips} | grep 'Nmap scan report'"
        ret         = subprocess.run(command, capture_output=True, shell=True)
        
        parse_out   = ret.stdout.decode("utf-8").strip()
        print(parse_out)
    

    def stall(self) -> None :
        while True :
            time.sleep(5)


if __name__ == "__main__" :
    net = Networking()
    net.getSubnet()
    net.getNeighbors()
    net.stall()