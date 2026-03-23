"""Просмотр клиентских папок и обнаружение файлов вне структуры."""

from pathlib import Path

from src.paths import CLIENTS_DIR, ROOT_DIR
from src.docx.template_manager import client_exists, find_client_card, create_client_card

# Файлы в корне, которые являются частью проекта и не требуют предупреждений
_SYSTEM_ROOT_FILES = {
    "app.py",
    "PROJECT_SPEC.md",
    "README.md",
    "requirements.txt",
    ".env",
    ".env.example",
    ".gitignore",
}


def get_client_dirs() -> list[Path]:
    """Возвращает список папок клиентов из data/clients/."""
    if not CLIENTS_DIR.exists():
        return []
    return sorted(
        [d for d in CLIENTS_DIR.iterdir() if d.is_dir()],
        key=lambda p: p.name,
    )


def get_client_files(client_dir: Path) -> list[Path]:
    """Возвращает список файлов внутри папки клиента."""
    if not client_dir.exists() or not client_dir.is_dir():
        return []
    return sorted(
        [f for f in client_dir.iterdir() if f.is_file()],
        key=lambda p: p.name,
    )


def find_root_level_docx_files() -> list[Path]:
    """Находит .docx файлы в корне проекта."""
    return sorted(ROOT_DIR.glob("*.docx"))


def find_root_level_md_or_txt_files() -> list[Path]:
    """Находит .md и .txt файлы в корне проекта, кроме системных файлов проекта."""
    result = []
    for pattern in ("*.md", "*.txt"):
        for f in ROOT_DIR.glob(pattern):
            if f.name not in _SYSTEM_ROOT_FILES:
                result.append(f)
    return sorted(result)
