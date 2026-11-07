"""Initial CustomTkinter dashboard."""

import customtkinter as ctk


class Dashboard(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SmartGrades-AI")
        self.geometry("900x600")
        self.minsize(760, 500)

        ctk.CTkLabel(
            self,
            text="SmartGrades-AI",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(pady=(40, 12))

        ctk.CTkLabel(
            self,
            text="Gestão de classificações e distribuição segura por e-mail",
        ).pack(pady=8)

        ctk.CTkLabel(
            self,
            text="Modo inicial: SIMULAÇÃO — nenhum e-mail será enviado.",
        ).pack(pady=20)
