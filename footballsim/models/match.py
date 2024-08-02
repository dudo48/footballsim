from functools import cached_property
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field

from .helpers import calculate_xg
from .match_result import MatchResult
from .team import Team


class Match(BaseModel):
    model_config = ConfigDict(frozen=True)

    home_team: Team
    away_team: Team
    result: Optional[MatchResult] = None

    @computed_field
    @cached_property
    def home_xg(self) -> float:
        return calculate_xg(self.home_team.attack - self.away_team.defense)

    @computed_field
    @cached_property
    def away_xg(self) -> float:
        return calculate_xg(self.away_team.attack - self.home_team.defense)

    @computed_field
    @cached_property
    def winner(self) -> Optional[Team]:
        if self.is_win():
            return self.home_team
        if self.is_loss():
            return self.away_team
        return None

    @computed_field
    @cached_property
    def loser(self) -> Optional[Team]:
        if self.is_win():
            return self.away_team
        if self.is_loss():
            return self.home_team
        return None

    def __str__(self) -> str:
        return "{} {:^9} {}".format(
            self.home_team, str(self.result) or "-", self.away_team
        )

    def is_win(self) -> bool:
        return bool(self.result and self.result.is_win())

    def is_draw(self) -> bool:
        return bool(self.result and self.result.is_draw())

    def is_loss(self) -> bool:
        return bool(self.result and self.result.is_loss())

    def get_opponent(self, team: Team) -> Team:
        if team is self.home_team:
            return self.away_team
        elif team is self.away_team:
            return self.home_team
        raise ValueError(f"The team '{team}' is not a contender in the match.")

    def get_team_goals(self, team: Team) -> int:
        if not self.result:
            raise ValueError("The match does not have a result.")
        if team is self.home_team:
            return self.result.home_goals
        elif team is self.away_team:
            return self.result.away_goals
        raise ValueError(f"The team '{team}' is not a contender in the match.")

    def get_opponent_goals(self, team: Team) -> int:
        return self.get_team_goals(self.get_opponent(team))

    def get_away_match(self) -> "Match":
        return self.model_copy(
            update={
                "home_team": self.away_team,
                "away_team": self.home_team,
            }
        )
