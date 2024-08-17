import random
from functools import cached_property
from typing import Annotated

from annotated_types import Len
from more_itertools import circular_shifts, flatten, interleave_longest, padded
from pydantic import BaseModel, ConfigDict, PositiveInt, computed_field

from .fixture import Fixture
from .match import Match
from .standings import Standings
from .team import Team


class League(BaseModel):
    model_config = ConfigDict(frozen=True)

    teams: Annotated[list[Team], Len(min_length=2)]
    iterations: PositiveInt = 2

    @computed_field
    @cached_property
    def fixtures(self) -> list[Fixture]:
        # create first iteration
        # add a dummy team if number of teams is not even
        teams = list(padded(self.teams, n=2, fillvalue=None, next_multiple=True))
        random.shuffle(teams)
        fixtures = [
            Fixture.from_teams(
                [teams[0]] + list(shift), home_or_away=True, sort_matches=True
            )
            for shift in circular_shifts(teams[1:])
        ]

        # create all next iterations with alternating home / away teams setting
        previous_iteration = fixtures.copy()
        for _ in range(self.iterations - 1):
            next_iteration = list(
                map(lambda f: f.get_away_fixture(), previous_iteration)
            )
            fixtures.extend(next_iteration)
            previous_iteration = next_iteration

        return fixtures

    @computed_field
    @cached_property
    def standings(self) -> list[Standings]:
        return [Standings.from_teams(self.teams)]

    @property
    def matches(self) -> list[Match]:
        return list(flatten(f.matches for f in self.fixtures))

    def __str__(self) -> str:
        return "\n\n".join(
            interleave_longest(
                (str(s) for s in self.standings),
                (f"FIXTURE {i + 1}" for i in range(len(self.fixtures))),
                (str(f) for f in self.fixtures),
            )
        )
