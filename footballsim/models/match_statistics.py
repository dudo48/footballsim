from collections import Counter
from functools import cached_property
from typing import Sequence

from more_itertools import ilen
from pydantic import BaseModel, ConfigDict

from .match import Match
from .match_result import Result


class MatchStatistics(BaseModel):
    model_config = ConfigDict(frozen=True)

    matches: Sequence[Match]

    @cached_property
    def number_of_matches(self) -> int:
        return len(self.matches)

    @cached_property
    def wins(self) -> int:
        return ilen(m for m in self.matches if m.is_win())

    @cached_property
    def draws(self) -> int:
        return ilen(m for m in self.matches if m.is_draw())

    @cached_property
    def losses(self) -> int:
        return ilen(m for m in self.matches if m.is_loss())

    @cached_property
    def win_percentage(self) -> float:
        return self.wins / self.number_of_matches

    @cached_property
    def draw_percentage(self) -> float:
        return self.draws / self.number_of_matches

    @cached_property
    def loss_percentage(self) -> float:
        return self.losses / self.number_of_matches

    @cached_property
    def home_goals(self) -> int:
        return sum(m.result.home_goals for m in self.matches if m.result)

    @cached_property
    def away_goals(self) -> int:
        return sum(m.result.away_goals for m in self.matches if m.result)

    @cached_property
    def total_goals(self) -> int:
        return self.home_goals + self.away_goals

    @cached_property
    def average_home_goals(self) -> float:
        return self.home_goals / self.number_of_matches

    @cached_property
    def average_away_goals(self) -> float:
        return self.away_goals / self.number_of_matches

    @cached_property
    def average_total_goals(self) -> float:
        return self.total_goals / self.number_of_matches

    @cached_property
    def results_frequency(self) -> "Counter[Result]":
        return Counter(m.result.full_time for m in self.matches if m.result)

    def __str__(self) -> str:
        percentages = f"{self.win_percentage:.1%} / {self.draw_percentage:.1%} / {self.loss_percentage:.1%}"
        average_goals = f"{self.average_home_goals:.2f} / {self.average_away_goals:.2f} / {self.average_total_goals:.2f}"
        results_probability = "\n".join(
            [
                f"{result} -> {freq / self.number_of_matches:.2%}"
                for result, freq in sorted(
                    self.results_frequency.items(), key=lambda t: t[1], reverse=True
                )
            ]
        )
        data = [
            f"Number of matches:         {self.number_of_matches}",
            f"W / D / L %:               {percentages}",
            f"Average goals H / A / T:   {average_goals}",
            f"Results Probability\n{results_probability}",
        ]
        return "\n".join(data)
