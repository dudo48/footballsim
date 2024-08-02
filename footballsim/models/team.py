import math
import random
from functools import cached_property
from statistics import fmean
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, computed_field

from .helpers import calculate_strength_diff

if TYPE_CHECKING:
    from .statistics import TeamStatistics


class Team(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    attack: int = 0
    defense: int = 0

    @classmethod
    def from_strength(cls, name: str, strength: int, ad_difference: int = 0) -> "Team":
        """
        Create a team from strength value and the difference between its attack and defense

        Args:
            name (str): Name of the team
            strength (int): Strength of the tea
            ad_difference (int, optional): Difference between attack and defense. Defaults to 0.

        Returns:
            Team: a new instance of a team
        """
        attack = strength + ad_difference
        defense = strength - ad_difference
        return cls(name=name, attack=attack, defense=defense)

    @classmethod
    def generate(
        cls, names: list[str], min_strength: int, max_strength: Optional[int] = None
    ) -> "list[Team]":
        """
        Generate random team(s) with count according to number of names given
        """
        if not max_strength:
            max_strength = min_strength

        def generate_random_team(name: str) -> "Team":
            strength = random.randint(min_strength, max_strength)
            ad_difference = round(random.gauss(sigma=math.log(math.sqrt(strength))))
            return cls.from_strength(name, strength, ad_difference)

        return [generate_random_team(name) for name in names]

    @classmethod
    def from_statistics(cls, team_statistics: "TeamStatistics") -> "Team":
        """
        Create a team with predicted strength from a TeamStatistics object

        Args:
            statistics (TeamStatistics):

        Returns:
            Team: a new Team object
        """

        def calculate_diff(goals: int):
            return calculate_strength_diff(goals or 0.5)

        attacks: list[float] = []
        defenses: list[float] = []

        team = team_statistics.team
        for match in team_statistics.matches:
            opponent = match.get_opponent(team)
            goals_scored, goals_conceded = (
                match.get_team_goals(team),
                match.get_team_goals(opponent),
            )

            attacks.append(opponent.defense + calculate_diff(goals_scored))
            defenses.append(opponent.attack - calculate_diff(goals_conceded))

        return team.model_copy(
            update={
                "attack": round(fmean(attacks)),
                "defense": round(fmean(defenses)),
            }
        )

    @computed_field
    @cached_property
    def strength(self) -> float:
        return (self.attack + self.defense) / 2

    def __str__(self) -> str:
        return self.name

    def __lt__(self, other: "Team") -> bool:
        return self.strength < other.strength
