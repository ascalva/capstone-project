# Metadata and configuration for a service.

NAME  = "A_iot_1"
TOPIC = "temperature"
SLEEP = 0

SERVICE_ARGS    = ["values"]
SERVICE_ARG_NUM = 1

def service(params) : 
    values = params[SERVICE_ARGS[0]]

    return sum(values) / len(values)
