import os
import time
from iot import IOT_Factory

if __name__ == "__main__" :
    topic    = os.environ.get("TOPIC", "")
    iot_type = os.environ.get("IOT_TYPE", "sensor")
    
    # Wait before creating IOT device.
    sleep_time = int(os.environ.get("SLEEP", "0"))
    time.sleep(sleep_time + 20)

    # Get IOT device and start.
    IOT_Factory()[iot_type](topic=topic)
