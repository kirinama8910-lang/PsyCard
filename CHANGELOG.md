# CHANGELOG

## [2026-03-25] — Интеграция HTML-фронтенда + FastAPI бэкенда

### Архитектурное решение

**Проблема:** фронтенд (`Frontend_ergonomic_v2.html`) ожидает REST API, бэкенд написан на Streamlit и не предоставляет никакого API.

**Решение:** добавлен FastAPI-сервер (`server.py`) на порту `8000`. HTML открывается двойным кликом как статический файл в браузере. CORS настроен на `allow_origins=["*"]` — обязательно для запросов из `file://`.

**Почему именно так:** FastAPI — стандарт для Python REST API, минимум кода, встроенная документация (`/docs`), нативная поддержка Pydantic v2. Streamlit остаётся как вспомогательный интерфейс Этапа 1 и не удаляется.

---

### Добавлено

- **`server.py`** — FastAPI-сервер с 8 эндпоинтами. Единая точка входа: `python server.py`
- **`src/docx/docx_writer.py`** — запись данных карты из фронтенда в `.docx` таблицу. Safe write через временный `.tmp` файл → замена оригинала.
- **`src/llm/llm_provider.py`** — клиент Claude API (`claude-sonnet-4-6`). Отправляет заметку, получает JSON, валидирует через Pydantic, логирует ошибки.
- **`src/llm/prompt_loader.py`** — загружает промпты из `prompts/*.md`. Fallback: inline-промпт если файл не найден. Legacy: читает `prompts claude_client_plan.md` из корня.
- **`src/llm/response_validator.py`** — Pydantic v2 схема `LLMResponse`. Валидирует `task_type`, `client_key`, `sections`.
- **`src/backup/backup_manager.py`** — создаёт backup в `data/backups/<client_id>/<client_id>_YYYY-MM-DD_HH-MM-SS.docx`.
- **`src/preview/diff_view.py`** — строит текстовый summary изменений (что будет записано в карту).
- **`src/llm/__init__.py`**, **`src/backup/__init__.py`**, **`src/preview/__init__.py`** — инит-файлы новых пакетов.

### Изменено

- **`Frontend_ergonomic_v2.html`** — заменены все 7 заглушек `console.log("TODO...")` на реальные `fetch`-вызовы через хелпер `apiFetch()`. Добавлены `loadClientsFromBackend()` и обновлён `bootstrap()` для загрузки клиентов при старте. Если сервер недоступен — автоматический fallback на `demoClients`.
- **`requirements.txt`** — добавлены: `fastapi`, `uvicorn`, `anthropic`, `python-dotenv`, `pydantic`.
- **`PROJECT_SPEC.md`** — добавлены разделы: REST API эндпоинты, фронтенд, обновлена архитектура, статусы этапов.

### Переиспользовано без изменений

- `src/paths.py` — все пути, `ensure_project_dirs()`
- `src/note_parser.py` — парсинг первой строки, `parse_note()`
- `src/validators.py` — regex-валидация формата `Имя 1234`
- `src/docx/template_manager.py` — создание папки и карты клиента
- `src/docx/docx_reader.py` — чтение таблицы карты
- `src/docx/section_mapper.py` — справочник меток секций
- `src/client_registry.py` — список клиентских папок
- `src/config.py` — константы приложения

### Известные ограничения

- `docx_writer.py` пишет только в **первую ячейку данных** каждой секции. Для секций с несколькими строками (логи встреч, реализация этапов) полная поддержка запланирована на Этап 6.
- LLM-ответ (`send-to-llm`) возвращается фронтенду, но фронтенд использует только `task_type` в toast. Применение LLM-результата к карте — Этап 4 (расширение фронтенда).
- Голосовой ввод — Этап 5.
- Streamlit (`app.py`) оставлен как исторический интерфейс и не синхронизируется с FastAPI.
