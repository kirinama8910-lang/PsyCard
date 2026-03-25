"""Создание резервных копий карт клиентов перед записью."""

import shutil
from datetime import datetime
from pathlib import Path

from src.paths import BACKUPS_DIR, CLIENTS_DIR


def create_backup(client_id: str) -> Path | None:
    """
    Создаёт backup текущей .docx карты клиента.

    Находит первый .docx в папке клиента, копирует его в:
        data/backups/<client_id>/<client_id>_YYYY-MM-DD_HH-MM-SS.docx

    Возвращает путь к файлу backup, или None если карта не найдена.
    """
    client_dir = CLIENTS_DIR / client_id
    if not client_dir.exists():
        return None

    docx_files = sorted(client_dir.glob("*.docx"))
    if not docx_files:
        return None

    card_path = docx_files[0]

    backup_dir = BACKUPS_DIR / client_id
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = backup_dir / f"{client_id}_{timestamp}.docx"

    shutil.copy2(card_path, backup_path)
    return backup_path
