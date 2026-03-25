"""Генерация текстового preview изменений карты для отображения в интерфейсе."""

from typing import Any


def build_preview_summary(card: dict, task_type: str, client_key: str) -> str:
    """
    Строит текстовый summary того, что будет сохранено в карту.
    card — объект карты в формате фронтенда (previewCard).
    Возвращает строку для отображения в поле preview фронтенда.
    """
    parts: list[str] = []

    if client_key:
        parts.append(f"Клиент: {client_key}")

    task_labels = {
        "intake_create_or_update": "Первичная карта / обновление",
        "session_update":          "Заметка после встречи",
        "client_plan_update":      "Обновление плана",
    }
    parts.append(f"Тип задачи: {task_labels.get(task_type, task_type)}")

    tc = card.get("therapyCore", {})
    pl = card.get("plan", {})
    lo = card.get("logs", {})
    p  = card.get("passport", {})

    def _add(label: str, value: Any, max_len: int = 200) -> None:
        text = str(value).strip()
        if text:
            parts.append(f"{label}: {text[:max_len]}{'...' if len(text) > max_len else ''}")

    _add("Пол и возраст", p.get("woman") or p.get("man") or p.get("child"))
    _add("Жалобы",         tc.get("complaints"))
    _add("Запрос",         tc.get("request"))
    _add("Мишени",         tc.get("therapyTargets"))
    _add("Гипотезы",       pl.get("hypotheses"))

    meetings = [m for m in lo.get("registrationMeetings", []) if m.get("date") or m.get("topic")]
    if meetings:
        m = meetings[0]
        _add("Встреча", f"{m.get('date','')} — {m.get('topic','')}")

    session_notes = [n for n in lo.get("sessionNotes", []) if n.get("content")]
    if session_notes:
        _add("Заметка по встрече", session_notes[0].get("content", ""))

    return "\n".join(parts)
