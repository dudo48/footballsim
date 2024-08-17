import random
from collections import defaultdict
from statistics import fmean, median
from typing import Generator, Optional

from more_itertools import bucket
from pydantic import BaseModel, ConfigDict, computed_field

from .constants import XG_CONSTANT
from .helpers import calculate_difference


class Team(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    attack: int = 0
    defense: int = 0

    @classmethod
    def from_strength(
        cls, name: str = "", strength: int = 0, ad_difference: int = 0
    ) -> "Team":
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
    def from_h2h(
        team: "Team",
        opponent: "Team",
        average_goals_scored: float = XG_CONSTANT,
        average_goals_conceded: float = XG_CONSTANT,
        number_of_matches: int = 1,
    ):
        zero_substitute = 1 / (number_of_matches + 1)
        return team.model_copy(
            update={
                "attack": round(
                    opponent.defense
                    + calculate_difference(average_goals_scored or zero_substitute)
                ),
                "defense": round(
                    opponent.attack
                    - calculate_difference(average_goals_conceded or zero_substitute)
                ),
            }
        )

    @staticmethod
    def from_matches(
        matches: "list[Match]",
        team: "Team",
        teams_override: "Optional[dict[Team, Team]]" = None,
    ) -> "Team":
        """
        Predict a team according to its results against other teams in a number of matches

        Args:
            matches (list[Match]): The group of matches to predict the team from. The team must be a contestant in at least one of the matches. The matches in which the team is not a contestant in will be ignored
            team (Team): The team to predict the strengths of
            teams_override (dict[Team, Team]): Override an opponent team with another team when calculating predicted strength

        Returns:
            Team: New version of the original team with predicted strength
        """

        teams_override = teams_override or {}
        team_matches = [m for m in matches if m.is_contestant(team)]
        assert (
            team_matches
        ), f"The team '{team}' is not a contestant in any of the matches."

        opponent_matches = bucket(team_matches, lambda m: m.get_opponent(team))
        h2h_statistics = [
            HeadToHeadStatistics(matches=list(opponent_matches[o]), team=team)
            for o in opponent_matches
        ]

        attacks: list[float] = []
        defenses: list[float] = []
        weights: list[int] = []

        for h2h in h2h_statistics:
            predicted_team = Team.from_h2h(
                team,
                opponent=teams_override.get(h2h.opponent, h2h.opponent),
                average_goals_scored=h2h.average_goals_scored,
                average_goals_conceded=h2h.average_goals_conceded,
                number_of_matches=h2h.number_of_matches,
            )
            attacks.append(predicted_team.attack)
            defenses.append(predicted_team.defense)
            weights.append(h2h.number_of_matches)

        return team.model_copy(
            update={
                "attack": round(fmean(attacks, weights)),
                "defense": round(fmean(defenses, weights)),
            }
        )

    @staticmethod
    def all_from_matches(matches: "list[Match]", mid_strength: int = 0) -> "list[Team]":
        team_matches: "defaultdict[Team, list[Match]]" = defaultdict(list)
        for match in matches:
            team_matches[match.home_team].append(match)
            team_matches[match.away_team].append(match)

        teams_statistics = [
            TeamStatistics(matches=matches, team=team)
            for team, matches in team_matches.items()
        ]

        # set the initial strength of teams using an imaginary medium-strength team
        anchor_team = Team.from_h2h(
            Team.from_strength(),
            Team.from_strength(strength=mid_strength),
            median((s.average_goals_scored for s in teams_statistics)),
            median((s.average_goals_conceded for s in teams_statistics)),
            round(median((s.number_of_matches for s in teams_statistics))),
        )

        teams_override = {
            s.team: Team.from_h2h(
                s.team,
                opponent=anchor_team,
                average_goals_scored=s.average_goals_scored,
                average_goals_conceded=s.average_goals_conceded,
                number_of_matches=s.number_of_matches,
            )
            for s in teams_statistics
        }

        # iterate over teams according to their predicted strength
        teams_to_predict = sorted(
            team_matches.keys(),
            key=lambda t: teams_override[t],
        )
        for team in teams_to_predict:
            predicted_team = Team.from_matches(team_matches[team], team, teams_override)

            # update the team with the more accurate prediction
            teams_override[team] = predicted_team

        return list(teams_override.values())

    @computed_field
    @property
    def strength(self) -> float:
        return (self.attack + self.defense) / 2

    def __str__(self) -> str:
        return self.name

    def __lt__(self, other: "Team") -> bool:
        return self.strength < other.strength


from .match import Match
from .statistics import HeadToHeadStatistics, TeamStatistics
