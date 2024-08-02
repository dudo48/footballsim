from functools import cached_property

from pydantic import BaseModel, ConfigDict, computed_field


class Result(BaseModel):
    model_config = ConfigDict(frozen=True)

    home_goals: int
    away_goals: int

    def __str__(self) -> str:
        return f"{self.home_goals} - {self.away_goals}"

    def is_win(self) -> bool:
        return self.home_goals > self.away_goals

    def is_draw(self) -> bool:
        return self.home_goals == self.away_goals

    def is_loss(self) -> bool:
        return self.home_goals < self.away_goals


class MatchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    full_time: Result

    @computed_field
    @cached_property
    def home_goals(self) -> int:
        return self.full_time.home_goals

    @computed_field
    @cached_property
    def away_goals(self) -> int:
        return self.full_time.away_goals

    def __str__(self) -> str:
        return str(self.full_time)

    def is_win(self) -> bool:
        return self.full_time.is_win()

    def is_draw(self) -> bool:
        return self.full_time.is_draw()

    def is_loss(self) -> bool:
        return self.full_time.is_loss()
