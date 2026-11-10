"""Initial CustomTkinter dashboard."""

import sqlite3
import tkinter
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageDraw
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


def _build_icon(kind: str, color: str) -> ctk.CTkImage:
    size = 18
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if kind == "folder":
        draw.rectangle([1, 5, 17, 16], fill=color)
        draw.rectangle([4, 2, 12, 7], fill=color)
    elif kind == "send":
        draw.polygon([(2, 11), (11, 1), (17, 6), (12, 18), (10, 18), (4, 6)], fill=color)
    elif kind == "search":
        draw.ellipse([2, 3, 16, 17], outline=color, width=2)
        draw.ellipse([11, 8, 14, 11], fill=color)
    return ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))


class Dashboard(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("light")
        self.title("SmartGrades")
        self.geometry("1100x750")
        self.minsize(1000, 750)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=3)
        self.rowconfigure(2, weight=2)
        self.rowconfigure(3, weight=0)
        self.configure(bg_color="#F3F4F6")

        self.file_path = ""
        self.records: list[dict[str, str]] = []
        self.mode = DEFAULT_EMAIL_MODE
        self.documents_path: Path = DOCUMENTS_PATH
        self.subject: str = "Resultados das provas ModA 2026"
        self.body_text: str = ""
        self.sender: str = "provas@aetsm.pt"

        self.header_frame = ctk.CTkFrame(self, corner_radius=0, bg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.header_frame.columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(self.header_frame, text="SmartGrades", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.grid(row=0, column=0, sticky="nw", padx=16, pady=12)

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Gestão de classificações e distribuição segura por e-mail",
            text_color="gray",
        )
        self.subtitle_label.grid(row=1, column=0, sticky="nw", padx=16, pady=(0, 8))

        self.sender_label = ctk.CTkLabel(
            self.header_frame,
            text=f"Email de envio: {self.sender}",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.sender_label.grid(row=0, column=1, sticky="ne", padx=20, pady=12)

        mode_color = "#2E7D32" if self.mode == "production" else "#B26A00"
        mode_text = "PRODUÇÃO" if self.mode == "production" else "SIMULAÇÃO"
        self.mode_label = ctk.CTkLabel(
            self.header_frame,
            text=f"Modo: {mode_text}",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=mode_color,
            text_color="white",
            corner_radius=4,
            width=100,
        )
        self.mode_label.grid(row=1, column=1, sticky="ne", padx=20, pady=(0, 12))

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.content_frame.columnconfigure(0, weight=4)
        self.content_frame.columnconfigure(1, weight=5)
        self.content_frame.rowconfigure(0, weight=1)

        self.left_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.left_frame.columnconfigure(0, weight=1)
        self.left_frame.rowconfigure(0, weight=0)
        self.left_frame.rowconfigure(1, weight=1)

        file_card = ctk.CTkFrame(self.left_frame, corner_radius=12, border_width=1, border_color="#E5E7EB", fg_color="#FFFFFF")
        file_card.grid(row=0, column=0, sticky="nsew")
        file_card.columnconfigure(0, weight=1)
        file_card.rowconfigure(0, weight=0)
        ctk.CTkLabel(file_card, text="Ficha de dados", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="nw", padx=20, pady=15)
        self.file_button = ctk.CTkButton(
            file_card,
            text="Selecionar ficha (Excel/CSV)",
            command=self.choose_file,
            image=_build_icon("folder", "#FFFFFF"),
            compound="left",
        )
        self.file_button.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        self._add_tooltip(self.file_button, TOOLTIP_SELECT_FILE)
        self.file_label = ctk.CTkLabel(file_card, text="Nenhum ficheiro selecionado.", text_color="gray")
        self.file_label.grid(row=2, column=0, sticky="nw", padx=20, pady=5)
        self.load_button = ctk.CTkButton(file_card, text="Carregar e validar", command=self.load_file, state="disabled", fg_color="gray")
        self.load_button.grid(row=3, column=0, sticky="ew", padx=20, pady=(5, 15))
        self._add_tooltip(self.load_button, TOOLTIP_LOAD_FILE)

        actions_card = ctk.CTkFrame(self.left_frame, corner_radius=12, border_width=1, border_color="#E5E7EB", fg_color="#FFFFFF")
        actions_card.grid(row=1, column=0, sticky="nsew")
        actions_card.columnconfigure(0, weight=1)
        actions_card.rowconfigure(0, weight=0)
        actions_card.rowconfigure(1, weight=1)
        actions_card.rowconfigure(2, weight=0)
        ctk.CTkLabel(actions_card, text="Ações", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="nw", padx=20, pady=15)
        self.match_button = ctk.CTkButton(
            actions_card,
            text="Localizar documentos",
            command=self.match_documents,
            state="disabled",
            image=_build_icon("search", "#FFFFFF"),
            compound="left",
        )
        self.match_button.grid(row=1, column=0, sticky="new", padx=20, pady=10)
        self._add_tooltip(self.match_button, TOOLTIP_MATCH_DOCUMENTS)
        self.send_button = ctk.CTkButton(
            actions_card,
            text="Enviar documentos",
            command=self.send_document,
            state="disabled",
            fg_color="#16A34A",
            hover_color="#15803D",
            height=46,
            font=ctk.CTkFont(size=14, weight="bold"),
            image=_build_icon("send", "#FFFFFF"),
            compound="left",
        )
        self.send_button.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))
        self._add_tooltip(self.send_button, TOOLTIP_SEND_DOCUMENTS)

        self.right_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.right_frame.columnconfigure(0, weight=1)
        preview_card = ctk.CTkFrame(self.right_frame, corner_radius=12, border_width=1, border_color="#E5E7EB", fg_color="#FFFFFF")
        preview_card.pack(fill="both", expand=True)
        ctk.CTkLabel(preview_card, text="Pré-visualização do e-mail", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 10), padx=20, anchor="w")
        self.subject_label = ctk.CTkLabel(preview_card, text="Assunto:")
        self.subject_label.pack(padx=20, anchor="w")
        self.subject_entry = ctk.CTkEntry(preview_card, placeholder_text="Assunto do e-mail")
        self.subject_entry.insert(0, self.subject)
        self.subject_entry.pack(fill="x", padx=20, pady=(0, 10))
        self.body_label = ctk.CTkLabel(preview_card, text="Mensagem:")
        self.body_label.pack(padx=20, anchor="w")
        self.body_textbox = ctk.CTkTextbox(preview_card, height=150)
        self.body_textbox.insert("1.0", self.body_text)
        self.body_textbox.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.results_card = ctk.CTkFrame(self, corner_radius=12, border_width=1, border_color="#E5E7EB", fg_color="#FFFFFF")
        self.results_card.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))
        ctk.CTkLabel(self.results_card, text="Resultados", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5), padx=20, anchor="w")
        self.scroll_frame = ctk.CTkScrollableFrame(self.results_card)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.grid_frame = ctk.CTkFrame(self.scroll_frame)
        self.grid_frame.pack(fill="x", expand=True, padx=5, pady=5)
        self._render_grid([])
        self.history_text = ctk.CTkTextbox(self.scroll_frame, height=140)
        self.history_text.pack(fill="x", padx=5, pady=5)
        self.history_text.configure(state="disabled")
        self.status_label = ctk.CTkLabel(self, text="Pronto.", text_color="#1E6B23", font=ctk.CTkFont(weight="bold"))
        self.status_label.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 10))

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
        self.status_label.configure(text=f"{len(self.records)} registos validados. Avança para localizar os documentos.")

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
        self.send_button.configure(state="normal")
        self.status_label.configure(text=f"{len(rows)} alunos processados. Revise o e-mail e envie.")

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
        header_frame = ctk.CTkFrame(self.grid_frame, fg_color="#F3F4F6", corner_radius=6)
        header_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        for column, title in enumerate(GRID_COLUMNS):
            ctk.CTkLabel(
                header_frame,
                text=title,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="transparent",
                text_color="#111827",
                corner_radius=6,
            ).grid(row=0, column=column, sticky="nsew", padx=6, pady=6)
        self.grid_frame.grid_rowconfigure(0, weight=0)
        for row_index, row in enumerate(rows, start=1):
            row_frame = ctk.CTkFrame(
                self.grid_frame,
                fg_color="#FFFFFF" if row_index % 2 == 1 else "#F9FAFB",
            )
            row_frame.grid(row=row_index, column=0, sticky="nsew", padx=6, pady=6)
            for column in range(len(row)):
                row_frame.columnconfigure(column, weight=1)
            for column, text in enumerate(row):
                if column == 3 and text in ("Encontrado", "Em falta"):
                    is_found = text == "Encontrado"
                    label = ctk.CTkLabel(
                        row_frame,
                        text=text,
                        fg_color="#DCFCE7" if is_found else "#FEE2E2",
                        text_color="#166534" if is_found else "#991B1B",
                        corner_radius=10,
                        font=ctk.CTkFont(size=11, weight="bold"),
                    )
                else:
                    label = ctk.CTkLabel(
                        row_frame,
                        text=str(text),
                        fg_color="transparent",
                        text_color="#374151",
                        anchor="w",
                    )
                label.grid(row=0, column=column, sticky="nsew", padx=6, pady=6)
            self.grid_frame.grid_rowconfigure(row_index, weight=0)
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
