from collections import Counter
from functools import cached_property
from typing import Annotated, cast

from annotated_types import Len, Predicate
from more_itertools import flatten, ilen
from pydantic import (
    BaseModel,
    ConfigDict,
    computed_field,
    model_validator,
)

from .match_result import MatchResult, Result


class MatchStatistics(BaseModel):
    """Statistics for a number of matches with possibly multiple different teams"""

    model_config = ConfigDict(frozen=True)

    matches: Annotated[
        list[Annotated["Match", Predicate(lambda m: m.result)]], Len(min_length=1)
    ]

    @computed_field
    @cached_property
    def teams(self) -> "list[Team]":
        return list(
            dict.fromkeys(flatten([(m.home_team, m.away_team) for m in self.matches]))
        )

    @computed_field
    @cached_property
    def number_of_matches(self) -> int:
        return len(self.matches)

    @computed_field
    @cached_property
    def goals(self) -> int:
        return sum(
            r.home_goals + r.away_goals
            for r in (cast(MatchResult, m.result) for m in self.matches)
        )

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

        return (
            f"Number of matches:   {self.number_of_matches}\n"
            f"Avg. goals:          {self.average_goals:.2f}\n"
            f"Results probability\n{results_probability}"
        )


class TeamStatistics(MatchStatistics):
    """Statistics for a performance of an individual team in a number of matches"""

    model_config = ConfigDict(frozen=True)

    team: "Team"

    @model_validator(mode="after")
    def validate_team(self):
        assert all(
            m.is_contestant(self.team) for m in self.matches
        ), f"The team '{self.team}' must be a contestant in all matches."
        return self

    @computed_field
    @cached_property
    def wins(self) -> int:
        return ilen(m for m in self.matches if m.get_winner() is self.team)

    @computed_field
    @cached_property
    def draws(self) -> int:
        return ilen(m for m in self.matches if m.is_draw())

    @computed_field
    @cached_property
    def losses(self) -> int:
        return ilen(m for m in self.matches if m.get_loser() is self.team)

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
        return sum(m.get_goals(self.team) for m in self.matches)

    @computed_field
    @cached_property
    def goals_conceded(self) -> int:
        return sum(m.get_opponent_goals(self.team) for m in self.matches)

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
        return (
            f"Team:                           {self.team}\n"
            f"Number of matches:              {self.number_of_matches}\n"
            f"W / D / L %:                    {percentages}\n"
            f"Avg. goals scored / conceded:   {average_goals}"
        )


class HeadToHeadStatistics(TeamStatistics):
    """Statistics for a performance of a team against a specific opponent in a number of matches"""

    @model_validator(mode="after")
    def validate_opponent(self):
        assert all(
            m.is_contestant(self.opponent) for m in self.matches
        ), f"The team '{self.opponent}' must be a contestant in all matches."
        return self

    @computed_field
    @cached_property
    def opponent(self) -> "Team":
        return self.matches[0].get_opponent(self.team)

    def __str__(self) -> str:
        percentages = f"{self.win_percentage:.1%} / {self.draw_percentage:.1%} / {self.loss_percentage:.1%}"
        average_goals = (
            f"{self.average_goals_scored:.2f} / {self.average_goals_conceded:.2f}"
        )
        return (
            f"Team:                           {self.team}\n"
            f"Opponent:                       {self.opponent}\n"
            f"Number of matches:              {self.number_of_matches}\n"
            f"W / D / L %:                    {percentages}\n"
            f"Avg. goals scored / conceded:   {average_goals}"
        )


from .match import Match
from .team import Team
