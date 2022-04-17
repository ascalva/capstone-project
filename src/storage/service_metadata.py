from typing import Optional, Dict, Any
from common import ServiceType


class ServiceMetadata :
    def __init__(self, name: str, type: Optional[ServiceType], cost: Optional[int]=None, params: Optional[Dict[str,Any]]=None) :
        self.name   = name
        self.type   = type
        self.cost   = cost
        self.params = params

    def __repr__(self) -> str :
        return self.name

    def __str__(self) -> str :
        return self.name

    def __hash__(self) -> int :
        return hash(str(self))

    def __eq__(self, other) -> bool:
        return (self.name == other.name) and (self.type == other.type)

    def toJSON(self) -> Dict[str, Any] :
        return self.__dict__

    @staticmethod
    def fromJSON(dict_obj: Dict[str, Any]) :
        s = ServiceMetadata("", None)

        for k, v in dict_obj.items() :
            setattr(s, k, v)

        return s