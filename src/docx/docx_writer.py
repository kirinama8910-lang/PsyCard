"""
Запись данных из фронтенда в карту .docx.

Карта построена на таблице. Секции определяются по строкам с одной уникальной ячейкой.
Запись обновляет текст в первой ячейке данных после заголовка секции.
Safe write: сначала .tmp файл, потом замена оригинала.
"""

from pathlib import Path

from docx import Document


# ── Маппинг: ключи фронтенда → метки секций в таблице ──────────────────────

def card_to_sections(card: dict) -> dict[str, str]:
    """
    Конвертирует объект карты фронтенда в словарь {метка_секции: текст}.
    Используется как входные данные для write_card().
    """
    p  = card.get("passport", {})
    a  = card.get("agreements", {})
    tc = card.get("therapyCore", {})
    n  = card.get("notes", {})
    pl = card.get("plan", {})
    lo = card.get("logs", {})

    def _lines(*pairs: tuple[str, str]) -> str:
        return "\n".join(f"{label}: {val}" for label, val in pairs if val)

    return {
        "ФИО клиента, возраст": _lines(
            ("Клиент",   p.get("clientDisplayName", "")),
            ("Женщина",  p.get("woman", "")),
            ("Мужчина",  p.get("man", "")),
            ("Ребёнок",  p.get("child", "")),
        ),
        "ДОГОВОРЕННОСТИ": _lines(
            ("Частота",   a.get("frequencyDuration", "")),
            ("Стоимость", a.get("cost", "")),
            ("Правила",   a.get("rules", "")),
            ("Другое",    a.get("other", "")),
        ),
        "Жалобы:": _lines(
            ("Жалобы", tc.get("complaints", "")),
            ("Запрос",  tc.get("request", "")),
        ),
        "Мишени терапии:": tc.get("therapyTargets", ""),
        "ЗАМЕТКИ": _lines(
            ("Тип личности",                   n.get("personalityType", "")),
            ("Образование/Профессия",          n.get("educationProfession", "")),
            ("Состав семьи",                   n.get("familyComposition", "")),
            ("Хронические заболевания",        n.get("chronicDiseases", "")),
            ("Наблюдения у психиатра",         n.get("psychiatristObservations", "")),
            ("Отец",                           n.get("father", "")),
            ("Мать",                           n.get("mother", "")),
            ("Сиблинги",                       n.get("siblings", "")),
            ("Дети",                           n.get("children", "")),
            ("Важные биографические события",  n.get("importantBiography", "")),
        ),
        "ПЛАН РАБОТЫ:": _build_plan_text(pl),
        "Регистрация встреч:":    _build_meetings_text(lo.get("registrationMeetings", [])),
        "Примечания по встречам:": _build_session_notes_text(lo.get("sessionNotes", [])),
    }


def _build_plan_text(plan: dict) -> str:
    parts = []
    if plan.get("hypotheses"):
        parts.append(f"Гипотезы:\n{plan['hypotheses']}")
    stages = plan.get("stages", {})
    for i in range(1, 6):
        stage = stages.get(str(i)) or stages.get(i, {})
        if stage and stage.get("plan"):
            parts.append(f"\nЭтап {i}:\n{stage['plan']}")
    return "\n".join(parts)


def _build_meetings_text(meetings: list) -> str:
    lines = []
    for m in meetings:
        if m.get("date") or m.get("topic"):
            lines.append(" | ".join(filter(None, [
                m.get("date", ""), m.get("topic", ""), m.get("exercises", "")
            ])))
    return "\n".join(lines)


def _build_session_notes_text(notes: list) -> str:
    lines = []
    for n in notes:
        if n.get("date") or n.get("content"):
            lines.append(" — ".join(filter(None, [
                n.get("date", ""), n.get("content", ""), n.get("observation", "")
            ])))
    return "\n".join(lines)


# ── Работа с таблицей ────────────────────────────────────────────────────────

def _unique_cells(row) -> list:
    """Возвращает уникальные ячейки строки (убирает дубликаты от слияния)."""
    seen: set[int] = set()
    result = []
    for cell in row.cells:
        cell_id = id(cell._tc)
        if cell_id not in seen:
            seen.add(cell_id)
            result.append(cell)
    return result


def _find_section_row(table, label: str) -> int | None:
    """Находит индекс строки-заголовка секции по метке (точное совпадение или вхождение)."""
    for i, row in enumerate(table.rows):
        cells = _unique_cells(row)
        texts = [c.text.strip() for c in cells if c.text.strip()]
        if len(texts) == 1 and (texts[0] == label or label in texts[0]):
            return i
    return None


def _set_cell_text(cell, text: str) -> None:
    """Заменяет текст ячейки. Сохраняет параграф, удаляет предыдущее содержимое."""
    cell.text = str(text) if text else ""


def write_card(card_path: Path, card: dict) -> int:
    """
    Записывает данные карты фронтенда в .docx файл.

    Алгоритм:
    1. Маппинг frontend card → {секция: текст}
    2. Для каждой секции: найти строку-заголовок в таблице
    3. Обновить первую ячейку данных после заголовка
    4. Safe write: сохранить во временный файл, заменить оригинал

    Возвращает количество обновлённых секций.
    """
    doc = Document(card_path)

    if not doc.tables:
        raise ValueError(
            "Документ не содержит таблиц. "
            "Убедитесь, что шаблон оформлен в табличном формате."
        )

    table = doc.tables[0]
    section_data = card_to_sections(card)
    updated = 0

    for label, content in section_data.items():
        if not content:
            continue

        header_idx = _find_section_row(table, label)
        if header_idx is None:
            continue

        # Ищем первую строку данных после заголовка
        for i in range(header_idx + 1, len(table.rows)):
            row = table.rows[i]
            cells = _unique_cells(row)
            texts = [c.text.strip() for c in cells if c.text.strip()]

            # Если это следующий заголовок секции — останавливаемся
            if len(texts) == 1:
                break

            # Нашли строку с данными — пишем в первую ячейку
            if cells:
                _set_cell_text(cells[0], content)
                updated += 1
                break

    # Safe write: temp → replace
    tmp_path = card_path.with_suffix(".tmp.docx")
    doc.save(tmp_path)
    tmp_path.replace(card_path)

    return updated
