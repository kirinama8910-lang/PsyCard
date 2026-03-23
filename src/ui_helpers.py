"""Вспомогательные функции для Streamlit-интерфейса."""

from pathlib import Path

import streamlit as st

from src.docx.section_mapper import SECTION_LABELS, SECTION_DISPLAY
from src.docx.docx_reader import find_field_value


def render_project_paths(dirs: dict[str, Path]) -> None:
    """Отображает основные пути проекта и их статус."""
    for name, path in dirs.items():
        exists = path.exists()
        icon = "✅" if exists else "❌"
        st.text(f"  {icon} {name}/")


def render_empty_clients_state() -> None:
    """Сообщение, когда клиентских папок нет."""
    st.info(
        "Папка data/clients/ пока пуста.\n\n"
        "Когда появятся клиенты, их карты будут храниться в отдельных подпапках:\n"
        "  data/clients/anna_2332/Анна 2332.docx"
    )


def render_root_warnings(
    docx_files: list[Path],
    extra_text_files: list[Path],
) -> None:
    """Показывает предупреждения о файлах, лежащих вне правильной структуры."""
    if docx_files:
        st.warning("**В корне проекта найдены .docx файлы:**")
        for f in docx_files:
            st.text(f"  • {f.name}")
        st.caption(
            "Рекомендация: переместите карты клиентов в data/clients/<client_id>/\n"
            "Шаблон карты — в data/templates/card_template.docx"
        )

    if extra_text_files:
        st.warning("**В корне проекта найдены текстовые/md файлы вне стандартной структуры:**")
        for f in extra_text_files:
            st.text(f"  • {f.name}")
        st.caption(
            "Рекомендация: промпт-файлы переместите в prompts/"
        )


def render_client_files(files: list[Path]) -> None:
    """Отображает список файлов выбранного клиента с кнопками скачивания."""
    if not files:
        st.info("В этой папке пока нет файлов.")
        return
    for f in files:
        col1, col2 = st.columns([3, 1])
        col1.markdown(f"📄 {f.name}")
        if f.suffix == ".docx":
            with open(f, "rb") as fh:
                col2.download_button(
                    label="Скачать",
                    data=fh,
                    file_name=f.name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=str(f),
                )
        else:
            col2.empty()


def render_card_contents(
    sections: dict[str, list[list[str]]],
    all_rows: list[list[str]] | None = None,
) -> None:
    """Отображает содержимое карты клиента по секциям."""

    def _rows_to_text(rows: list[list[str]]) -> str:
        return "\n".join("  |  ".join(row) for row in rows).strip()

    # Секции, которые читаются как заголовок одной ячейки
    simple_sections = [
        "client_info",
        "agreements",
        "notes",
        "plan",
        "session_log",
        "session_notes",
    ]

    for key in simple_sections:
        label = SECTION_LABELS.get(key, key)
        display = SECTION_DISPLAY.get(key, key)
        rows = sections.get(label, [])
        content = _rows_to_text(rows)
        with st.expander(display, expanded=(key == "client_info")):
            if content:
                st.text(content)
            else:
                st.caption("Нет данных")

    # Жалобы и запрос — строка с 2 ячейками, ищем линейно
    with st.expander("Жалобы и запрос", expanded=True):
        if all_rows:
            data = find_field_value(all_rows, "Жалобы:")
            if data:
                for row in data:
                    cols = st.columns(len(row))
                    headers = ["Жалобы", "Запрос"]
                    for i, (col, cell) in enumerate(zip(cols, row)):
                        col.markdown(f"**{headers[i] if i < len(headers) else ''}**")
                        col.write(cell)
            else:
                st.caption("Нет данных")
        else:
            st.caption("Нет данных")

    # Мишени терапии
    with st.expander("Мишени терапии", expanded=False):
        if all_rows:
            data = find_field_value(all_rows, "Мишени терапии:")
            content = _rows_to_text(data)
            if content:
                st.text(content)
            else:
                st.caption("Нет данных")
        else:
            st.caption("Нет данных")


def render_info_block() -> None:
    """Блок-подсказка по правильной структуре хранения файлов."""
    st.markdown(
        """
**Правильная структура хранения:**

| Что | Куда |
|---|---|
| Карты клиентов | `data/clients/<client_id>/Имя 1234.docx` |
| Шаблон карты | `data/templates/card_template.docx` |
| Промпт-файлы | `prompts/` |
| Входящие заметки | `data/inbox_notes/` |
| Аудиозаписи | `data/audio_archive/` |
| Бэкапы | `data/backups/` |
| Логи | `data/logs/` |
"""
    )
