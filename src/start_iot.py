import os
from iot import IOT_Factory

if __name__ == "__main__" :
    topic    = os.environ.get("TOPIC", "")
    iot_type = os.environ.get("IOT_TYPE", "sensor")

    # Get IOT device and start.
    IOT_Factory()[iot_type](topic=topic)
