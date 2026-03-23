"""Парсинг текстовых заметок: извлечение клиента из первой строки."""

from src.validators import parse_client_string

# Таблица транслитерации кириллицы → латиница для имён папок
_TRANSLIT = {
    'а': 'a',  'б': 'b',  'в': 'v',  'г': 'g',  'д': 'd',
    'е': 'e',  'ё': 'yo', 'ж': 'zh', 'з': 'z',  'и': 'i',
    'й': 'y',  'к': 'k',  'л': 'l',  'м': 'm',  'н': 'n',
    'о': 'o',  'п': 'p',  'р': 'r',  'с': 's',  'т': 't',
    'у': 'u',  'ф': 'f',  'х': 'kh', 'ц': 'ts', 'ч': 'ch',
    'ш': 'sh', 'щ': 'sch','ъ': '',   'ы': 'y',  'ь': '',
    'э': 'e',  'ю': 'yu', 'я': 'ya',
}


def _transliterate(text: str) -> str:
    """Транслитерирует кириллицу в латиницу для использования в именах папок."""
    return ''.join(_TRANSLIT.get(ch, ch) for ch in text.lower())


def build_client_id(name: str, digits: str) -> str:
    """Строит безопасный идентификатор папки клиента: anna_2332."""
    return f"{_transliterate(name)}_{digits}"


def extract_first_line(note_text: str) -> str | None:
    """Возвращает первую непустую строку заметки."""
    for line in note_text.splitlines():
        line = line.strip()
        if line:
            return line
    return None


def parse_note(note_text: str) -> dict | None:
    """
    Разбирает заметку и возвращает данные клиента или None.

    Возвращает словарь:
      {
        "raw":          "Анна 2332",
        "name":         "Анна",
        "digits":       "2332",
        "display_name": "Анна 2332",
        "client_id":    "anna_2332",
      }
    """
    first_line = extract_first_line(note_text)
    if not first_line:
        return None

    parsed = parse_client_string(first_line)
    if not parsed:
        return None

    name, digits = parsed
    return {
        "raw": first_line,
        "name": name,
        "digits": digits,
        "display_name": f"{name} {digits}",
        "client_id": build_client_id(name, digits),
    }
