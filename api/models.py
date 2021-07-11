from typing import Dict
from enum import Enum

from pydantic import BaseModel


class Basis(str, Enum):
    PERCENT = "PERCENT",
    NOMINAL = "NOMINAL"

class Target(BaseModel):
    basis: Basis
    allocation: Dict[str, float]

class TargetPortfolio(BaseModel):
    basis: Basis
    allocations: Dict[str, float]
