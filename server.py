"""
FastAPI-сервер psy-client-cards.
Запуск: python server.py
Документация: http://127.0.0.1:8000/docs
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.paths import ensure_project_dirs, CLIENTS_DIR, LOGS_DIR
from src.note_parser import parse_note
from src.docx.template_manager import (
    template_exists,
    client_exists,
    create_client_card,
    find_client_card,
)
from src.docx.docx_reader import read_card, read_card_rows
from src.docx.docx_writer import write_card
from src.backup.backup_manager import create_backup
from src.preview.diff_view import build_preview_summary
from src.llm.llm_provider import send_to_claude

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="psy-client-cards API", version="0.1.0")

# CORS — обязательно для доступа из file:// или другого порта
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаём папки при старте сервера
ensure_project_dirs()


# ── Pydantic-модели запросов ──────────────────────────────────────────────────

class ClientPayload(BaseModel):
    """Стандартный payload, который отправляет фронтенд через collectPayload()."""
    clientKey:      str  = ""
    taskType:       str  = "intake_create_or_update"
    noteText:       str  = ""
    activeClientId: str  = ""
    previewCard:    dict | None = None


class FindOrCreateRequest(BaseModel):
    client_key: str
    task_type:  str = "intake_create_or_update"


class BackupRequest(BaseModel):
    client_key: str = ""
    clientKey:  str = ""  # алиас для фронтенда

    def resolve_client_key(self) -> str:
        return self.client_key or self.clientKey


# ── Вспомогательные функции ───────────────────────────────────────────────────

def _write_action_log(client_key: str, action: str, task_type: str, **kwargs) -> None:
    """Записывает действие в дневной лог-файл (.jsonl)."""
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        entry = {
            "ts":         datetime.now().isoformat(),
            "client":     client_key,
            "action":     action,
            "task_type":  task_type,
            **kwargs,
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _build_empty_card(display_name: str) -> dict:
    """Возвращает пустой объект карты в формате фронтенда."""
    return {
        "passport":    {"clientDisplayName": display_name, "man": "", "child": "", "woman": ""},
        "agreements":  {"frequencyDuration": "", "cost": "", "rules": "", "other": ""},
        "therapyCore": {
            "complaints": "", "request": "", "therapyTargets": "",
            "therapyNotes": "", "completionCriteria": "", "completionNotes": "",
        },
        "notes": {
            "personalityType": "", "educationProfession": "", "familyComposition": "",
            "chronicDiseases": "", "psychiatristObservations": "",
            "father": "", "mother": "", "siblings": "", "children": "",
            "importantBiography": "",
        },
        "plan": {
            "hypotheses": "",
            "stages": {str(i): {"plan": "", "implementation": []} for i in range(1, 6)},
        },
        "logs": {"registrationMeetings": [], "sessionNotes": []},
        "meta": {"createdAt": datetime.now().strftime("%Y-%m-%d")},
    }


def _docx_to_card(card_path: Path, display_name: str) -> dict:
    """
    Best-effort конвертация секций .docx в объект карты фронтенда.
    Если что-то не читается — возвращает пустую карту.
    """
    card = _build_empty_card(display_name)
    try:
        sections = read_card(card_path)

        # Жалобы и запрос
        complaints_rows = sections.get("Жалобы:", [])
        for row in complaints_rows:
            if len(row) >= 2:
                card["therapyCore"]["complaints"] = row[0]
                card["therapyCore"]["request"]    = row[1]
                break
            elif len(row) == 1:
                card["therapyCore"]["complaints"] = row[0]
                break

        # Мишени терапии
        targets_rows = sections.get("Мишени терапии:", [])
        if targets_rows:
            card["therapyCore"]["therapyTargets"] = "\n".join(
                " | ".join(r) for r in targets_rows if r
            )

        # ЗАМЕТКИ
        notes_rows = sections.get("ЗАМЕТКИ", [])
        if notes_rows:
            card["notes"]["importantBiography"] = "\n".join(
                " | ".join(r) for r in notes_rows[:5] if r
            )

        # ПЛАН РАБОТЫ
        plan_rows = sections.get("ПЛАН РАБОТЫ:", [])
        if plan_rows:
            card["plan"]["hypotheses"] = "\n".join(
                " | ".join(r) for r in plan_rows[:8] if r
            )

        # Регистрация встреч
        meetings_rows = sections.get("Регистрация встреч:", [])
        meetings = []
        for row in meetings_rows[:10]:
            if any(row):
                meetings.append({
                    "date":      row[0] if len(row) > 0 else "",
                    "topic":     row[1] if len(row) > 1 else "",
                    "exercises": row[2] if len(row) > 2 else "",
                })
        if meetings:
            card["logs"]["registrationMeetings"] = meetings

        # Примечания по встречам
        notes_rows_s = sections.get("Примечания по встречам:", [])
        session_notes = []
        for row in notes_rows_s[:10]:
            if any(row):
                session_notes.append({
                    "date":        row[0] if len(row) > 0 else "",
                    "content":     row[1] if len(row) > 1 else "",
                    "observation": row[2] if len(row) > 2 else "",
                })
        if session_notes:
            card["logs"]["sessionNotes"] = session_notes

        # meta: дата создания файла
        card["meta"]["createdAt"] = datetime.fromtimestamp(
            card_path.stat().st_mtime
        ).strftime("%Y-%m-%d")

    except Exception as e:
        log.warning("Не удалось прочитать карту %s: %s", card_path.name, e)

    return card


# ── Эндпоинты ─────────────────────────────────────────────────────────────────

# Сканирует data/clients/ и возвращает список клиентов в формате фронтенда
@app.get("/api/clients")
def get_clients() -> list[dict]:
    if not CLIENTS_DIR.exists():
        return []

    clients = []
    for client_dir in sorted(CLIENTS_DIR.iterdir()):
        if not client_dir.is_dir():
            continue

        docx_files = sorted(client_dir.glob("*.docx"))
        if not docx_files:
            continue

        card_path    = docx_files[0]
        display_name = card_path.stem        # "Анна 2332" из "Анна 2332.docx"
        client_id    = client_dir.name       # "anna_2332"

        card = _docx_to_card(card_path, display_name)

        note_count = len([
            n for n in card["logs"]["sessionNotes"]
            if n.get("content") or n.get("date")
        ])

        clients.append({
            "id":          client_id,
            "displayName": display_name,
            "shortStatus": "Активная карта",
            "genderAge":   card["passport"].get("woman") or card["passport"].get("man") or "",
            "noteCount":   note_count,
            "card":        card,
        })

    return clients


# Валидирует клиента, находит или создаёт папку и карту по шаблону
@app.post("/api/find-or-create-card")
def find_or_create_card(payload: ClientPayload) -> dict:
    client_key = payload.clientKey.strip()
    if not client_key:
        raise HTTPException(400, "clientKey не может быть пустым")

    parsed = parse_note(client_key)
    if not parsed:
        raise HTTPException(
            400,
            f"Формат клиента не распознан: '{client_key}'. Ожидается 'Имя 1234'."
        )

    client_id    = parsed["client_id"]
    display_name = parsed["display_name"]
    already      = client_exists(client_id)
    created      = False

    if not already:
        if not template_exists():
            raise HTTPException(
                503,
                "Шаблон карты отсутствует. "
                "Поместите card_template.docx в data/templates/."
            )
        create_client_card(client_id, display_name)
        created = True

    card_path = find_client_card(client_id, display_name)
    card      = _docx_to_card(card_path, display_name) if card_path else _build_empty_card(display_name)

    _write_action_log(client_key, "find_or_create", payload.taskType, created=created)

    return {
        "ok":          True,
        "client_id":   client_id,
        "displayName": display_name,
        "created":     created,
        "card":        card,
    }


# Отправляет заметку в Claude, возвращает структурированный JSON
@app.post("/api/send-to-llm")
def send_to_llm(payload: ClientPayload) -> dict:
    if not payload.noteText.strip():
        raise HTTPException(400, "noteText не может быть пустым")

    result = send_to_claude(payload.noteText, payload.taskType)

    _write_action_log(
        payload.clientKey, "send_to_llm", payload.taskType,
        ok=result["ok"],
        error=result.get("error", ""),
    )

    if not result["ok"]:
        raise HTTPException(502, result.get("error", "Ошибка LLM"))

    return {
        "ok":             True,
        "task_type":      payload.taskType,
        "client_key":     payload.clientKey,
        "structured_json": result["data"],
    }


# Строит текстовый preview того, что будет записано в карту
@app.post("/api/get-preview")
def get_preview(payload: ClientPayload) -> dict:
    card = payload.previewCard or {}
    summary = build_preview_summary(card, payload.taskType, payload.clientKey)
    return {"ok": True, "summary": summary}


# Создаёт backup + записывает изменения в .docx через safe write
@app.post("/api/save-changes")
def save_changes(payload: ClientPayload) -> dict:
    client_key = payload.clientKey.strip()
    parsed = parse_note(client_key)
    if not parsed:
        raise HTTPException(400, f"Не удалось определить клиента: '{client_key}'")

    client_id    = parsed["client_id"]
    display_name = parsed["display_name"]

    # 1. Backup
    backup_path = create_backup(client_id)

    # 2. Найти карту
    card_path = find_client_card(client_id, display_name)
    if not card_path:
        raise HTTPException(404, f"Карта клиента не найдена: {client_id}")

    # 3. Записать изменения
    card = payload.previewCard or {}
    sections_updated = write_card(card_path, card)

    _write_action_log(
        client_key, "save_changes", payload.taskType,
        backup=str(backup_path) if backup_path else None,
        sections_updated=sections_updated,
    )

    return {
        "ok":               True,
        "backup_path":      str(backup_path) if backup_path else None,
        "sections_updated": sections_updated,
    }


# Создаёт backup текущей карты по запросу
@app.post("/api/create-backup")
def create_backup_endpoint(payload: ClientPayload) -> dict:
    client_key = payload.clientKey.strip()
    parsed = parse_note(client_key) if client_key else None

    if not parsed and payload.activeClientId:
        client_id = payload.activeClientId
    elif parsed:
        client_id = parsed["client_id"]
    else:
        raise HTTPException(400, "Не удалось определить клиента")

    backup_path = create_backup(client_id)

    if not backup_path:
        raise HTTPException(404, f"Карта клиента не найдена: {client_id}")

    _write_action_log(client_key or client_id, "backup", payload.taskType,
                      backup=str(backup_path))

    return {"ok": True, "backup_path": str(backup_path)}


# Отдаёт .docx файл карты клиента для скачивания
@app.get("/api/download-document")
def download_document(client_id: str = Query(..., description="ID клиента, например anna_2332")) -> FileResponse:
    client_dir = CLIENTS_DIR / client_id
    if not client_dir.exists():
        raise HTTPException(404, f"Папка клиента не найдена: {client_id}")

    docx_files = sorted(client_dir.glob("*.docx"))
    if not docx_files:
        raise HTTPException(404, f"Карта клиента не найдена в папке: {client_id}")

    card_path = docx_files[0]
    return FileResponse(
        path=str(card_path),
        filename=card_path.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


# Возвращает hardcoded демо-JSON для тестирования без Claude API
@app.post("/api/simulate-analysis")
def simulate_analysis(payload: ClientPayload) -> dict:
    client_key = payload.clientKey or "Анна 2332"
    task_type  = payload.taskType  or "intake_create_or_update"

    demo_json = {
        "task_type":        task_type,
        "client_key":       client_key,
        "create_if_missing": True,
        "sections": {
            "Данные клиента": {
                "Пол и возраст": "женщина, 36 лет",
            },
            "Жалобы и запрос": {
                "Жалобы": "Амбивалентные чувства, не понимаю себя, теряю себя при критике",
                "Запрос": "Разобраться в себе",
            },
            "Первичная клиническая картина": {
                "Выявленный симптом":  "ожидание помощи от окружающих",
                "Дополнения из жизни": "незавершённый развод",
            },
            "Мишени терапии": {
                "append_list": [
                    "Нестабильная идентичность при критике",
                    "Экстернальный локус контроля",
                    "Незавершённый развод",
                ]
            },
        },
    }

    return {
        "ok":   True,
        "text": f"Демо-разбор готов для клиента: {client_key}",
        "structured_json": demo_json,
    }


# ── Точка входа ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
