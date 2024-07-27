from functools import cached_property
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .helpers import calculate_xg
from .match_result import MatchResult
from .team import Team


class Match(BaseModel):
    model_config = ConfigDict(frozen=True)

    home_team: Team
    away_team: Team
    result: Optional[MatchResult] = None

    @cached_property
    def home_xg(self) -> float:
        return calculate_xg(self.home_team.attack - self.away_team.defense)

    @cached_property
    def away_xg(self) -> float:
        return calculate_xg(self.away_team.attack - self.home_team.defense)

    @cached_property
    def winner(self) -> Optional[Team]:
        if self.is_win():
            return self.home_team
        if self.is_loss():
            return self.away_team
        return None

    @cached_property
    def loser(self) -> Optional[Team]:
        if self.is_win():
            return self.away_team
        if self.is_loss():
            return self.home_team
        return None

    def is_win(self) -> bool:
        return bool(self.result and self.result.is_win())

    def is_draw(self) -> bool:
        return bool(self.result and self.result.is_draw())

    def is_loss(self) -> bool:
        return bool(self.result and self.result.is_loss())

    def get_away_match(self) -> "Match":
        return self.model_copy(
            update={
                "home_team": self.away_team,
                "away_team": self.home_team,
            }
        )

    def __str__(self) -> str:
        return "{} {:^9} {}".format(
            self.home_team, str(self.result) or "-", self.away_team
        )
