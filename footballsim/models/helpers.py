import math

from .constants import XG_CONSTANT, XG_FACTOR


def calculate_xg(strength_diff: float) -> float:
    return XG_CONSTANT * (XG_FACTOR**strength_diff)


def calculate_strength_diff(xg: float) -> float:
    """
    Calculate strength difference from XG. Inverse function of calculate_xg.
    """
    return math.log(xg / XG_CONSTANT, XG_FACTOR)
