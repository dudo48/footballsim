import random
from functools import cached_property
from typing import Annotated

from annotated_types import Len, Predicate
from more_itertools import circular_shifts, distribute, nth
from pydantic import BaseModel, ConfigDict, PositiveInt, computed_field

from .match import Match
from .round import Round
from .standings import Standings
from .team import Team


class League(BaseModel):
    model_config = ConfigDict(frozen=True)

    teams: Annotated[
        list[Team], Len(min_length=2), Predicate(lambda t: len(t) % 2 == 0)
    ]
    iterations: PositiveInt = 2

    @computed_field
    @cached_property
    def rounds(self) -> list[Round]:
        def create_round(teams: list[Team]) -> Round:
            matches: list[Match] = []
            for t1, t2 in distribute(len(teams) // 2, teams):
                match = Match(home_team=t1, away_team=t2)
                if random.random() < 0.5:
                    match = match.get_away_match()
                matches.append(match)
            return Round(matches=matches)

        # create first iteration
        teams = [t for t in self.teams]
        random.shuffle(teams)
        rounds = [
            create_round([teams[0]] + list(shifts))
            for shifts in circular_shifts(teams[1:])
        ]

        # create all next iterations with alternating home / away teams setting
        previous_iteration = [r for r in rounds]
        next_iteration: list[Round] = []
        for _ in range(self.iterations - 1):
            for round in previous_iteration:
                next_iteration.append(round.get_away_round())
            rounds.extend(next_iteration)
            previous_iteration = next_iteration
            next_iteration = []

        return rounds

    @computed_field
    @cached_property
    def standings(self) -> list[Standings]:
        return [Standings.from_teams(self.teams)]

    def __str__(self) -> str:
        result = ""
        for i, round in enumerate(self.rounds):
            result += f"{nth(self.standings, i, default="")}\n\n"
            result += f"ROUND {i + 1}\n{round}\n\n"
        result += str(nth(self.standings, len(self.rounds), default=""))
        return result
