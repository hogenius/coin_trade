from abc import ABC, abstractmethod #추상클래스
from typing import Protocol        #인터페이스
from singletone import SingletonInstane

class DockManager(SingletonInstane):
    def __init__(self):
        self.DicDataInfo = {}

    def AddDock(self, dataInfo):
        if dataInfo.name in self.DicDataInfo:
            print(f"Already DockInfo : {dataInfo.name}")
            return False
        else:
            self.DicDataInfo[dataInfo.name] = dataInfo
            return True

    def GetDock(self, name):
        if name in self.DicDataInfo:
            return self.DicDataInfo[name]
        else:
            print(f"no have DockInfo : {name}")
            return None

    def Remove(self, name):
        if name in self.DicDataInfo:
            del self.DicDataInfo[name]
            return True
        else:
            return False

class DockInfo(ABC):
    def __init__(self, name):
        self.name = name
        DockManager.Instance().AddDock(self)

class CoinInfo(DockInfo):
    @abstractmethod
    def BuyCoin(self, data):
        pass
