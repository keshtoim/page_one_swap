"""Графический интерфейс приложения для замены первого листа PDF (Tkinter)."""
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from pdf_maker.config import load_output_folder, save_output_folder
from pdf_maker.core import PdfReplaceError, replace_first_page

# -- цветовая палитра ------------------------------------------------------
BG = "#f4f6fb"
CARD_BG = "#ffffff"
BORDER = "#e2e5ee"
TEXT_DARK = "#1f2430"
TEXT_MUTED = "#6b7280"
ACCENT = "#3b6fed"
ACCENT_DARK = "#2c56c4"
ACCENT_DISABLED = "#aebdf0"
SUCCESS = "#1a7f37"
ERROR = "#c62828"


class PdfMakerApp(tk.Tk):
    """Главное окно приложения."""

    def __init__(self) -> None:
        super().__init__()
        self.title("PDF Maker — замена первого листа")
        self.configure(bg=BG)

        self.source_path = tk.StringVar()
        self.replacement_path = tk.StringVar()
        self.output_folder = tk.StringVar(value=str(load_output_folder()))
        self.output_filename = tk.StringVar(value="result.pdf")

        self._last_output_path: Optional[Path] = None

        self._setup_style()
        self._setup_clipboard()
        self._build_ui()
        self._fit_and_center_window()

    # -- стиль ---------------------------------------------------------
    def _setup_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD_BG)

        style.configure("TLabel", background=BG, foreground=TEXT_DARK, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT_DARK, font=("Segoe UI", 10))
        style.configure("CardBold.TLabel", background=CARD_BG, foreground=TEXT_DARK, font=("Segoe UI", 10, "bold"))
        style.configure("Muted.TLabel", background=BG, foreground=TEXT_MUTED, font=("Segoe UI", 9))
        style.configure("CardMuted.TLabel", background=CARD_BG, foreground=TEXT_MUTED, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=BG, foreground=TEXT_DARK, font=("Segoe UI", 18, "bold"))
        style.configure("Status.TLabel", background=BG, font=("Segoe UI", 9))

        style.configure("TEntry", padding=6, fieldbackground="#ffffff", bordercolor=BORDER)
        style.configure(
            "TButton",
            padding=(10, 6),
            font=("Segoe UI", 9),
            background="#e7eaf3",
            foreground=TEXT_DARK,
            borderwidth=0,
        )
        style.map("TButton", background=[("active", "#d9deee")])

        style.configure(
            "Accent.TButton",
            padding=(14, 10),
            font=("Segoe UI", 11, "bold"),
            background=ACCENT,
            foreground="#ffffff",
            borderwidth=0,
        )
        style.map(
            "Accent.TButton",
            background=[("active", ACCENT_DARK), ("disabled", ACCENT_DISABLED)],
            foreground=[("disabled", "#eef1fc")],
        )

        style.configure(
            "Card.TLabelframe",
            background=CARD_BG,
            bordercolor=BORDER,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=CARD_BG,
            foreground=TEXT_DARK,
            font=("Segoe UI", 10, "bold"),
        )

    def _setup_clipboard(self) -> None:
        """Ctrl+C/X/V при любой раскладке и контекстное меню во всех полях ввода.

        Штатные биндинги Tk завязаны на keysym, а при русской раскладке
        вместо «v» приходит «Cyrillic_em» — вставка молча не работает.
        Поэтому дополнительно ловим физическую клавишу по keycode.
        """
        keycode_events = {86: "<<Paste>>", 67: "<<Copy>>", 88: "<<Cut>>"}  # V, C, X

        def on_ctrl_key(event: tk.Event) -> Optional[str]:
            virtual = keycode_events.get(event.keycode)
            # латинскую раскладку уже обработал штатный биндинг Tk
            if virtual and event.keysym.lower() not in ("v", "c", "x"):
                event.widget.event_generate(virtual)
                return "break"
            return None

        self._entry_menu = tk.Menu(self, tearoff=False)
        for label, virtual in (("Вырезать", "<<Cut>>"), ("Копировать", "<<Copy>>"), ("Вставить", "<<Paste>>")):
            self._entry_menu.add_command(
                label=label, command=lambda v=virtual: self.focus_get().event_generate(v)
            )

        def show_menu(event: tk.Event) -> None:
            event.widget.focus_set()
            self._entry_menu.tk_popup(event.x_root, event.y_root)

        self.bind_class("TEntry", "<Control-KeyPress>", on_ctrl_key, add="+")
        self.bind_class("TEntry", "<Button-3>", show_menu, add="+")

    def _fit_and_center_window(self) -> None:
        """Подгоняет размер окна под реальное содержимое (с запасом) и центрирует его.

        Фиксированный размер окна ломался на разных DPI/масштабах экрана —
        низ окна обрезался. Вместо этого меряем требуемый размер после
        построения интерфейса и берём его с запасом.
        """
        self.update_idletasks()
        width = max(self.winfo_reqwidth() + 20, 640)
        height = self.winfo_reqheight() + 30
        self.minsize(width, height)
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 3
        self.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")

    # -- построение интерфейса ------------------------------------------
    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)

        self._build_header(container)

        files_card = self._make_card(container, "1. Выберите файлы")
        self._add_file_row(
            files_card,
            label="Исходный PDF",
            hint="Документ, у которого будет заменена первая страница",
            var=self.source_path,
            browse_command=self._browse_source,
        )
        self._add_file_row(
            files_card,
            label="Новый лист (PDF, ровно 1 страница)",
            hint="Эта страница станет новой первой страницей результата",
            var=self.replacement_path,
            browse_command=self._browse_replacement,
            last=True,
        )

        save_card = self._make_card(container, "2. Куда сохранить результат")
        self._build_save_section(save_card)

        self._build_action_and_status(container)

    def _build_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent)
        header.pack(fill="x", pady=(0, 16))
        ttk.Label(header, text="📄  PDF Maker", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Заменяет первый лист PDF-документа страницей из другого файла",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 0))

    def _make_card(self, parent: ttk.Frame, title: str) -> ttk.LabelFrame:
        card = ttk.LabelFrame(parent, text=title, style="Card.TLabelframe", padding=16)
        card.pack(fill="x", pady=(0, 16))
        return card

    def _add_file_row(self, card, label, hint, var, browse_command, last=False) -> None:
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x", pady=(0, 0 if last else 14))

        ttk.Label(row, text=label, style="CardBold.TLabel").pack(anchor="w")
        ttk.Label(row, text=hint, style="CardMuted.TLabel").pack(anchor="w", pady=(0, 4))

        inner = ttk.Frame(row, style="Card.TFrame")
        inner.pack(fill="x")
        inner.columnconfigure(0, weight=1)

        entry = ttk.Entry(inner, textvariable=var)
        entry.grid(row=0, column=0, sticky="we", padx=(0, 8))
        ttk.Button(inner, text="Обзор…", command=browse_command).grid(row=0, column=1)

    def _build_save_section(self, card: ttk.LabelFrame) -> None:
        folder_row = ttk.Frame(card, style="Card.TFrame")
        folder_row.pack(fill="x", pady=(0, 14))
        ttk.Label(folder_row, text="Папка сохранения", style="CardBold.TLabel").pack(anchor="w")
        ttk.Label(
            folder_row,
            text="Файл будет сохранён в эту папку — она запоминается для следующего раза",
            style="CardMuted.TLabel",
        ).pack(anchor="w", pady=(0, 4))

        folder_inner = ttk.Frame(folder_row, style="Card.TFrame")
        folder_inner.pack(fill="x")
        folder_inner.columnconfigure(0, weight=1)
        folder_entry = ttk.Entry(folder_inner, textvariable=self.output_folder, state="readonly")
        folder_entry.grid(row=0, column=0, sticky="we", padx=(0, 8))
        ttk.Button(folder_inner, text="Изменить папку…", command=self._browse_output_folder).grid(
            row=0, column=1
        )

        name_row = ttk.Frame(card, style="Card.TFrame")
        name_row.pack(fill="x")
        ttk.Label(name_row, text="Имя нового файла", style="CardBold.TLabel").pack(anchor="w")
        ttk.Label(
            name_row, text="Расширение .pdf добавится автоматически, если не указано", style="CardMuted.TLabel"
        ).pack(anchor="w", pady=(0, 4))
        ttk.Entry(name_row, textvariable=self.output_filename).pack(fill="x")

    def _build_action_and_status(self, parent: ttk.Frame) -> None:
        action_row = ttk.Frame(parent)
        action_row.pack(fill="x", pady=(8, 12))
        self.run_button = ttk.Button(
            action_row,
            text="Заменить и сохранить",
            style="Accent.TButton",
            command=self._run,
        )
        self.run_button.pack(fill="x")

        status_row = ttk.Frame(parent)
        status_row.pack(fill="x")
        self.status_var = tk.StringVar(
            value="Выберите файлы и папку сохранения, затем нажмите «Заменить и сохранить»."
        )
        self.status_label = ttk.Label(
            status_row,
            textvariable=self.status_var,
            style="Status.TLabel",
            foreground=TEXT_MUTED,
            wraplength=560,
            justify="left",
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        self.open_folder_button = ttk.Button(
            status_row, text="Открыть папку", command=self._open_output_folder
        )
        # Кнопка появляется только после успешного сохранения (см. _run).

    # -- вспомогательное --------------------------------------------------
    def _set_status(self, text: str, color: str = TEXT_MUTED) -> None:
        self.status_var.set(text)
        self.status_label.configure(foreground=color)

    # -- обработчики выбора файлов -----------------------------------------
    def _browse_source(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите исходный PDF",
            filetypes=[("PDF файлы", "*.pdf"), ("Все файлы", "*.*")],
        )
        if path:
            self.source_path.set(path)

    def _browse_replacement(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите PDF с новым листом",
            filetypes=[("PDF файлы", "*.pdf"), ("Все файлы", "*.*")],
        )
        if path:
            self.replacement_path.set(path)

    def _browse_output_folder(self) -> None:
        path = filedialog.askdirectory(
            title="Выберите папку для сохранения результатов",
            initialdir=self.output_folder.get() or str(Path.home()),
        )
        if path:
            self.output_folder.set(path)
            save_output_folder(Path(path))

    def _open_output_folder(self) -> None:
        folder = self._last_output_path.parent if self._last_output_path else Path(self.output_folder.get())
        try:
            os.startfile(folder)  # доступно на Windows; открывает Проводник
        except (AttributeError, OSError):
            messagebox.showinfo("Папка", str(folder))

    # -- основное действие --------------------------------------------------
    def _run(self) -> None:
        source = self.source_path.get().strip()
        replacement = self.replacement_path.get().strip()
        folder = self.output_folder.get().strip()
        filename = self.output_filename.get().strip()

        if not source or not replacement:
            messagebox.showwarning(
                "Не все поля заполнены", "Укажите исходный PDF и PDF с новым листом."
            )
            return
        if not folder:
            messagebox.showwarning("Папка не выбрана", "Выберите папку для сохранения результата.")
            return
        if not filename:
            messagebox.showwarning("Имя файла не указано", "Введите имя нового PDF-файла.")
            return

        # Берём только имя файла (на случай, если пользователь вставил путь) и
        # гарантируем расширение .pdf.
        safe_name = Path(filename).name
        if not safe_name.lower().endswith(".pdf"):
            safe_name += ".pdf"

        output_path = Path(folder) / safe_name

        if output_path.exists():
            if not messagebox.askyesno(
                "Файл уже существует",
                f"Файл «{safe_name}» уже есть в этой папке. Перезаписать его?",
            ):
                return

        try:
            replace_first_page(source, replacement, output_path)
        except PdfReplaceError as exc:
            self._set_status(f"Ошибка: {exc}", ERROR)
            messagebox.showerror("Ошибка", str(exc))
            return
        except Exception as exc:  # noqa: BLE001 — показываем пользователю любую иную ошибку
            self._set_status(f"Непредвиденная ошибка: {exc}", ERROR)
            messagebox.showerror("Непредвиденная ошибка", str(exc))
            return

        self._last_output_path = output_path
        self._set_status(f"Готово! Сохранено как «{safe_name}» в выбранной папке.", SUCCESS)
        self.open_folder_button.pack(side="right")
        messagebox.showinfo("Готово", f"Файл успешно сохранён:\n{output_path}")


def main() -> None:
    app = PdfMakerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
