"""Тесты для pdf_maker.core.replace_first_page."""
import sys
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pdf_maker.core import PdfReplaceError, replace_first_page


def _make_pdf(path: Path, page_count: int, size=(200, 200)) -> None:
    """Создаёт простой PDF с заданным числом пустых страниц заданного размера."""
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=size[0], height=size[1])
    with open(path, "wb") as f:
        writer.write(f)


def test_replace_first_page_success(tmp_path):
    source = tmp_path / "source.pdf"
    replacement = tmp_path / "replacement.pdf"
    output = tmp_path / "output.pdf"

    _make_pdf(source, page_count=3, size=(200, 200))
    _make_pdf(replacement, page_count=1, size=(300, 300))

    replace_first_page(source, replacement, output)

    reader = PdfReader(str(output))
    assert len(reader.pages) == 3
    # первая страница — из файла замены (другой размер)
    assert float(reader.pages[0].mediabox.width) == 300
    # остальные страницы — из исходного файла
    assert float(reader.pages[1].mediabox.width) == 200
    assert float(reader.pages[2].mediabox.width) == 200


def test_replacement_must_have_exactly_one_page(tmp_path):
    source = tmp_path / "source.pdf"
    replacement = tmp_path / "replacement.pdf"
    output = tmp_path / "output.pdf"

    _make_pdf(source, page_count=2)
    _make_pdf(replacement, page_count=2)

    with pytest.raises(PdfReplaceError):
        replace_first_page(source, replacement, output)


def test_missing_source_file_raises(tmp_path):
    replacement = tmp_path / "replacement.pdf"
    output = tmp_path / "output.pdf"
    _make_pdf(replacement, page_count=1)

    with pytest.raises(PdfReplaceError):
        replace_first_page(tmp_path / "does_not_exist.pdf", replacement, output)


def test_missing_replacement_file_raises(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "output.pdf"
    _make_pdf(source, page_count=1)

    with pytest.raises(PdfReplaceError):
        replace_first_page(source, tmp_path / "does_not_exist.pdf", output)


def test_single_page_source(tmp_path):
    """Если у источника всего 1 страница, результат — только новая страница."""
    source = tmp_path / "source.pdf"
    replacement = tmp_path / "replacement.pdf"
    output = tmp_path / "output.pdf"

    _make_pdf(source, page_count=1, size=(200, 200))
    _make_pdf(replacement, page_count=1, size=(300, 300))

    replace_first_page(source, replacement, output)

    reader = PdfReader(str(output))
    assert len(reader.pages) == 1
    assert float(reader.pages[0].mediabox.width) == 300
