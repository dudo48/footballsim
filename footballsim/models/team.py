import random
from statistics import fmean
from typing import TYPE_CHECKING, Generator

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
        Create a team from single strength value and the difference between its attack and defense and the value

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
    def random(
        cls,
        names: list[str],
        strength_mu: float = 0,
        strength_sigma: float = 1,
        ad_difference_sigma: float = 1,
    ) -> "Generator[Team, None, None]":
        """
        Generates teams with random strengths according to gauss distribution
        """

        def random_team(name: str) -> "Team":
            strength = round(random.gauss(strength_mu, strength_sigma))
            ad_difference = round(random.gauss(sigma=ad_difference_sigma))
            return cls.from_strength(name, strength, ad_difference)

        i = 0
        while True:
            for name in names:
                yield random_team(name if i == 0 else f"{name} {i}")
            i += 1

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
    @property
    def strength(self) -> int:
        return round((self.attack + self.defense) / 2)

    def __str__(self) -> str:
        return self.name

    def __lt__(self, other: "Team") -> bool:
        return self.strength < other.strength
