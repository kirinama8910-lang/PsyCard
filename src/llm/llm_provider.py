"""Клиент Claude API: отправка заметки, получение и валидация структурированного JSON."""

import json
import os
from datetime import datetime

import anthropic
from dotenv import load_dotenv

from src.llm.prompt_loader import load_prompt, build_inline_prompt
from src.llm.response_validator import LLMResponse
from src.paths import LOGS_DIR

load_dotenv()

MODEL = "claude-sonnet-4-6"

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY не задан. "
                "Создайте файл .env и добавьте ANTHROPIC_API_KEY=ваш_ключ"
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def send_to_claude(note_text: str, task_type: str) -> dict:
    """
    Отправляет заметку в Claude и возвращает структурированный результат.

    Возвращает:
        {"ok": True, "data": {...LLMResponse dict...}}
        или
        {"ok": False, "error": "...", "raw": "..."}
    """
    prompt_template = load_prompt(task_type)
    if prompt_template:
        user_message = f"{prompt_template}\n\nТекст заметки:\n{note_text}"
    else:
        user_message = build_inline_prompt(task_type, note_text)

    raw = ""
    try:
        client = _get_client()
        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = message.content[0].text.strip()

        # Убираем markdown-блоки если Claude их добавил
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:]).rsplit("```", 1)[0].strip()

        parsed = json.loads(raw)
        validated = LLMResponse(**parsed)
        return {"ok": True, "data": validated.model_dump()}

    except json.JSONDecodeError as e:
        _write_error_log(task_type, str(e), raw)
        return {"ok": False, "error": f"Claude вернул невалидный JSON: {e}", "raw": raw}

    except Exception as e:
        _write_error_log(task_type, str(e), raw)
        return {"ok": False, "error": str(e), "raw": raw}


def _write_error_log(task_type: str, error: str, raw: str) -> None:
    """Записывает ошибку LLM в дневной лог-файл (.jsonl)."""
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        entry = {
            "ts":        datetime.now().isoformat(),
            "type":      "llm_error",
            "task_type": task_type,
            "error":     error,
            "raw":       raw[:500],
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Логирование не должно падать само по себе
