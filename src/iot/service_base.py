from abc import ABC, abstractmethod

class ServiceBase(ABC) :

    @abstractmethod
    def executeService(self) :
        pass

