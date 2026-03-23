"""
Маппинг смысловых имён секций к заголовкам строк в таблице карты.

Используется для поиска нужной секции при чтении и (на следующих этапах)
при записи данных в карту.
"""

# Соответствие: логическое имя секции → заголовок строки в таблице
SECTION_LABELS: dict[str, str] = {
    "client_info":      "ФИО клиента, возраст",
    "agreements":       "ДОГОВОРЕННОСТИ",
    "complaints":       "Жалобы:",
    "targets":          "Мишени терапии:",
    "notes":            "ЗАМЕТКИ",
    "plan":             "ПЛАН РАБОТЫ:",
    "session_log":      "Регистрация встреч:",
    "session_notes":    "Примечания по встречам:",
}

# Человекочитаемые названия для интерфейса
SECTION_DISPLAY: dict[str, str] = {
    "client_info":      "Клиент",
    "agreements":       "Договорённости",
    "complaints":       "Жалобы и запрос",
    "targets":          "Мишени терапии",
    "notes":            "Заметки",
    "plan":             "План работы",
    "session_log":      "Регистрация встреч",
    "session_notes":    "Примечания по встречам",
}


def get_label(section_key: str) -> str:
    """Возвращает заголовок строки в таблице для логического имени секции."""
    return SECTION_LABELS.get(section_key, section_key)


def get_display_name(section_key: str) -> str:
    """Возвращает читаемое название секции для интерфейса."""
    return SECTION_DISPLAY.get(section_key, section_key)


def find_section_data(
    sections: dict[str, list[list[str]]],
    section_key: str,
) -> list[list[str]]:
    """
    Находит данные секции по логическому ключу.
    Возвращает список строк (каждая строка — список ячеек).
    """
    label = get_label(section_key)
    return sections.get(label, [])
