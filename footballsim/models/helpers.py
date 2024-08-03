import math
from typing import TYPE_CHECKING

from .constants import XG_CONSTANT, XG_FACTOR

if TYPE_CHECKING:
    from .standings import TeamStanding


def calculate_xg(strength_diff: float) -> float:
    return XG_CONSTANT * (XG_FACTOR**strength_diff)


def calculate_strength_diff(xg: float) -> float:
    """
    Calculate strength difference from XG. Inverse function of calculate_xg.
    """

    return math.log(xg / XG_CONSTANT, XG_FACTOR)


def default_tie_breakers(standing: "TeamStanding") -> tuple[int, ...]:
    return standing.points, standing.goals_difference, standing.goals_scored
