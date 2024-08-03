from typing import Annotated

from annotated_types import Len
from pydantic import BaseModel, ConfigDict
from tabulate import tabulate

from .match import Match


class Fixture(BaseModel):
    """Encapsulates a fixture of matches"""

    model_config = ConfigDict(frozen=True)

    matches: Annotated[list[Match], Len(min_length=1)]

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
