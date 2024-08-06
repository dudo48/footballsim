import csv
from typing import NamedTuple

from .match import Match
from .match_result import MatchResult, Result
from .team import Team


class ReadMatchesResult(NamedTuple):
    matches: list[Match]
    teams: list[Team]


def read_matches(
    csv_file: str,
    home_team_col: str = "home_team",
    away_team_col: str = "away_team",
    home_goals_col: str = "home_goals",
    away_goals_col: str = "away_goals",
) -> ReadMatchesResult:
    def create_team(name: str) -> Team:
        if name not in team_names:
            team = Team(name=name)
            team_names[name] = team
            teams.append(team)
        return team_names[name]

    matches: list[Match] = []
    teams: list[Team] = []
    with open(csv_file) as file:
        team_names: dict[str, Team] = {}
        reader = csv.DictReader(file)
        for row in reader:
            match_result = None
            home_goals: str = row.get(home_goals_col, "")
            away_goals: str = row.get(away_goals_col, "")
            if home_goals.isdigit() and away_goals.isdigit():
                match_result = MatchResult(
                    full_time=Result(
                        home_goals=int(home_goals), away_goals=int(away_goals)
                    )
                )
            matches.append(
                Match(
                    home_team=create_team(row[home_team_col]),
                    away_team=create_team(row[away_team_col]),
                    result=match_result,
                )
            )

    return ReadMatchesResult(matches=matches, teams=teams)
