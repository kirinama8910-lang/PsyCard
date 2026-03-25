"""Загрузка промптов из файлов папки prompts/ или корня проекта."""

from pathlib import Path

from src.paths import PROMPTS_DIR, ROOT_DIR

# Соответствие task_type → файл промпта в prompts/
_TASK_PROMPT_FILES: dict[str, str] = {
    "intake_create_or_update": "intake_structuring.md",
    "session_update":          "session_note.md",
    "client_plan_update":      "client_plan.md",
}

# Промпт в корне проекта (имя с пробелом, legacy)
_ROOT_LEGACY_PROMPT = ROOT_DIR / "prompts claude_client_plan.md"


def load_prompt(task_type: str) -> str | None:
    """
    Загружает промпт для задачи.
    Сначала ищет в prompts/, затем — legacy-файл в корне.
    Возвращает текст промпта или None если файл не найден.
    """
    filename = _TASK_PROMPT_FILES.get(task_type)
    if filename:
        path = PROMPTS_DIR / filename
        if path.exists():
            return path.read_text(encoding="utf-8")

    # Fallback: legacy client_plan.md в корне
    if task_type == "client_plan_update" and _ROOT_LEGACY_PROMPT.exists():
        return _ROOT_LEGACY_PROMPT.read_text(encoding="utf-8")

    return None


def build_inline_prompt(task_type: str, note_text: str) -> str:
    """
    Строит инлайн-промпт если файл промпта не найден.
    Используется как запасной вариант для всех task_type.
    """
    task_descriptions = {
        "intake_create_or_update": "первичное заполнение или обновление карты клиента",
        "session_update":          "заметка после терапевтической встречи",
        "client_plan_update":      "обновление плана работы с клиентом",
    }
    description = task_descriptions.get(task_type, task_type)

    return f"""Ты помощник психолога. Задача: {description}.

Текст заметки:
{note_text}

Извлеки структурированные данные и верни строго JSON без markdown-блоков:
{{
  "task_type": "{task_type}",
  "client_key": "<имя и 4 цифры из первой строки>",
  "create_if_missing": true,
  "sections": {{
    "Данные клиента": {{"Пол и возраст": "..."}},
    "Жалобы и запрос": {{"Жалобы": "...", "Запрос": "..."}},
    "Первичная клиническая картина": {{"Выявленный симптом": "..."}}
  }}
}}

Включай только те секции, для которых есть данные в заметке.
Отвечай только JSON, без пояснений.
"""
