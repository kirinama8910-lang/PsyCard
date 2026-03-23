"""Модуль путей проекта. Все пути строятся относительно корня через pathlib.Path."""

from pathlib import Path

# Корень проекта — папка, содержащая src/
ROOT_DIR = Path(__file__).resolve().parent.parent

# Основные директории
PROMPTS_DIR = ROOT_DIR / "prompts"
DATA_DIR = ROOT_DIR / "data"
SRC_DIR = ROOT_DIR / "src"
TESTS_DIR = ROOT_DIR / "tests"

# Поддиректории data/
CLIENTS_DIR = DATA_DIR / "clients"
TEMPLATES_DIR = DATA_DIR / "templates"
INBOX_NOTES_DIR = DATA_DIR / "inbox_notes"
AUDIO_ARCHIVE_DIR = DATA_DIR / "audio_archive"
BACKUPS_DIR = DATA_DIR / "backups"
LOGS_DIR = DATA_DIR / "logs"

# Все директории, которые должны существовать
_PROJECT_DIRS = [
    PROMPTS_DIR,
    CLIENTS_DIR,
    TEMPLATES_DIR,
    INBOX_NOTES_DIR,
    AUDIO_ARCHIVE_DIR,
    BACKUPS_DIR,
    LOGS_DIR,
    TESTS_DIR,
]


def ensure_project_dirs() -> list[Path]:
    """Создаёт недостающие папки проекта. Возвращает список созданных."""
    created = []
    for d in _PROJECT_DIRS:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(d)
    return created


def list_expected_dirs() -> dict[str, Path]:
    """Возвращает словарь основных путей проекта (имя → путь)."""
    return {
        "prompts": PROMPTS_DIR,
        "data/clients": CLIENTS_DIR,
        "data/templates": TEMPLATES_DIR,
        "data/inbox_notes": INBOX_NOTES_DIR,
        "data/audio_archive": AUDIO_ARCHIVE_DIR,
        "data/backups": BACKUPS_DIR,
        "data/logs": LOGS_DIR,
        "tests": TESTS_DIR,
    }
