import os

def import_config_file(hostname) :
    config_path = "src.config.{hostname}"

    try :
        m = __import__(config_path)
    
    except ModuleNotFoundError as e :
        print(f"!!! Cound not find module {config_path}")
        print(e)
