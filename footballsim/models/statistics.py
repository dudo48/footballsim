from collections import Counter, defaultdict
from functools import cached_property
from typing import Any, Sequence

from more_itertools import flatten, ilen
from pydantic import (
    BaseModel,
    ConfigDict,
    computed_field,
    field_validator,
    model_validator,
)

from .match import Match
from .match_result import Result
from .team import Team


class TeamStatistics(BaseModel):
    """Statistics for a performance of an individual team in a number of matches"""

    model_config = ConfigDict(frozen=True)

    team: Team
    matches: Sequence[Match]

    @model_validator(mode="after")
    def validate_team_matches(self):
        assert all(
            self.team in (m.home_team, m.away_team) for m in self.matches
        ), f"The team '{self.team}' must be a contender in all matches."
        return self

    @computed_field
    @cached_property
    def number_of_matches(self) -> int:
        return len(self.matches)

    @computed_field
    @cached_property
    def wins(self) -> int:
        return ilen(m for m in self.matches if m.winner is self.team)

    @computed_field
    @cached_property
    def draws(self) -> int:
        return ilen(m for m in self.matches if m.is_draw())

    @computed_field
    @cached_property
    def losses(self) -> int:
        return ilen(m for m in self.matches if m.loser is self.team)

    @computed_field
    @cached_property
    def win_percentage(self) -> float:
        return self.wins / self.number_of_matches

    @computed_field
    @cached_property
    def draw_percentage(self) -> float:
        return self.draws / self.number_of_matches

    @computed_field
    @cached_property
    def loss_percentage(self) -> float:
        return self.losses / self.number_of_matches

    @computed_field
    @cached_property
    def goals_scored(self) -> int:
        return sum(
            m.result.home_goals if m.home_team is self.team else m.result.away_goals
            for m in self.matches
            if m.result
        )

    @computed_field
    @cached_property
    def goals_conceded(self) -> int:
        return sum(
            m.result.away_goals if m.home_team is self.team else m.result.home_goals
            for m in self.matches
            if m.result
        )

    @computed_field
    @cached_property
    def average_goals_scored(self) -> float:
        return self.goals_scored / self.number_of_matches

    @computed_field
    @cached_property
    def average_goals_conceded(self) -> float:
        return self.goals_conceded / self.number_of_matches

    def __str__(self) -> str:
        percentages = f"{self.win_percentage:.1%} / {self.draw_percentage:.1%} / {self.loss_percentage:.1%}"
        average_goals = (
            f"{self.average_goals_scored:.2f} / {self.average_goals_conceded:.2f}"
        )
        data = [
            f"Team:                           {self.team}",
            f"Number of matches:              {self.number_of_matches}",
            f"W / D / L %:                    {percentages}",
            f"Avg. goals scored / conceded:   {average_goals}",
        ]
        return "\n".join(data)


class MatchStatistics(BaseModel):
    """Statistics for a number of matches with possibly multiple different teams"""

    model_config = ConfigDict(frozen=True)

    matches: Sequence[Match]

    @field_validator("matches")
    @classmethod
    def non_empty(cls, sequence: Sequence[Any]):
        assert bool(sequence), "must not be empty"
        return sequence

    @computed_field
    @cached_property
    def teams(self) -> "list[Team]":
        return list(set(flatten([(m.home_team, m.away_team) for m in self.matches])))

    @computed_field
    @cached_property
    def teams_statistics(self) -> "list[TeamStatistics]":
        team_matches: "dict[Team, list[Match]]" = defaultdict(list)
        for match in self.matches:
            team_matches[match.home_team].append(match)
            team_matches[match.away_team].append(match)

        return [
            TeamStatistics(team=team, matches=matches)
            for team, matches in team_matches.items()
        ]

    @computed_field
    @cached_property
    def number_of_matches(self) -> int:
        return len(self.matches)

    @computed_field
    @cached_property
    def goals(self) -> int:
        return sum(stats.goals_scored for stats in self.teams_statistics)

    @computed_field
    @cached_property
    def average_goals(self) -> float:
        return self.goals / self.number_of_matches

    @computed_field
    @cached_property
    def results_frequency(self) -> "Counter[Result]":
        return Counter(m.result.full_time for m in self.matches if m.result)

    def __str__(self) -> str:
        results_probability = "\n".join(
            [
                f"{result} -> {freq / self.number_of_matches:.2%}"
                for result, freq in sorted(
                    self.results_frequency.items(), key=lambda t: t[1], reverse=True
                )
            ]
        )
        data = (
            f"Number of matches:   {self.number_of_matches}\n"
            f"Avg. goals:          {self.average_goals:.2f}\n"
            f"Results probability\n{results_probability}"
        )

        return "\n\n".join(
            [data]
            + [
                str(stats)
                for stats in sorted(
                    self.teams_statistics,
                    key=lambda s: s.number_of_matches,
                    reverse=True,
                )
            ]
        )
