"""Логика работы с PDF: замена первого листа документа.

Не зависит от GUI — можно использовать и из командной строки, и из тестов.
"""
from pathlib import Path
from typing import Union

from pypdf import PdfReader, PdfWriter

PathLike = Union[str, Path]


class PdfReplaceError(Exception):
    """Ошибка при замене страницы PDF (некорректные файлы, неверное число страниц и т.п.)."""


def replace_first_page(
    source_pdf: PathLike,
    replacement_pdf: PathLike,
    output_pdf: PathLike,
) -> None:
    """Заменяет первую страницу ``source_pdf`` на единственную страницу
    ``replacement_pdf`` и сохраняет результат в ``output_pdf``.

    :param source_pdf: путь к исходному многостраничному PDF.
    :param replacement_pdf: путь к PDF, содержащему ровно одну страницу —
        именно она станет новой первой страницей результата.
    :param output_pdf: путь, по которому будет сохранён итоговый PDF.
    :raises PdfReplaceError: если один из файлов не найден, не открывается
        как PDF, исходный файл пуст или файл замены содержит не ровно одну
        страницу.
    """
    source_path = Path(source_pdf)
    replacement_path = Path(replacement_pdf)

    if not source_path.exists():
        raise PdfReplaceError(f"Исходный файл не найден: {source_path}")
    if not replacement_path.exists():
        raise PdfReplaceError(f"Файл замены не найден: {replacement_path}")

    try:
        source_reader = PdfReader(str(source_path))
    except Exception as exc:  # noqa: BLE001 — сообщаем пользователю понятную причину
        raise PdfReplaceError(f"Не удалось открыть исходный PDF: {exc}") from exc

    try:
        replacement_reader = PdfReader(str(replacement_path))
    except Exception as exc:  # noqa: BLE001
        raise PdfReplaceError(f"Не удалось открыть PDF замены: {exc}") from exc

    if len(source_reader.pages) == 0:
        raise PdfReplaceError("Исходный PDF не содержит страниц")

    if len(replacement_reader.pages) != 1:
        raise PdfReplaceError(
            "Файл замены должен содержать ровно 1 страницу, "
            f"а содержит {len(replacement_reader.pages)}"
        )

    writer = PdfWriter()
    writer.add_page(replacement_reader.pages[0])
    for page in source_reader.pages[1:]:
        writer.add_page(page)

    output_path = Path(output_pdf)
    if output_path.parent:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        writer.write(f)
