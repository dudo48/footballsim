import math
import random

from pydantic import BaseModel, computed_field


class Team(BaseModel):
    name: str
    attack: int
    defense: int

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
        cls, names: list[str], min_strength: int, max_strength: int
    ) -> "list[Team]":
        """
        Generate multiple teams with random strengths
        """

        def generate_random_team(name: str) -> "Team":
            strength = random.randint(min_strength, max_strength)
            factor: int = (-1) ** random.randint(0, 1)
            ad_difference = int(random.random() * math.sqrt(strength)) * factor
            return cls.from_strength(name, strength, ad_difference)

        return [generate_random_team(name) for name in names]

    @computed_field
    @property
    def strength(self) -> float:
        return (self.attack + self.defense) / 2

    def __str__(self) -> str:
        return self.name

    def __lt__(self, other: "Team") -> bool:
        return self.strength < other.strength
