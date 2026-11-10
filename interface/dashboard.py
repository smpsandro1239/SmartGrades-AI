"""Initial CustomTkinter dashboard."""

import sqlite3
import tkinter
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from config.settings import (
    DEFAULT_EMAIL_MODE,
    DOCUMENTS_PATH,
    GMAIL_CREDENTIALS_PATH,
    GMAIL_TOKEN_PATH,
    MAX_SEND_PER_RUN,
)
from database.database import insert_email_log, list_email_logs, upsert_students
from services.document_matcher import find_student_document
from services.email_preview import EmailPreview, build_preview
from services.email_sender import get_gmail_service, send_email
from services.student_import import load_students

GRID_COLUMNS = ("ID", "E-mail", "Escola", "Estado", "Detalhe")

TOOLTIP_SELECT_FILE = (
    "Selecionar ficha de alunos (Excel/CSV) com as colunas "
    "E-mail, ID_Aluno e Escola."
)
TOOLTIP_LOAD_FILE = (
    "Carregar e validar a ficha: colunas obrigatórias E-mail, "
    "ID_Aluno e Escola."
)
TOOLTIP_MATCH_DOCUMENTS = (
    "Localizar o documento <ID>.docx na pasta da escola do registo."
)
TOOLTIP_SEND_DOCUMENTS = (
    "Enviar os documentos por e-mail (modo produção) após "
    "confirmação."
)


