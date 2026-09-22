from enum import Enum


class ProductLevel(str, Enum):
    """Only operational LS4T levels; fusion remains an L3N process."""

    L1O = "L1O"
    L2LST = "L2LST"
    L2LSCT = "L2LSCT"
    L3N = "L3N"
    L3C = "L3C"
    L4A = "L4A"

