import math
import random
from functools import singledispatch

from models.match import Match
from models.match_result import MatchResult, Result


def poisson(n: float) -> int:
    """Knuth's algorithm."""
    limit = math.exp(-n)
    product = random.random()
    result = 0
    while product >= limit:
        product *= random.random()
        result += 1
    return result


def score_goals(xg: float) -> int:
    return poisson(xg)


@singledispatch
def simulate(match: Match) -> Match:
    full_time = Result(
        home_goals=score_goals(match.home_xg),
        away_goals=score_goals(match.away_xg),
    )
    result = MatchResult(full_time=full_time)
    return match.model_copy(update={"result": result})