class Dashboard(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SmartGrades")
        self.geometry("900x600")
        self.minsize(760, 500)

        self.file_path = ""
        self.records: list[dict[str, str]] = []
        self.mode = DEFAULT_EMAIL_MODE
        self.documents_path: Path = DOCUMENTS_PATH
        self.subject: str = "Resultados das provas ModA 2026"
        self.body_text: str = ""
        self.sender: str = "provas@aetsm.pt"
        self.sender_label = ctk.CTkLabel(
            self,
            text=f"Email de envio: {self.sender}",
            font=ctk.CTkFont(size=12),
        )
        self.sender_label.pack(pady=6)
        self.subject_entry = ctk.CTkEntry(
            self,
            placeholder_text="Assunto do e-mail",
        )
        self.subject_entry.insert(0, self.subject)
        self.subject_entry.pack(pady=6)
        self.body_textbox = ctk.CTkTextbox(self, height=120)
        self.body_textbox.insert("1.0", self.body_text)
        self.body_textbox.pack(fill="x", pady=6, padx=20)

        ctk.CTkLabel(
            self,
            text="SmartGrades",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(pady=(40, 12))

        ctk.CTkLabel(
            self,
            text="Gestão de classificações e distribuição segura por e-mail",
        ).pack(pady=8)

        ctk.CTkLabel(
            self,
            text=f"Modo de envio: {self.mode}.",
        ).pack(pady=20)
        if self.mode == "simulation":
            ctk.CTkLabel(
                self,
                text="Nenhum e-mail será enviado.",
            ).pack(pady=8)

        self.file_button = ctk.CTkButton(
            self,
            text="Selecionar ficha (Excel/CSV)",
            command=self.choose_file,
        )
        self.file_button.pack(pady=6)
        self._add_tooltip(self.file_button, TOOLTIP_SELECT_FILE)

        self.file_label = ctk.CTkLabel(self, text="Nenhum ficheiro selecionado.")
        self.file_label.pack(pady=4)

        self.load_button = ctk.CTkButton(
            self,
            text="Carregar e validar",
            command=self.load_file,
            state="disabled",
        )
        self.load_button.pack(pady=6)
        self._add_tooltip(self.load_button, TOOLTIP_LOAD_FILE)

        self.match_button = ctk.CTkButton(
            self,
            text="Localizar documentos",
            command=self.match_documents,
            state="disabled",
        )
        self.match_button.pack(pady=6)
        self._add_tooltip(self.match_button, TOOLTIP_MATCH_DOCUMENTS)

        self.send_button = ctk.CTkButton(
            self,
            text="Enviar documentos",
            command=self.send_document,
            state="disabled",
        )
        self.send_button.pack(pady=6)
        self._add_tooltip(self.send_button, TOOLTIP_SEND_DOCUMENTS)

        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=12)

        self.grid_frame = ctk.CTkFrame(self.scroll_frame)
        self.grid_frame.pack(fill="x", expand=True, padx=10, pady=4)
        self._render_grid([])

        self.history_text = ctk.CTkTextbox(self.scroll_frame, height=140)
        self.history_text.pack(fill="x", padx=10, pady=(0, 4))
        self.history_text.configure(state="disabled")

        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack(pady=(0, 12))

    def choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecionar ficha de alunos",
            filetypes=[("Ficheiros suportados", "*.xlsx *.xlsm *.csv"), ("Todos os ficheiros", "*.*")],
        )
        if not path:
            return
        self.file_path = path
        self.file_label.configure(text=Path(path).name)
        self.load_button.configure(state="normal")

    def load_file(self) -> None:
        if not self.file_path:
            self.status_label.configure(text="Selecione primeiro uma ficha de alunos.")
            return
        try:
            self.records = load_students(self.file_path)
        except (OSError, ValueError) as error:
            self.status_label.configure(text=f"Erro ao carregar a ficha: {error}")
            self._clear_results()
            return
        self.match_button.configure(state="normal")
        self.send_button.configure(state="normal")
        self.status_label.configure(text=f"{len(self.records)} registos validados.")

    def match_documents(self) -> None:
        if not self.records:
            self.status_label.configure(text="Carregue antes uma ficha validada.")
            return
        rows: list[list[str]] = []
        for record in self.records:
            match = find_student_document(self.documents_path, record["school"], record["student_id"])
            rows.append(
                [
                    record["student_id"],
                    record["email"],
                    record["school"],
                    "Encontrado" if match.path is not None else "Em falta",
                    match.path.name if match.path is not None else (match.error or "sem documento"),
                ]
            )
        self._render_grid(rows)
        self.status_label.configure(text=f"{len(rows)} alunos processados.")

    def send_document(self) -> None:
        if self.mode != "production":
            self.status_label.configure(text="Modo de envio: SIMULAÇÃO — envio real desativado.")
            return
        if not self.records:
            self.status_label.configure(text="Carregue antes uma ficha validada.")
            return
        if len(self.records) > MAX_SEND_PER_RUN:
            self.status_label.configure(text=f"Limite de envios por execução: {MAX_SEND_PER_RUN}.")
            return
        confirmed = messagebox.askyesno(
            "Confirmar envio",
            f"Enviar {len(self.records)} documentos por e-mail?",
        )
        if not confirmed:
            return
        service = self._get_gmail_service()
        if service is None:
            return
        sender = self.sender.strip()
        previews: list[EmailPreview] = []
        skipped: list[str] = []
        for record in self.records:
            match = find_student_document(self.documents_path, record["school"], record["student_id"])
            if match.path is None:
                skipped.append(f"{record['student_id']} ({record['school']}): {match.error}")
                continue
            previews.append(
                build_preview(
                    record,
                    match.path,
                    body_text=self.body_textbox.get("1.0", "end").strip(),
                    subject=self.subject_entry.get().strip() or self.subject,
                )
            )
        if previews:
            self._show_preview(previews)
        upsert_students(
            [
                {
                    "student_id": preview.student_id,
                    "school": preview.school,
                    "email": preview.recipient,
                }
                for preview in previews
            ]
        )
        sent = 0
        failed = 0
        for preview in previews:
            try:
                response = send_email(service, preview, sender)
                insert_email_log(
                    student_number=preview.student_id,
                    school=preview.school,
                    recipient=preview.recipient,
                    mode="production",
                    status="sent",
                    message_id=str(response.get("id")) if response else None,
                )
                sent += 1
            except Exception as error:
                insert_email_log(
                    student_number=preview.student_id,
                    school=preview.school,
                    recipient=preview.recipient,
                    mode="production",
                    status="failed",
                    error_message=str(error),
                )
                failed += 1
        self._refresh_history()
        skipped_text = f" Ignorados por falta de ficheiro: {len(skipped)}." if skipped else ""
        self.status_label.configure(
            text=f"Envio concluído: {sent} enviados, {failed} falhados.{skipped_text}"
        )

    def _show_preview(self, previews: list[EmailPreview]) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Pré-visualização dos e-mails")
        dialog.geometry("680x520")
        content = "\n\n".join(
            f"Para: {preview.recipient}\nAssunto: {preview.subject}\n\n{preview.html_body}"
            for preview in previews
        )
        box = ctk.CTkTextbox(dialog, wrap="word")
        box.pack(fill="both", expand=True, padx=20, pady=20)
        box.insert("end", content)
        box.configure(state="disabled")
        ctk.CTkButton(dialog, text="Confirmar envio", command=dialog.destroy).pack(pady=10)

    def _add_tooltip(self, widget, text: str) -> None:
        tooltip_window = None

        def show(_event=None) -> None:
            nonlocal tooltip_window
            if tooltip_window is not None and tooltip_window.winfo_exists():
                return
            window = ctk.CTkToplevel(self)
            window.overrideredirect(True)
            label = ctk.CTkLabel(
                window,
                text=text,
                bg_color="#333333",
                fg_color="#ffffff",
                corner_radius=6,
                font=ctk.CTkFont(size=12),
            )
            label.pack(fill="both", expand=True)
            x = widget.winfo_rootx() + widget.winfo_width() / 2 - 80
            y = widget.winfo_rooty() + widget.winfo_height()
            window.geometry(f"+{int(x)}+{int(y + 10)}")
            tooltip_window = window

        def hide(_event=None) -> None:
            nonlocal tooltip_window
            if tooltip_window is not None and tooltip_window.winfo_exists():
                tooltip_window.destroy()
                tooltip_window = None

        tkinter.Misc.bind(widget, "<Enter>", show)
        tkinter.Misc.bind(widget, "<Leave>", hide)

    def _get_gmail_service(self):
        try:
            return get_gmail_service(GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH)
        except Exception as error:
            self.status_label.configure(text=f"Falha ao autenticar com Gmail: {error}")
            return None

    def _render_grid(self, rows: list[list[str]]) -> None:
        for child in list(self.grid_frame.winfo_children()):
            child.destroy()
        for column, title in enumerate(GRID_COLUMNS):
            ctk.CTkLabel(
                self.grid_frame,
                text=title,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).grid(row=0, column=column, sticky="nsew", padx=6, pady=6)
        for row_index, row in enumerate(rows, start=1):
            for column, text in enumerate(row):
                ctk.CTkLabel(
                    self.grid_frame,
                    text=str(text),
                ).grid(row=row_index, column=column, sticky="nsew", padx=6, pady=6)
            self.grid_frame.grid_rowconfigure(row_index, weight=1)
        for column in range(len(GRID_COLUMNS)):
            self.grid_frame.grid_columnconfigure(column, weight=1)

    def _refresh_history(self) -> None:
        logs = list_email_logs()
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        for log in logs:
            self.history_text.insert(
                "end",
                f"{log.get('created_at', '')} | {log.get('student_number', '')} | "
                f"{log.get('recipient', '')} | {log.get('mode', '')} | {log.get('status', '')}\n",
            )
        self.history_text.configure(state="disabled")

    def _clear_results(self) -> None:
        self.records = []
        self.match_button.configure(state="disabled")
        self.send_button.configure(state="disabled")
        self._render_grid([])
