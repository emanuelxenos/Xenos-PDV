"""
Sistema Xenos PDV — Ponto de Entrada Principal com Contas a Receber integrado.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from core.database import criar_tabelas, db_session, Cliente, Fornecedor, Produto, Venda, ContaReceber
from core.auth import criar_admin_padrao
from telas.login import TelaLogin
from telas.clientes import TelaClientes
from telas.fornecedores import TelaFornecedores
from telas.produtos import TelaProdutos
from telas.pdv import TelaPDV
from telas.caixa import TelaCaixa
from telas.relatorios import TelaRelatorios
from telas.contas_receber import TelaContasReceber

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COR_MENU  = "#1e2a3a"
COR_HOVER = "#2d3f56"
COR_ATIVO = "#1a73e8"
COR_BG    = "#f0f4f8"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Xenos PDV — Gestão Comercial")
        self.geometry("1280x760")
        self.minsize(980, 620)

        self.usuario = None
        self._tela_atual_key = None
        self._telas_cache = {}
        self._botoes_menu = {}

        self._exibir_login()

    def _exibir_login(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.tela_login = TelaLogin(self, on_sucesso=self._login_sucesso)
        self.tela_login.grid(row=0, column=0, sticky="nsew")

    def _login_sucesso(self, usuario):
        self.usuario = usuario
        self.tela_login.destroy()
        self._montar_layout_principal()
        self._abrir("dashboard")

    def _montar_layout_principal(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COR_MENU)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(20, weight=1)

        ctk.CTkLabel(self.sidebar, text="⚡ Xenos PDV", font=("Segoe UI", 16, "bold"), text_color="white").grid(
            row=0, column=0, padx=16, pady=(20, 2), sticky="w")
        u_nome = self.usuario.nome if self.usuario else "Admin"
        ctk.CTkLabel(self.sidebar, text=f"👤 {u_nome}", font=("Segoe UI", 10), text_color="#8da0b8").grid(
            row=1, column=0, padx=16, pady=(0, 14), sticky="w")

        ctk.CTkFrame(self.sidebar, height=1, fg_color="#2d3f56").grid(
            row=2, column=0, sticky="ew", padx=12, pady=4)

        # Menus completos
        menus = [
            ("🏠", "Dashboard",        "dashboard"),
            ("🛒", "Frente de Caixa",  "pdv"),
            ("📖", "Contas a Receber", "contas"),
            ("💵", "Fluxo de Caixa",   "caixa"),
            ("📊", "Relatórios Vendas","relatorios"),
            ("📦", "Produtos",         "produtos"),
            ("👤", "Clientes",         "clientes"),
            ("🏭", "Fornecedores",     "fornecedores"),
        ]
        for i, (icon, label, key) in enumerate(menus, start=3):
            btn = ctk.CTkButton(
                self.sidebar, text=f"  {icon}  {label}",
                anchor="w", width=200, height=38,
                corner_radius=6, font=("Segoe UI", 11),
                fg_color="transparent", text_color="#c8d8ea",
                hover_color=COR_HOVER,
                command=lambda k=key: self._abrir(k)
            )
            btn.grid(row=i, column=0, padx=10, pady=2, sticky="ew")
            self._botoes_menu[key] = btn

        ctk.CTkLabel(self.sidebar, text="v2.1 • Python & SQLite",
                     font=("Segoe UI", 9), text_color="#4a6080").grid(
            row=21, column=0, padx=16, pady=12, sticky="sw")

        # ── Área Central de Conteúdo ──
        self.frame_conteudo = ctk.CTkFrame(self, corner_radius=0, fg_color=COR_BG)
        self.frame_conteudo.grid(row=0, column=1, sticky="nsew")
        self.frame_conteudo.grid_columnconfigure(0, weight=1)
        self.frame_conteudo.grid_rowconfigure(0, weight=1)

    def _abrir(self, key: str):
        if self._tela_atual_key == key:
            return

        for k, btn in self._botoes_menu.items():
            btn.configure(fg_color=COR_ATIVO if k == key else "transparent",
                          text_color="white" if k == key else "#c8d8ea")

        if self._tela_atual_key and self._tela_atual_key in self._telas_cache:
            self._telas_cache[self._tela_atual_key].grid_forget()

        if key not in self._telas_cache:
            if key == "dashboard":
                tela = self._criar_tela_dashboard()
            elif key == "pdv":
                tela = TelaPDV(self.frame_conteudo, usuario=self.usuario)
            elif key == "contas":
                tela = TelaContasReceber(self.frame_conteudo, usuario=self.usuario)
            elif key == "caixa":
                tela = TelaCaixa(self.frame_conteudo, usuario=self.usuario)
            elif key == "relatorios":
                tela = TelaRelatorios(self.frame_conteudo, usuario=self.usuario)
            elif key == "produtos":
                tela = TelaProdutos(self.frame_conteudo)
            elif key == "clientes":
                tela = TelaClientes(self.frame_conteudo)
            elif key == "fornecedores":
                tela = TelaFornecedores(self.frame_conteudo)
            self._telas_cache[key] = tela
        else:
            tela = self._telas_cache[key]
            if key == "dashboard":
                self._atualizar_dashboard_dados()
            elif hasattr(tela, "_load"):
                tela._load()
            elif hasattr(tela, "_filtrar"):
                tela._filtrar("HOJE")

        tela.grid(row=0, column=0, sticky="nsew")
        self._tela_atual_key = key

    def _criar_tela_dashboard(self):
        frame = ctk.CTkFrame(self.frame_conteudo, fg_color="transparent")
        frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(frame, text="📊  Painel Geral / Dashboard", font=("Segoe UI", 22, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(24, 20), padx=24)

        self._dash_cards_lbls = {}
        cards = [
            ("💰 Total em Vendas",   "#00897b", "vendas"),
            ("📖 A Receber (Fiado)", "#c2185b", "fiado"),
            ("📦 Produtos Ativos",   "#6a1b9a", "produtos"),
            ("👤 Clientes",          "#1a73e8", "clientes"),
        ]

        for col, (titulo, cor, k) in enumerate(cards):
            card = ctk.CTkFrame(frame, corner_radius=10, fg_color=cor)
            card.grid(row=1, column=col, padx=(24 if col==0 else 8, 24 if col==3 else 8), pady=8, sticky="ew")
            ctk.CTkLabel(card, text=titulo, font=("Segoe UI", 12), text_color="white").pack(padx=16, pady=(14, 2))
            lbl_val = ctk.CTkLabel(card, text="0", font=("Segoe UI", 24, "bold"), text_color="white")
            lbl_val.pack(padx=16, pady=(0, 14))
            self._dash_cards_lbls[k] = lbl_val

        info = ctk.CTkFrame(frame, corner_radius=8, fg_color="white")
        info.grid(row=2, column=0, columnspan=4, pady=24, padx=24, sticky="ew")
        ctk.CTkLabel(info, text="💡 Dica: Vendas finalizadas como 'A PRAZO (FIADO)' criam automaticamente títulos no 'Contas a Receber'.",
                     font=("Segoe UI", 12)).pack(padx=20, pady=16)

        self._atualizar_dashboard_dados()
        return frame

    def _atualizar_dashboard_dados(self):
        if not hasattr(self, "_dash_cards_lbls"):
            return
        tot_cli  = db_session.query(Cliente).filter_by(ativo=True).count()
        tot_prod = db_session.query(Produto).filter_by(ativo=True).count()
        vendas = db_session.query(Venda).filter_by(status="CONCLUIDA").all()
        tot_vendas_valor = sum(v.total for v in vendas)

        contas = db_session.query(ContaReceber).filter(ContaReceber.status.in_(["PENDENTE", "PARCIAL"])).all()
        tot_fiado = sum(c.saldo_devedor for c in contas)

        self._dash_cards_lbls["vendas"].configure(
            text=f"R$ {tot_vendas_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        self._dash_cards_lbls["fiado"].configure(
            text=f"R$ {tot_fiado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        self._dash_cards_lbls["produtos"].configure(text=str(tot_prod))
        self._dash_cards_lbls["clientes"].configure(text=str(tot_cli))


if __name__ == "__main__":
    criar_tabelas()
    criar_admin_padrao()
    app = App()
    app.mainloop()
