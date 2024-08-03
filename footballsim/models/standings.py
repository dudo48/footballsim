from collections import defaultdict
from typing import Annotated, Callable

from annotated_types import Len
from pydantic import BaseModel, ConfigDict, computed_field
from tabulate import tabulate

from .constants import DRAW_POINTS, WIN_POINTS
from .helpers import default_tie_breakers
from .match import Match
from .team import Team


class TeamStanding(BaseModel):
    model_config = ConfigDict(frozen=True)

    team: Team
    position: int = 1
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
        return self.position < other.position

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


class Standings(BaseModel):
    model_config = ConfigDict(frozen=True)

    team_standings: Annotated[list[TeamStanding], Len(min_length=2)]
    tie_breakers: Callable[[TeamStanding], tuple[int, ...]] = default_tie_breakers

    @classmethod
    def from_teams(cls, teams: list[Team]) -> "Standings":
        return cls(
            team_standings=[
                TeamStanding(team=team, position=len(teams)) for team in teams
            ]
        )

    @staticmethod
    def calculate_teams_delta(match: Match) -> tuple[TeamStanding, TeamStanding]:
        """Calculate the delta TeamStanding of the home team and away team from a single match and returns the results in the order: home, away"""
        assert bool(match.result)
        home: dict[str, int] = {}
        away: dict[str, int] = {}
        if match.is_draw():
            home["draws"] = away["draws"] = 1
        elif match.is_win():
            home["wins"] = away["losses"] = 1
        elif match.is_loss():
            home["losses"] = away["wins"] = 1

        home["goals_scored"] = away["goals_conceded"] = match.result.home_goals
        home["goals_conceded"] = away["goals_scored"] = match.result.away_goals
        return TeamStanding(team=match.home_team, **home), TeamStanding(
            team=match.away_team, **away
        )

    def __str__(self) -> str:
        data = [
            [
                s.position,
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
            headers=["", "TEAM", "MP", "W", "D", "L", "GS", "GC", "GD", "PTS"],
        )

    def _calculate_positions(
        self, team_standings: list[TeamStanding]
    ) -> list[TeamStanding]:
        """Calculate positions of a list of team standings using the standings' tie breaker gunction"""
        return [
            s.model_copy(update={"position": i + 1})
            for i, s in enumerate(
                sorted(team_standings, key=self.tie_breakers, reverse=True)
            )
        ]

    def update_from_matches(self, matches: list[Match]) -> "Standings":
        """Returns new standings same as current standings but with statistics updated according to results from given matches"""
        deltas: defaultdict[Team, list[TeamStanding]] = defaultdict(list)
        for match in matches:
            if not match.result:
                continue
            home, away = Standings.calculate_teams_delta(match)
            deltas[match.home_team].append(home)
            deltas[match.away_team].append(away)

        team_standings: list[TeamStanding] = []
        for standing in self.team_standings:
            new_standing = sum(deltas.get(standing.team, []), standing)
            team_standings.append(new_standing)

        return self.model_copy(
            update={"team_standings": self._calculate_positions(team_standings)}
        )
