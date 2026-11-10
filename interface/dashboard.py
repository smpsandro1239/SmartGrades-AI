"""Initial CustomTkinter dashboard."""

import sqlite3
import subprocess
import sys
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
from PIL import Image, ImageDraw
from services.document_matcher import find_student_document
from services.email_preview import EmailPreview, build_preview
from services.email_sender import get_gmail_service, send_email
from services.student_import import load_students

GRID_COLUMNS = ("ID", "E-mail", "Escola", "Estado", "Detalhe")
# Pesos relativos de cada coluna (controla a largura proporcional)
GRID_COLUMN_WEIGHTS = (1, 3, 2, 1, 2)

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
TOOLTIP_REAUTH = (
    "Reautenticar com o Gmail institucional (provas@aetsm.pt)."
)

# --- Paleta de cores (tema claro) ---
COL_BG_WINDOW = "#F3F4F6"
COL_CARD_BG = "#FFFFFF"
COL_CARD_BORDER = "#E5E7EB"
COL_TITLE = "#111827"
COL_BODY = "#374151"
COL_MUTED = "#6B7280"
COL_ROW_ODD = "#F9FAFB"
COL_ROW_EVEN = "#FFFFFF"
COL_HEADER_BG = "#F3F4F6"
COL_PRIMARY = "#2563EB"
COL_PRIMARY_HOVER = "#1D4ED8"
COL_SUCCESS = "#16A34A"
COL_SUCCESS_HOVER = "#15803D"
COL_DISABLED = "#9CA3AF"
COL_BADGE_OK_BG = "#DCFCE7"
COL_BADGE_OK_TX = "#166534"
COL_BADGE_ERR_BG = "#FEE2E2"
COL_BADGE_ERR_TX = "#991B1B"


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
        self.geometry("1200x880")
        self.minsize(1050, 820)

        # Grid principal da janela
        # FIX: peso 4 na linha de conteúdo para garantir altura suficiente
        # para a coluna esquerda (file_card + actions_card com botões visíveis)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)   # Header
        self.rowconfigure(1, weight=4)   # Conteúdo (2 colunas) — peso aumentado
        self.rowconfigure(2, weight=2)   # Resultados (tabela + histórico)
        self.rowconfigure(3, weight=0)   # Status bar

        # FIX 1: usar fg_color (não bg_color) para o fundo da janela
        self.configure(fg_color=COL_BG_WINDOW)

        # --- Estado ---
        self.file_path = ""
        self.records: list[dict[str, str]] = []
        self.mode = DEFAULT_EMAIL_MODE
        self.documents_path: Path = DOCUMENTS_PATH
        self.subject: str = "Resultados das provas ModA 2026"
        self.body_text: str = ""
        self.sender: str = "provas@aetsm.pt"

        self._build_header()
        self._build_content()
        self._build_results()
        self._build_status_bar()

    # ==================================================================
    # HEADER
    # ==================================================================
    def _build_header(self) -> None:
        # FIX 1: fg_color="transparent" (não bg_color)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        self.header_frame.columnconfigure(0, weight=1)
        self.header_frame.columnconfigure(1, weight=0)

        # Esquerda: título + subtítulo num frame transparente
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="nw")

        self.title_label = ctk.CTkLabel(
            title_box,
            text="SmartGrades",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COL_TITLE,
            fg_color="transparent",
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            title_box,
            text="Gestão de classificações e distribuição segura por e-mail",
            font=ctk.CTkFont(size=12),
            text_color=COL_MUTED,
            fg_color="transparent",
        )
        self.subtitle_label.pack(anchor="w")

        # Direita: email + badge de modo
        info_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        info_box.grid(row=0, column=1, sticky="ne")

        self.sender_label = ctk.CTkLabel(
            info_box,
            text=f"Email de envio: {self.sender}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COL_BODY,
            fg_color="transparent",
        )
        self.sender_label.pack(anchor="e", pady=(0, 6))

        mode_color = COL_SUCCESS if self.mode == "production" else "#D97706"
        mode_text = "PRODUÇÃO" if self.mode == "production" else "SIMULAÇÃO"
        self.mode_label = ctk.CTkLabel(
            info_box,
            text=f"\u25cf Modo: {mode_text}",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=mode_color,
            text_color="white",
            corner_radius=6,
            padx=12,
            pady=4,
        )
        self.mode_label.pack(anchor="e")

    # ==================================================================
    # CONTEÚDO PRINCIPAL (2 colunas)
    # ==================================================================
    def _build_content(self) -> None:
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=10)
        self.content_frame.columnconfigure(0, weight=2)
        self.content_frame.columnconfigure(1, weight=3)
        self.content_frame.rowconfigure(0, weight=1)

        self._build_left_column()
        self._build_right_column()

    def _build_left_column(self) -> None:
        # FIX DEFINITIVO: usar CTkScrollableFrame para a coluna esquerda.
        # Isto garante que TODOS os botões são sempre renderizados e acessíveis
        # via scroll, independentemente do tamanho da janela (minimizada,
        # maximizada, ou qualquer dimensão intermédia).
        self.left_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color="transparent",
            scrollbar_button_color="#D1D5DB",
            scrollbar_button_hover_color="#9CA3AF",
        )
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        # --- Card: Ficha de dados (altura natural no topo) ---
        file_card = ctk.CTkFrame(
            self.left_frame,
            corner_radius=12,
            border_width=1,
            border_color=COL_CARD_BORDER,
            fg_color=COL_CARD_BG,
        )
        file_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            file_card,
            text="Ficha de dados",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COL_TITLE,
            fg_color="transparent",
        ).pack(anchor="w", padx=20, pady=(16, 10))

        self.file_button = ctk.CTkButton(
            file_card,
            text="Selecionar ficha (Excel/CSV)",
            command=self.choose_file,
            image=_build_icon("folder", "#FFFFFF"),
            compound="left",
            fg_color=COL_PRIMARY,
            hover_color=COL_PRIMARY_HOVER,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.file_button.pack(fill="x", padx=20, pady=5)
        self._add_tooltip(self.file_button, TOOLTIP_SELECT_FILE)

        self.file_label = ctk.CTkLabel(
            file_card,
            text="Nenhum ficheiro selecionado.",
            text_color=COL_MUTED,
            fg_color="transparent",
            font=ctk.CTkFont(size=12),
        )
        self.file_label.pack(anchor="w", padx=20, pady=5)

        self.load_button = ctk.CTkButton(
            file_card,
            text="Carregar e validar",
            command=self.load_file,
            state="disabled",
            fg_color=COL_DISABLED,
            hover_color="#6B7280",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.load_button.pack(fill="x", padx=20, pady=(5, 16))
        self._add_tooltip(self.load_button, TOOLTIP_LOAD_FILE)

        # --- Card: Ações (altura natural, sem pack_propagate) ---
        # Com CTkScrollableFrame, o cartão toma a sua altura natural.
        # Se não couber, aparece scroll. Os botões são SEMPRE renderizados.
        actions_card = ctk.CTkFrame(
            self.left_frame,
            corner_radius=12,
            border_width=1,
            border_color=COL_CARD_BORDER,
            fg_color=COL_CARD_BG,
        )
        actions_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            actions_card,
            text="Ações",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COL_TITLE,
            fg_color="transparent",
        ).pack(anchor="w", padx=20, pady=(16, 10))

        self.match_button = ctk.CTkButton(
            actions_card,
            text="Localizar documentos",
            command=self.match_documents,
            state="disabled",
            image=_build_icon("search", "#FFFFFF"),
            compound="left",
            fg_color=COL_PRIMARY,
            hover_color=COL_PRIMARY_HOVER,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.match_button.pack(fill="x", padx=20, pady=10)
        self._add_tooltip(self.match_button, TOOLTIP_MATCH_DOCUMENTS)

        # Botão verde de envio — preenche o espaço restante do cartão
        self.send_button = ctk.CTkButton(
            actions_card,
            text="Enviar documentos",
            command=self.send_document,
            state="disabled",
            fg_color=COL_SUCCESS,
            hover_color=COL_SUCCESS_HOVER,
            height=46,
            font=ctk.CTkFont(size=14, weight="bold"),
            image=_build_icon("send", "#FFFFFF"),
            compound="left",
        )
        self.send_button.pack(fill="x", padx=20, pady=(10, 20))
        self._add_tooltip(self.send_button, TOOLTIP_SEND_DOCUMENTS)

        self.reauth_button = ctk.CTkButton(
            actions_card,
            text="ReAutenticar",
            command=self._start_reauth,
            state="disabled",
            fg_color=COL_DISABLED,
            hover_color="#6B7280",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.reauth_button.pack(fill="x", padx=20, pady=10)
        self._add_tooltip(self.reauth_button, TOOLTIP_REAUTH)

    def _build_right_column(self) -> None:
        self.right_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        self.right_frame.rowconfigure(0, weight=1)
        self.right_frame.columnconfigure(0, weight=1)

        preview_card = ctk.CTkFrame(
            self.right_frame,
            corner_radius=12,
            border_width=1,
            border_color=COL_CARD_BORDER,
            fg_color=COL_CARD_BG,
        )
        preview_card.grid(row=0, column=0, sticky="nsew")
        preview_card.columnconfigure(0, weight=1)
        preview_card.rowconfigure(0, weight=0)   # título
        preview_card.rowconfigure(1, weight=0)   # label assunto
        preview_card.rowconfigure(2, weight=0)   # entry assunto
        preview_card.rowconfigure(3, weight=0)   # label mensagem
        preview_card.rowconfigure(4, weight=1)   # textbox (expande)

        ctk.CTkLabel(
            preview_card,
            text="Pré-visualização do e-mail",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COL_TITLE,
            fg_color="transparent",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 10))

        self.subject_label = ctk.CTkLabel(
            preview_card,
            text="Assunto",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COL_BODY,
            fg_color="transparent",
        )
        self.subject_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 4))

        self.subject_entry = ctk.CTkEntry(
            preview_card,
            placeholder_text="Assunto do e-mail",
            fg_color=COL_ROW_ODD,
            border_color=COL_CARD_BORDER,
            text_color=COL_TITLE,
        )
        self.subject_entry.insert(0, self.subject)
        self.subject_entry.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 12))

        self.body_label = ctk.CTkLabel(
            preview_card,
            text="Mensagem",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COL_BODY,
            fg_color="transparent",
        )
        self.body_label.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 4))

        self.body_textbox = ctk.CTkTextbox(
            preview_card,
            fg_color=COL_ROW_ODD,
            border_color=COL_CARD_BORDER,
            border_width=1,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            text_color=COL_TITLE,
            height=220,
        )
        self.body_textbox.insert("1.0", self.body_text)
        self.body_textbox.grid(row=4, column=0, sticky="nsew", padx=20, pady=(0, 20))

    # ==================================================================
    # RESULTADOS (tabela + histórico separados)
    # ==================================================================
    def _build_results(self) -> None:
        self.results_card = ctk.CTkFrame(
            self,
            corner_radius=12,
            border_width=1,
            border_color=COL_CARD_BORDER,
            fg_color=COL_CARD_BG,
        )
        self.results_card.grid(row=2, column=0, sticky="nsew", padx=24, pady=(10, 12))
        self.results_card.columnconfigure(0, weight=1)
        # FIX 3: separar tabela (peso 3) do histórico (peso 1)
        self.results_card.rowconfigure(0, weight=0)   # título "Resultados"
        self.results_card.rowconfigure(1, weight=3)   # tabela
        self.results_card.rowconfigure(2, weight=0)   # título "Histórico"
        self.results_card.rowconfigure(3, weight=1)   # histórico de envios

        # Título da tabela
        ctk.CTkLabel(
            self.results_card,
            text="Resultados",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COL_TITLE,
            fg_color="transparent",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 8))

        # Scrollable frame APENAS para a tabela (não misturar com histórico)
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.results_card,
            fg_color="transparent",
            scrollbar_button_color="#D1D5DB",
            scrollbar_button_hover_color="#9CA3AF",
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        self.scroll_frame.columnconfigure(0, weight=1)

        # grid_frame usa fill="both" para ocupar toda a área
        self.grid_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True)
        self.grid_frame.columnconfigure(0, weight=1)

        self._render_grid([])

        # Título do histórico
        ctk.CTkLabel(
            self.results_card,
            text="Histórico de envios",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COL_BODY,
            fg_color="transparent",
        ).grid(row=2, column=0, sticky="w", padx=20, pady=(8, 4))

        # Histórico fora do scroll_frame da tabela
        # height=70 (reduzido de 100) para libertar espaço vertical
        # para a coluna esquerda (actions_card com botões)
        self.history_text = ctk.CTkTextbox(
            self.results_card,
            height=70,
            fg_color=COL_ROW_ODD,
            border_color=COL_CARD_BORDER,
            border_width=1,
            corner_radius=8,
            font=ctk.CTkFont(size=11),
            text_color=COL_BODY,
        )
        self.history_text.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 16))
        self.history_text.configure(state="disabled")

    def _build_status_bar(self) -> None:
        self.status_label = ctk.CTkLabel(
            self,
            text="\u25cf Pronto.",
            text_color=COL_SUCCESS,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent",
        )
        self.status_label.grid(row=3, column=0, sticky="w", padx=24, pady=(0, 12))

    # ==================================================================
    # MÉTODOS DE AÇÃO (inalterados)
    # ==================================================================
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
        self.reauth_button.configure(state="normal")
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
        failed: list[str] = []
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
                failed.append(f"{preview.recipient} ({preview.school}): {error}")
        self._refresh_history()
        message_lines = [f"{sent} documento(s) enviado(s) com sucesso."]
        if skipped:
            message_lines.append(f"{len(skipped)} ignorado(s) por falta de documento:")
            message_lines.extend(f"  - {item}" for item in skipped)
        if failed:
            message_lines.append(f"{len(failed)} falharam:")
            message_lines.extend(f"  - {item}" for item in failed)
        if not previews:
            message_lines = ["Nenhum documento encontrado para enviar."]
        messagebox.showinfo(
            "Resultado do envio",
            "\n".join(message_lines),
        )
        skipped_text = f" Ignorados por falta de ficheiro: {len(skipped)}." if skipped else ""
        self.status_label.configure(
            text=f"Envio concluído: {sent} enviados, {len(failed)} falhados.{skipped_text}"
        )

    def _show_preview(self, previews: list[EmailPreview]) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Pré-visualização dos e-mails")
        dialog.geometry("680x520")
        content = "\n\n".join(
            f"Para: {preview.recipient}\nAssunto: {preview.subject}\n\n{preview.html_body}"
            for preview in previews
        )
        scroll_frame = ctk.CTkScrollableFrame(dialog)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        box = ctk.CTkTextbox(scroll_frame, wrap="word", height=320)
        box.pack(fill="both", expand=True)
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
            # FIX 1: fg_color é o fundo do label, text_color é a cor do texto
            # (o código original tinha bg_color e fg_color trocados)
            label = ctk.CTkLabel(
                window,
                text=text,
                fg_color="#333333",
                text_color="#ffffff",
                corner_radius=6,
                font=ctk.CTkFont(size=12),
                padx=10,
                pady=6,
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

    def _start_reauth(self) -> None:
        self.status_label.configure(
            text="A autenticar com o Gmail. Complete o fluxo no browser."
        )
        subprocess.Popen(
            [
                sys.executable,
                "run_oauth_flow.py",
            ],
            cwd=str(Path(__file__).resolve().parents[1]),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )

    # ==================================================================
    # TABELA DE RESULTADOS — renderização com colunas separadas
    # ==================================================================
    def _render_grid(self, rows: list[list[str]]) -> None:
        """
        Desenha a tabela com:
          - colunas proporcionalmente distribuídas (columnconfigure dentro de cada linha)
          - cabeçalho alinhado com o corpo
          - zebra striping
          - badges de Estado coloridas e legíveis
          - separação visual horizontal entre colunas (padx)
        """
        for child in list(self.grid_frame.winfo_children()):
            child.destroy()

        # --- Linha de cabeçalho ---
        header_frame = ctk.CTkFrame(
            self.grid_frame,
            fg_color=COL_HEADER_BG,
            corner_radius=6,
        )
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        # FIX 2: configurar pesos DENTRO do header_frame (não no grid_frame)
        for i, weight in enumerate(GRID_COLUMN_WEIGHTS):
            header_frame.columnconfigure(i, weight=weight)

        # FIX: TODOS os cabeçalhos centrados na sua coluna
        for i, title in enumerate(GRID_COLUMNS):
            ctk.CTkLabel(
                header_frame,
                text=title,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="transparent",
                text_color=COL_TITLE,
                anchor="center",
                justify="center",
            ).grid(row=0, column=i, sticky="ew", padx=10, pady=10)

        # --- Estado vazio ---
        if not rows:
            empty_label = ctk.CTkLabel(
                self.grid_frame,
                text="Sem dados para mostrar. Carregue uma ficha e localize os documentos.",
                text_color=COL_DISABLED,
                fg_color="transparent",
                font=ctk.CTkFont(size=12),
            )
            empty_label.grid(row=1, column=0, pady=30)
            return

        # --- Linhas de dados ---
        for row_index, row in enumerate(rows, start=1):
            row_bg = COL_ROW_EVEN if row_index % 2 == 1 else COL_ROW_ODD
            row_frame = ctk.CTkFrame(
                self.grid_frame,
                fg_color=row_bg,
                corner_radius=0,
            )
            row_frame.grid(row=row_index, column=0, sticky="ew")

            # FIX 2: configurar pesos DENTRO de cada row_frame
            for i, weight in enumerate(GRID_COLUMN_WEIGHTS):
                row_frame.columnconfigure(i, weight=weight)

            # FIX: TODAS as células centradas na sua coluna
            for column, text in enumerate(row):
                if column == 3:  # Estado — badge colorida centrada
                    is_found = str(text) == "Encontrado"
                    ctk.CTkLabel(
                        row_frame,
                        text=str(text),
                        fg_color=COL_BADGE_OK_BG if is_found else COL_BADGE_ERR_BG,
                        text_color=COL_BADGE_OK_TX if is_found else COL_BADGE_ERR_TX,
                        corner_radius=10,
                        font=ctk.CTkFont(size=11, weight="bold"),
                        padx=8,
                        pady=2,
                        anchor="center",
                        justify="center",
                    ).grid(row=0, column=column, sticky="ew", padx=10, pady=8)
                else:
                    text_color = COL_BODY if column != 4 else COL_MUTED
                    ctk.CTkLabel(
                        row_frame,
                        text=str(text),
                        fg_color="transparent",
                        text_color=text_color,
                        anchor="center",
                        justify="center",
                        font=ctk.CTkFont(size=12),
                    ).grid(row=0, column=column, sticky="ew", padx=10, pady=8)

            # Separador horizontal entre linhas (linha fina)
            if row_index < len(rows):
                separator = ctk.CTkFrame(
                    self.grid_frame,
                    fg_color=COL_CARD_BORDER,
                    corner_radius=0,
                    height=1,
                )
                separator.grid(row=row_index * 2, column=0, sticky="ew")

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
        self.reauth_button.configure(state="disabled")
        self._render_grid([])
