from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class PollCreateSchema(BaseModel):
    question: str
    options: list[str]

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str):
        value = value.strip()

        if len(value) < 2 or len(value) > 255:
            raise ValueError("Question must be 2-255 characters")

        return value

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: list[str]):
        clean_options = []

        for option in value:
            option = option.strip()

            if not option:
                raise ValueError("Poll option cannot be empty")

            if len(option) > 100:
                raise ValueError("Poll option must be at most 100 characters")

            clean_options.append(option)

        if len(clean_options) < 2 or len(clean_options) > 10:
            raise ValueError("Poll must have 2-10 options")

        if len(set(clean_options)) != len(clean_options):
            raise ValueError("Poll options must be unique")

        return clean_options


class PollVoteSchema(BaseModel):
    option_id: int

    @field_validator("option_id")
    @classmethod
    def validate_option_id(cls, value: int):
        if value <= 0:
            raise ValueError("Option id must be positive")

        return value


class PollOptionRead(BaseModel):
    id: int
    text: str
    votes_count: int
    percent: int
    is_voted_by_me: bool


class PollRead(BaseModel):
    id: int
    question: str
    options: list[PollOptionRead]
    total_votes: int
    is_voted_by_me: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DetailResponse(BaseModel):
    detail: str
