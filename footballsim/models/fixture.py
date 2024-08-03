import random
from typing import Annotated

from annotated_types import Len
from more_itertools import always_reversible, divide
from pydantic import BaseModel, ConfigDict
from tabulate import tabulate

from .match import Match
from .team import Team


class Fixture(BaseModel):
    """Encapsulates a fixture of matches"""

    model_config = ConfigDict(frozen=True)

    matches: Annotated[list[Match], Len(min_length=1)]

    @classmethod
    def from_teams(
        cls,
        teams: list[Team | None],
        home_or_away: bool = False,
        shuffle_matches: bool = False,
    ) -> "Fixture":
        """Create matches fixture from a list of teams, where the ith team plays with the n - i team, where n is the number of teams.
        the list of teams might include None values which indicate a 'bye' contestant"""
        matches: list[Match] = []
        half_1, half_2 = divide(2, teams)
        for t1, t2 in zip(half_1, always_reversible(half_2)):
            if not t1 or not t2:
                continue

            match = Match(home_team=t1, away_team=t2)
            if home_or_away and random.random() < 0.5:
                match = match.get_away_match()
            matches.append(match)

        if shuffle_matches:
            random.shuffle(matches)
        return cls(matches=matches)

    def __str__(self) -> str:
        data = [[m.home_team, m.result or "-", m.away_team] for m in self.matches]
        return tabulate(
            data,
            headers=["HOME", "RESULT", "AWAY"],
            colalign=("left", "center", "left"),
        )

    def get_away_fixture(self) -> "Fixture":
        return self.model_copy(
            update={"matches": [m.get_away_match() for m in self.matches]}
        )
