import uuid
from dataclasses import dataclass

@dataclass
class QueueMessage :
    message  : bytes
    send_to  : str
    trans_id : uuid.UUID
