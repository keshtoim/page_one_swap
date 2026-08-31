"""PDF Maker: утилита для замены первого листа PDF-документа."""

from pdf_maker.core import PdfReplaceError, replace_first_page

__all__ = ["replace_first_page", "PdfReplaceError"]
