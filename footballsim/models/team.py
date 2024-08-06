import random
from statistics import fmean
from typing import Generator

from more_itertools import bucket
from pydantic import BaseModel, ConfigDict, computed_field

from .helpers import calculate_difference


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

    @staticmethod
    def from_matches(matches: "list[Match]", team: "Team") -> "Team":
        """
        Predict a team according to its results in a number of matches

        Args:
            team (Team): The team to predict the strengths of
            matches (list[Match]): The group of matches to predict the team from. The team must be a contender in at least one of the matches. The matches in which the team is not a contender in will be ignored

        Returns:
            Team: A new team similar to the original team except with possibly different strengths
        """

        team_matches = [m for m in matches if m.is_contender(team)]
        assert (
            team_matches
        ), f"The team '{team}' is not a contender in any of the matches."

        opponent_matches = bucket(team_matches, lambda m: m.get_opponent(team))
        h2h_statistics = [
            HeadToHeadStatistics(matches=list(opponent_matches[o]), team=team)
            for o in opponent_matches
        ]

        attacks: list[float] = []
        defenses: list[float] = []
        weights: list[int] = []

        for statistics in h2h_statistics:
            zero_substitute = 1 / (statistics.number_of_matches + 1)
            attacks.append(
                statistics.opponent.defense
                + calculate_difference(
                    statistics.average_goals_scored or zero_substitute
                )
            )
            defenses.append(
                statistics.opponent.attack
                - calculate_difference(
                    statistics.average_goals_conceded or zero_substitute
                )
            )
            weights.append(statistics.number_of_matches)

        return team.model_copy(
            update={
                "attack": round(fmean(attacks, weights)),
                "defense": round(fmean(defenses, weights)),
            }
        )

    @computed_field
    @property
    def strength(self) -> float:
        return (self.attack + self.defense) / 2

    def __str__(self) -> str:
        return self.name

    def __lt__(self, other: "Team") -> bool:
        return self.strength < other.strength


from .match import Match
from .statistics import HeadToHeadStatistics
