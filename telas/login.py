"""
Tela de Login — Integrada como Frame interno do App (sem Toplevel fantasma).
"""
import os
import customtkinter as ctk
from PIL import Image
from core.auth import login, criar_admin_padrao

COR_BG   = "#1e2a3a"
COR_CARD = "#253447"
AZUL     = "#1a73e8"


class TelaLogin(ctk.CTkFrame):
    def __init__(self, master, on_sucesso, **kw):
        super().__init__(master, fg_color=COR_BG, **kw)
        self.on_sucesso = on_sucesso
        criar_admin_padrao()
        self._build()
        self.after(150, lambda: self.ent_login.focus())

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Card Centralizado
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0)

        # Logo em Imagem
        caminho_logo = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icone.png")
        if os.path.exists(caminho_logo):
            try:
                img_pil = Image.open(caminho_logo)
                img_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(90, 90))
                lbl_logo = ctk.CTkLabel(container, image=img_ctk, text="")
                lbl_logo.pack(pady=(10, 4))
            except Exception:
                ctk.CTkLabel(container, text="⚡", font=("Segoe UI", 48)).pack(pady=(10, 0))
        else:
            ctk.CTkLabel(container, text="⚡", font=("Segoe UI", 48)).pack(pady=(10, 0))

        ctk.CTkLabel(container, text="Xenos PDV",
                     font=("Segoe UI", 26, "bold"), text_color="white").pack()
        ctk.CTkLabel(container, text="Sistema de Gestão Comercial e Vendas",
                     font=("Segoe UI", 11), text_color="#8da0b8").pack(pady=(2, 16))

        card = ctk.CTkFrame(container, fg_color=COR_CARD, corner_radius=12, width=380)
        card.pack(padx=20, pady=10)

        ctk.CTkLabel(card, text="Usuário", anchor="w",
                     font=("Segoe UI", 11), text_color="#c0d0e0").pack(
            fill="x", padx=24, pady=(20, 4))
        self.ent_login = ctk.CTkEntry(card, height=40, width=320, placeholder_text="login")
        self.ent_login.pack(padx=24)

        ctk.CTkLabel(card, text="Senha", anchor="w",
                     font=("Segoe UI", 11), text_color="#c0d0e0").pack(
            fill="x", padx=24, pady=(12, 4))
        self.ent_senha = ctk.CTkEntry(card, height=40, width=320, placeholder_text="senha", show="●")
        self.ent_senha.pack(padx=24)
        self.ent_senha.bind("<Return>", lambda e: self._entrar())

        self.lbl_erro = ctk.CTkLabel(card, text="", text_color="#ff6b6b", font=("Segoe UI", 11))
        self.lbl_erro.pack(pady=(8, 0))

        ctk.CTkButton(card, text="ENTRAR NO SISTEMA", height=42, width=320,
                      font=("Segoe UI", 13, "bold"), fg_color=AZUL, command=self._entrar).pack(
            padx=24, pady=(10, 20))

        ctk.CTkLabel(container, text="Acesso padrão: admin / 1234",
                     font=("Segoe UI", 10), text_color="#64748b").pack(pady=10)

    def _entrar(self):
        u = login(self.ent_login.get(), self.ent_senha.get())
        if u:
            self.on_sucesso(u)
        else:
            self.lbl_erro.configure(text="⚠ Usuário ou senha incorretos")
            self.ent_senha.delete(0, "end")
