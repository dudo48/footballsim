from collections import defaultdict
from typing import Annotated

from annotated_types import Len
from pydantic import BaseModel, ConfigDict, computed_field
from tabulate import tabulate

from .constants import DRAW_POINTS, WIN_POINTS
from .match import Match
from .team import Team


class TeamStanding(BaseModel):
    model_config = ConfigDict(frozen=True)

    team: Team
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_scored: int = 0
    goals_conceded: int = 0

    @computed_field
    @property
    def matches_played(self) -> int:
        return self.wins + self.draws + self.losses

    @computed_field
    @property
    def goals_difference(self) -> int:
        return self.goals_scored - self.goals_conceded

    @computed_field
    @property
    def points(self) -> int:
        return WIN_POINTS * self.wins + DRAW_POINTS * self.draws

    def __lt__(self, other: "TeamStanding") -> bool:
        return self._weights() < other._weights()

    def __add__(self, other: "TeamStanding") -> "TeamStanding":
        assert self.team is other.team
        return self.model_copy(
            update={
                "wins": self.wins + other.wins,
                "draws": self.draws + other.draws,
                "losses": self.losses + other.losses,
                "goals_scored": self.goals_scored + other.goals_scored,
                "goals_conceded": self.goals_conceded + other.goals_conceded,
            }
        )

    def _weights(self) -> tuple[int, ...]:
        return self.points, self.goals_difference, self.goals_scored


class Standings(BaseModel):
    model_config = ConfigDict(frozen=True)

    team_standings: Annotated[list[TeamStanding], Len(min_length=2)]

    @classmethod
    def from_teams(cls, teams: list[Team]) -> "Standings":
        return cls(team_standings=[TeamStanding(team=team) for team in teams])

    def __str__(self) -> str:
        data = [
            [
                s.team,
                s.matches_played,
                s.wins,
                s.draws,
                s.losses,
                s.goals_scored,
                s.goals_conceded,
                s.goals_difference,
                s.points,
            ]
            for s in self.team_standings
        ]
        return tabulate(
            data,
            headers=["TEAM", "MP", "W", "D", "L", "GS", "GC", "GD", "PTS"],
        )

    def update_from_matches(self, matches: list[Match]) -> "Standings":
        """Returns new standings same as current standings but with statistics updated according to results from given matches"""
        deltas: defaultdict[Team, list[TeamStanding]] = defaultdict(list)
        for match in matches:
            if not match.result:
                continue

            home_update: dict[str, int] = {}
            away_update: dict[str, int] = {}
            if match.is_draw():
                home_update["draws"] = away_update["draws"] = 1
            elif match.is_win():
                home_update["wins"] = away_update["losses"] = 1
            elif match.is_loss():
                home_update["losses"] = away_update["wins"] = 1

            home_update["goals_scored"] = away_update["goals_conceded"] = (
                match.result.home_goals
            )
            home_update["goals_conceded"] = away_update["goals_scored"] = (
                match.result.away_goals
            )

            deltas[match.home_team].append(
                TeamStanding(team=match.home_team, **home_update)
            )
            deltas[match.away_team].append(
                TeamStanding(team=match.away_team, **away_update)
            )

        team_standings: list[TeamStanding] = []
        for standing in self.team_standings:
            new_standing = sum(deltas.get(standing.team, []), standing)
            team_standings.append(new_standing)

        return self.model_copy(
            update={"team_standings": sorted(team_standings, reverse=True)}
        )
