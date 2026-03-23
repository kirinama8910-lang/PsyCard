"""Управление шаблоном карты: проверка, копирование, создание папки клиента."""

import shutil
from pathlib import Path

from src.paths import CLIENTS_DIR, TEMPLATES_DIR

TEMPLATE_FILE = TEMPLATES_DIR / "card_template.docx"


def template_exists() -> bool:
    """Проверяет, существует ли файл шаблона карты."""
    return TEMPLATE_FILE.exists()


def get_client_dir(client_id: str) -> Path:
    """Возвращает путь к папке клиента (не создаёт)."""
    return CLIENTS_DIR / client_id


def client_exists(client_id: str) -> bool:
    """Проверяет, существует ли папка клиента."""
    return get_client_dir(client_id).exists()


def find_client_card(client_id: str, display_name: str) -> Path | None:
    """
    Ищет .docx карту клиента. Сначала по точному имени,
    затем — первый .docx в папке клиента.
    """
    client_dir = get_client_dir(client_id)
    if not client_dir.exists():
        return None

    exact = client_dir / f"{display_name}.docx"
    if exact.exists():
        return exact

    docx_files = sorted(client_dir.glob("*.docx"))
    return docx_files[0] if docx_files else None


def create_client_card(client_id: str, display_name: str) -> Path:
    """
    Создаёт папку клиента и копирует туда шаблон карты.
    Возвращает путь к созданному файлу.
    Не перезаписывает существующую карту.
    """
    if not template_exists():
        raise FileNotFoundError(
            f"Шаблон карты не найден: {TEMPLATE_FILE}\n"
            "Поместите шаблон в data/templates/card_template.docx"
        )

    client_dir = get_client_dir(client_id)
    client_dir.mkdir(parents=True, exist_ok=True)

    card_path = client_dir / f"{display_name}.docx"
    if card_path.exists():
        return card_path

    shutil.copy2(TEMPLATE_FILE, card_path)
    return card_path
