"""Pydantic v2 схемы для валидации JSON-ответов от LLM."""

from typing import Any
from pydantic import BaseModel, model_validator


class LLMResponse(BaseModel):
    task_type: str
    client_key: str
    create_if_missing: bool = True
    sections: dict[str, Any]

    @model_validator(mode="after")
    def check_sections_not_empty(self) -> "LLMResponse":
        if not self.sections:
            raise ValueError("Поле sections не может быть пустым")
        return self

    @model_validator(mode="after")
    def check_client_key_format(self) -> "LLMResponse":
        import re
        pattern = re.compile(r'^[А-Яа-яЁёA-Za-z\-]+\s\d{4}$')
        if not pattern.match(self.client_key.strip()):
            raise ValueError(
                f"client_key '{self.client_key}' не соответствует формату 'Имя 1234'"
            )
        return self
