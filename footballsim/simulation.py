import math
import random
from functools import singledispatch
from typing import Any, overload

from models.league import League
from models.match import Match
from models.match_result import MatchResult, Result

from models.fixture import Fixture


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
def _simulate(_: Any) -> Any: ...


@_simulate.register
def _(match: Match) -> Match:
    full_time = Result(
        home_goals=score_goals(match.home_xg),
        away_goals=score_goals(match.away_xg),
    )
    result = MatchResult(full_time=full_time)
    return match.model_copy(update={"result": result})


@_simulate.register
def _(fixture: Fixture) -> Fixture:
    return fixture.model_copy(
        update={"matches": [simulate(m) for m in fixture.matches]}
    )


@_simulate.register
def _(league: League) -> League:
    # recompute the cached_property
    standings = league.standings[:1]
    fixtures: list[Fixture] = []
    for fixture in league.fixtures:
        simulated_fixture = simulate(fixture)
        fixtures.append(simulated_fixture)
        standings.append(standings[-1].update_from_matches(simulated_fixture.matches))

    return league.model_copy(update={"fixtures": fixtures, "standings": standings})


@overload
def simulate(model: Match) -> Match: ...


@overload
def simulate(model: Fixture) -> Fixture: ...


@overload
def simulate(model: League) -> League: ...


def simulate(model: Any):
    """Takes a simulate-able model and returns the simulated version of it"""
    return _simulate(model)
