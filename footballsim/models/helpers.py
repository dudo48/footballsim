import math

from .constants import XG_CONSTANT, XG_FACTOR


def calculate_xg(difference: float) -> float:
    return XG_CONSTANT * (XG_FACTOR**difference)


def calculate_difference(xg: float) -> float:
    """
    Calculate strength difference from XG. Inverse function of calculate_xg.
    """

    return math.log(xg / XG_CONSTANT, XG_FACTOR)
