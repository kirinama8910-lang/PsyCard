# VERIFY_AND_DEPLOY.md

## Запуск

```bash
# 1. Проверить версию Python (нужна 3.10+)
python --version

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Создать .env с ключом (нужен только для LLM)
# Скопировать .env.example → .env и вставить ключ:
# ANTHROPIC_API_KEY=sk-ant-...

# 4. Запустить сервер
python server.py
# Сервер стартует на http://127.0.0.1:8000

# 5. Открыть фронтенд
# Двойной клик на Frontend_ergonomic_v2.html
# или File → Open в браузере
```

---

## Чеклист проверки

### Сервер

- [ ] В консоли: `Uvicorn running on http://127.0.0.1:8000`
- [ ] Открыть `http://127.0.0.1:8000/docs` — видны все 8 эндпоинтов

### Фронтенд — базовая загрузка

- [ ] Открыть `Frontend_ergonomic_v2.html` — страница загрузилась без ошибок
- [ ] В сайдбаре появился список клиентов из `data/clients/` (не демо-данные)
- [ ] Консоль браузера: нет ошибок `CORS` или `Failed to fetch`

### Сценарий: новый клиент

- [ ] Очистить поле заметки
- [ ] Вставить текст: `Тест 9999\n• Жалобы: тревога`
- [ ] Нажать **"Найти / создать карту"**
- [ ] Toast: "Карта создана"
- [ ] В `data/clients/test_9999/` появился файл `Тест 9999.docx`

### Сценарий: существующий клиент

- [ ] Вставить заметку с именем существующего клиента: `Анна 2332\n• Жалобы: обновлённые данные`
- [ ] Нажать **"Найти / создать карту"**
- [ ] Toast: "Карта найдена"
- [ ] Клиент активировался в сайдбаре

### Preview

- [ ] Нажать **"Просмотр изменений"**
- [ ] В поле preview появился текст с секциями карты (не "Нет изменений")

### Сохранение

- [ ] Нажать **"Сохранить"**
- [ ] Toast: "Изменения сохранены"
- [ ] В `data/backups/anna_2332/` появился backup-файл с timestamp
- [ ] Открыть `data/clients/anna_2332/Анна 2332.docx` в Word — данные обновились

### Скачивание

- [ ] Нажать **"Скачать документ"**
- [ ] Открылась новая вкладка, файл `.docx` скачался

### Backup вручную

- [ ] Нажать **"Резервная копия"**
- [ ] Toast: "Резервная копия"
- [ ] В `data/backups/` появился новый файл

### Демо без LLM

- [ ] Нажать **"Смоделировать разбор"**
- [ ] Toast: "Демо-разбор готов для клиента: ..."

### LLM (требует ANTHROPIC_API_KEY в .env)

- [ ] Вставить заметку, нажать **"Отправить текст в LLM"**
- [ ] Toast: "Текст отправлен в LLM" с типом задачи
- [ ] В `data/logs/YYYY-MM-DD.jsonl` нет записей с `"type": "llm_error"`

### Логи

- [ ] После действий открыть `data/logs/YYYY-MM-DD.jsonl`
- [ ] Есть записи с полями: `ts`, `client`, `action`, `task_type`

---

## Публикация на GitHub

```bash
# Проверить что чувствительные файлы не попадут в коммит
git status

# .env и data/ должны быть в .gitignore
# Проверить:
cat .gitignore

# Добавить новые файлы
git add server.py CHANGELOG.md VERIFY_AND_DEPLOY.md
git add src/docx/docx_writer.py
git add src/llm/ src/backup/ src/preview/
git add requirements.txt Frontend_ergonomic_v2.html PROJECT_SPEC.md

# Создать коммит
git commit -m "feat: connect HTML frontend to FastAPI backend

- Add server.py with 8 REST API endpoints
- Replace demoClients with live GET /api/clients
- Implement all backendApi fetch calls in frontend
- Add docx_writer, llm_provider, backup_manager, diff_view
- Update PROJECT_SPEC.md and add CHANGELOG.md"

git push origin main
```

### Проверка после пуша

- [ ] Открыть GitHub → commits/main — коммит появился
- [ ] Убедиться: `.env`, `data/`, `__pycache__` не попали в репозиторий

---

## Структура папок после запуска

```
psy-client-cards/
├── server.py                    ← FastAPI сервер (python server.py)
├── app.py                       ← Streamlit (исторический, Этап 1)
├── Frontend_ergonomic_v2.html   ← Открыть двойным кликом
├── .env                         ← ANTHROPIC_API_KEY (не в git!)
│
├── data/
│   ├── clients/                 ← Карты клиентов
│   ├── templates/card_template.docx  ← Шаблон карты
│   ├── backups/                 ← Автобэкапы
│   └── logs/                    ← Логи действий (.jsonl)
│
└── src/
    ├── llm/                     ← Claude API
    ├── backup/                  ← Backup менеджер
    ├── preview/                 ← Preview изменений
    └── docx/                    ← Чтение и запись .docx
```
