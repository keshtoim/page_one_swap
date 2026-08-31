"""Графический интерфейс приложения для замены первого листа PDF (Tkinter)."""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from pdf_maker.core import PdfReplaceError, replace_first_page


class PdfMakerApp(tk.Tk):
    """Главное окно приложения."""

    def __init__(self) -> None:
        super().__init__()
        self.title("PDF Maker — замена первого листа")
        self.geometry("640x340")
        self.minsize(640, 340)

        self.source_path = tk.StringVar()
        self.replacement_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.status_var = tk.StringVar(
            value="Выберите три файла и нажмите «Заменить и сохранить»."
        )

        self._build_ui()

    # -- построение интерфейса -------------------------------------------------
    def _build_ui(self) -> None:
        self.columnconfigure(1, weight=1)

        title = ttk.Label(
            self,
            text="Замена первого листа PDF",
            font=("Segoe UI", 14, "bold"),
        )
        title.grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(16, 4))

        subtitle = ttk.Label(
            self,
            text=(
                "Первая страница «Исходного PDF» будет заменена страницей\n"
                "из «PDF с новым листом» (он должен содержать ровно 1 страницу)."
            ),
            foreground="#555",
        )
        subtitle.grid(row=1, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 12))

        self._add_file_row(
            row=2,
            label_text="Исходный PDF (документ):",
            var=self.source_path,
            browse_command=self._browse_source,
        )
        self._add_file_row(
            row=3,
            label_text="PDF с новым листом (1 страница):",
            var=self.replacement_path,
            browse_command=self._browse_replacement,
        )
        self._add_file_row(
            row=4,
            label_text="Сохранить результат как:",
            var=self.output_path,
            browse_command=self._browse_output,
        )

        run_button = ttk.Button(
            self, text="Заменить и сохранить", command=self._run
        )
        run_button.grid(row=5, column=0, columnspan=3, pady=18)

        status_label = ttk.Label(
            self, textvariable=self.status_var, wraplength=600, foreground="#333"
        )
        status_label.grid(row=6, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 16))

    def _add_file_row(self, row, label_text, var, browse_command) -> None:
        ttk.Label(self, text=label_text).grid(
            row=row, column=0, sticky="w", padx=16, pady=6
        )
        entry = ttk.Entry(self, textvariable=var)
        entry.grid(row=row, column=1, sticky="we", pady=6)
        ttk.Button(self, text="Обзор…", command=browse_command).grid(
            row=row, column=2, padx=16, pady=6
        )

    # -- обработчики -------------------------------------------------------
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

    def _browse_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Сохранить результат как",
            defaultextension=".pdf",
            filetypes=[("PDF файлы", "*.pdf"), ("Все файлы", "*.*")],
        )
        if path:
            self.output_path.set(path)

    def _run(self) -> None:
        source = self.source_path.get().strip()
        replacement = self.replacement_path.get().strip()
        output = self.output_path.get().strip()

        if not source or not replacement or not output:
            messagebox.showwarning(
                "Не все поля заполнены", "Пожалуйста, укажите все три файла."
            )
            return

        try:
            replace_first_page(source, replacement, output)
        except PdfReplaceError as exc:
            self.status_var.set(f"Ошибка: {exc}")
            messagebox.showerror("Ошибка", str(exc))
            return
        except Exception as exc:  # noqa: BLE001 — показываем пользователю любую иную ошибку
            self.status_var.set(f"Непредвиденная ошибка: {exc}")
            messagebox.showerror("Непредвиденная ошибка", str(exc))
            return

        self.status_var.set(f"Готово! Результат сохранён в: {output}")
        messagebox.showinfo("Готово", f"Файл успешно сохранён:\n{output}")


def main() -> None:
    app = PdfMakerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
