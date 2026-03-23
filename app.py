"""Главное Streamlit-приложение psy-client-cards (Этап 3)."""

import streamlit as st

from src.config import APP_TITLE
from src.paths import ensure_project_dirs
from src.note_parser import parse_note
from src.client_registry import (
    get_client_dirs,
    get_client_files,
)
from src.docx.template_manager import (
    template_exists,
    client_exists,
    find_client_card,
    create_client_card,
)
from src.docx.docx_reader import read_card, read_card_rows
from src.ui_helpers import (
    render_empty_clients_state,
    render_client_files,
    render_card_contents,
)

# ── Настройка страницы ──────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, layout="centered")

# ── Создание папок при первом запуске ────────────────────────────
created = ensure_project_dirs()

# ── Заголовок ────────────────────────────────────────────────────
st.title(APP_TITLE)
st.caption("Локальное приложение для ведения карт клиентов")

st.divider()

# ── 2. Ввод заметки ─────────────────────────────────────────────
st.header("Заметка")

# Ключ-счётчик для сброса поля
if "note_key" not in st.session_state:
    st.session_state.note_key = 0

note_text = st.text_area(
    "Вставьте заметку. Первая строка — имя клиента и 4 цифры: Анна 2332",
    height=200,
    placeholder="Анна 2332\n• Жалобы: ...\n• Запрос: ...",
    key=f"note_{st.session_state.note_key}",
)

col_submit, col_clear = st.columns([4, 1])
submitted = col_submit.button("Найти / создать карту", type="primary", use_container_width=True)
if col_clear.button("Очистить", use_container_width=True):
    st.session_state.note_key += 1
    st.rerun()

if submitted and note_text.strip():
    client = parse_note(note_text)

    if client is None:
        st.error(
            "Первая строка не распознана. Ожидается формат: **Имя 1234**\n\n"
            "Пример: `Анна 2332` или `Наталья 3445`"
        )
    else:
        # ── Карточка клиента ────────────────────────────────────
        col1, col2 = st.columns(2)
        col1.metric("Клиент", client["display_name"])
        col2.metric("ID папки", client["client_id"])

        already_exists = client_exists(client["client_id"])
        card_path = find_client_card(client["client_id"], client["display_name"])

        if already_exists and card_path:
            st.success(f"Карта найдена: `{card_path.relative_to(card_path.parents[2])}`")
            with open(card_path, "rb") as f:
                st.download_button(
                    label=f"Скачать {card_path.name}",
                    data=f,
                    file_name=card_path.name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            try:
                sections = read_card(card_path)
                all_rows = read_card_rows(card_path)
                st.subheader("Содержимое карты")
                render_card_contents(sections, all_rows)
            except Exception as e:
                st.warning(f"Не удалось прочитать карту: {e}")
        elif already_exists and not card_path:
            st.warning(
                f"Папка клиента существует (`{client['client_id']}/`), "
                "но .docx карта внутри не найдена."
            )
        else:
            st.info("Клиент не найден. Можно создать новую карту.")

            if not template_exists():
                st.error(
                    "Шаблон карты отсутствует.\n\n"
                    "Поместите файл шаблона в:\n"
                    "`data/templates/card_template.docx`"
                )
            else:
                if st.button("Создать карту клиента", type="primary", use_container_width=True):
                    try:
                        new_card = create_client_card(
                            client["client_id"],
                            client["display_name"],
                        )
                        st.success(
                            f"Карта создана: "
                            f"`{new_card.relative_to(new_card.parents[2])}`"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка при создании карты: {e}")

st.divider()

# ── 3. Клиенты ───────────────────────────────────────────────────
st.header("Все клиенты")

client_dirs = get_client_dirs()

if not client_dirs:
    render_empty_clients_state()
else:
    selected_name = st.selectbox(
        "Выберите клиента для просмотра",
        options=[d.name for d in client_dirs],
    )
    if selected_name:
        selected_dir = next(d for d in client_dirs if d.name == selected_name)
        files = get_client_files(selected_dir)
        render_client_files(files)

        # Показываем содержимое карты если есть .docx
        docx_files = [f for f in files if f.suffix == ".docx"]
        if docx_files:
            try:
                sections = read_card(docx_files[0])
                all_rows = read_card_rows(docx_files[0])
                st.subheader("Содержимое карты")
                render_card_contents(sections, all_rows)
            except Exception as e:
                st.warning(f"Не удалось прочитать карту: {e}")

