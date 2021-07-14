from typing import Dict
from abc import ABC, abstractmethod

from models import Target, TargetPortfolio

class Broker(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def account_value(self) -> float:
        pass

    @abstractmethod
    def cash_available(self) -> float:
        pass

    @abstractmethod
    def positions(self):
        pass

    @abstractmethod
    def order(self):
        pass

    @abstractmethod
    def order_target(self, target: Target):
        pass

    @abstractmethod
    def order_target_portfolio(self, allocations: TargetPortfolio):
        pass
