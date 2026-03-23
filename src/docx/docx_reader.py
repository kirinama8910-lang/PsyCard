"""
Чтение клиентской карты .docx.

Карта построена на таблице. Строки с одной уникальной ячейкой считаются
заголовками секций. Следующие строки — содержимое этой секции.
"""

from pathlib import Path
from docx import Document


def _unique_cells(row) -> list[str]:
    """Возвращает уникальные непустые ячейки строки (убирает слияния)."""
    seen: set[str] = set()
    result: list[str] = []
    for cell in row.cells:
        text = cell.text.strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def read_card(card_path: Path) -> dict[str, list[list[str]]]:
    """
    Читает .docx карту клиента.

    Возвращает словарь:
        { "Заголовок секции": [ [ячейки строки], [ячейки строки], ... ] }

    Строки с одной уникальной ячейкой считаются заголовком новой секции.
    """
    doc = Document(card_path)

    if not doc.tables:
        raise ValueError(
            "Документ не содержит таблиц. "
            "Убедитесь, что шаблон оформлен в табличном формате."
        )

    table = doc.tables[0]
    sections: dict[str, list[list[str]]] = {}
    current: str = "_top"
    sections[current] = []

    for row in table.rows:
        cells = _unique_cells(row)
        if not cells:
            continue

        if len(cells) == 1:
            current = cells[0]
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(cells)

    return sections


def get_field(sections: dict, section_key: str, col_index: int = 0) -> str:
    """
    Возвращает текст первой строки данных в секции по индексу колонки.
    Удобно для получения одиночного значения поля.
    """
    rows = sections.get(section_key, [])
    for row in rows:
        if col_index < len(row):
            return row[col_index]
    return ""


def read_card_rows(card_path: Path) -> list[list[str]]:
    """
    Возвращает все строки таблицы в виде плоского списка (дедуплицированные ячейки).
    Используется для поиска полей, которые не являются одиночными заголовками.
    """
    doc = Document(card_path)
    if not doc.tables:
        return []
    result = []
    for row in doc.tables[0].rows:
        cells = _unique_cells(row)
        if cells:
            result.append(cells)
    return result


def _is_section_header(row: list[str]) -> bool:
    """
    Строка считается заголовком или меткой-разделителем если:
    - одна ячейка: текст КАПС или короткий с ":"
    - несколько ячеек: все ячейки короткие и заканчиваются на ":"
    """
    if not row:
        return False
    if len(row) == 1:
        text = row[0]
        return text.isupper() or (len(text) < 60 and text.endswith(":"))
    # Многоячеечная строка — все ячейки выглядят как метки
    return all(len(c) < 60 and c.endswith(":") for c in row)


def find_field_value(
    rows: list[list[str]],
    label: str,
) -> list[list[str]]:
    """
    Ищет строку-метку, содержащую label в первой ячейке,
    и возвращает строки данных до следующего заголовка секции.
    Саму строку-метку в результат не включает.
    """
    result = []
    found = False
    for row in rows:
        if not found:
            if row and label in row[0]:
                found = True
        else:
            if _is_section_header(row):
                break
            result.append(row)
    return result
