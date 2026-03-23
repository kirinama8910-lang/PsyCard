"""Валидация входных данных: формат клиента, первая строка заметки."""

import re

# Паттерн: Имя 1234 (кириллица или латиница, дефис допустим, 4 цифры)
_CLIENT_PATTERN = re.compile(r'^([А-Яа-яЁёA-Za-z\-]+)\s(\d{4})$')


def validate_client_string(s: str) -> bool:
    """Проверяет, соответствует ли строка формату 'Имя 1234'."""
    return bool(_CLIENT_PATTERN.match(s.strip()))


def parse_client_string(s: str) -> tuple[str, str] | None:
    """Разбирает строку 'Имя 1234'. Возвращает (имя, цифры) или None."""
    m = _CLIENT_PATTERN.match(s.strip())
    if not m:
        return None
    return m.group(1), m.group(2)
