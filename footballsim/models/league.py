import random
from functools import cached_property
from typing import Annotated

from annotated_types import Len
from more_itertools import always_reversible, circular_shifts, divide, nth, padded
from pydantic import BaseModel, ConfigDict, PositiveInt, computed_field

from .fixture import Fixture
from .match import Match
from .standings import Standings
from .team import Team


class League(BaseModel):
    model_config = ConfigDict(frozen=True)

    teams: Annotated[list[Team], Len(min_length=2)]
    iterations: PositiveInt = 2

    @staticmethod
    def create_fixture(teams: list[Team | None]) -> Fixture:
        matches: list[Match] = []
        half_1, half_2 = divide(2, teams)
        for t1, t2 in zip(half_1, always_reversible(half_2)):
            if not t1 or not t2:
                continue
            match = Match(home_team=t1, away_team=t2)
            if random.random() < 0.5:
                match = match.get_away_match()
            matches.append(match)
        return Fixture(matches=matches)

    @computed_field
    @cached_property
    def fixtures(self) -> list[Fixture]:
        # create first iteration
        # add a dummy team if number of teams is not even
        teams = list(padded(self.teams, n=2, fillvalue=None, next_multiple=True))
        random.shuffle(teams)
        fixtures = [
            League.create_fixture([teams[0]] + list(shifts))
            for shifts in circular_shifts(teams[1:])
        ]

        # create all next iterations with alternating home / away teams setting
        previous_iteration = fixtures
        for _ in range(self.iterations - 1):
            next_iteration = [f.get_away_fixture() for f in previous_iteration]
            fixtures.extend(next_iteration)
            previous_iteration = next_iteration

        return fixtures

    @computed_field
    @cached_property
    def standings(self) -> list[Standings]:
        return [Standings.from_teams(self.teams)]

    def __str__(self) -> str:
        result = ""
        for i, fixture in enumerate(self.fixtures):
            result += f"{nth(self.standings, i, default="")}\n\n"
            result += f"FIXTURE {i + 1}\n{fixture}\n\n"
        result += str(nth(self.standings, len(self.fixtures), default=""))
        return result
