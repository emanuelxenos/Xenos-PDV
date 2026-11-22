"""
Tela de Relatórios e Histórico de Vendas com Filtros por Período e Forma de Pagamento.
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
from core.database import db_session, Venda, Cliente
from core.impressao import emitir_comprovante
from datetime import datetime, date, timedelta

COR = "#4527a0"


class TelaRelatorios(ctk.CTkFrame):
    def __init__(self, master, usuario=None, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.usuario = usuario
        self._ui()
        self._filtrar("HOJE")

    def _ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Cabeçalho
        h = ctk.CTkFrame(self, fg_color=COR, corner_radius=8)
        h.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        ctk.CTkLabel(h, text="📊  Relatórios e Histórico de Vendas", font=("Segoe UI", 16, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        ctk.CTkButton(h, text="🧾 Reemitir Comprovante", width=170, height=34, font=("Segoe UI", 11, "bold"),
                      fg_color="white", text_color=COR, hover_color="#ede7f6", command=self._reemitir).pack(side="right", padx=14, pady=8)

        # Barra de Filtros
        bar = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        bar.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        bar.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(bar, text="Filtrar Período:", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, padx=12, pady=10)

        botoes = [
            ("Hoje",       "HOJE"),
            ("Últimos 7d", "7DIAS"),
            ("Este Mês",   "MES"),
            ("Todas",      "TODAS")
        ]
        self.btn_filtros = {}
        for c, (lbl, k) in enumerate(botoes, 1):
            btn = ctk.CTkButton(bar, text=lbl, width=85, height=30, fg_color="gray75", text_color="black",
                                command=lambda chave=k: self._filtrar(chave))
            btn.grid(row=0, column=c, padx=4, pady=10)
            self.btn_filtros[k] = btn

        # Totalizador na Barra
        self.lbl_resumo = ctk.CTkLabel(bar, text="Total: R$ 0,00  |  Qtd: 0 vendas", font=("Segoe UI", 13, "bold"), text_color=COR)
        self.lbl_resumo.grid(row=0, column=5, sticky="e", padx=20)

        # Tabela de Vendas
        t_frame = ctk.CTkFrame(self, corner_radius=8)
        t_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(6, 16))
        t_frame.grid_columnconfigure(0, weight=1)
        t_frame.grid_rowconfigure(0, weight=1)

        cols = ("Venda Nº", "Data e Hora", "Cliente", "Operador", "Forma Pgto", "Subtotal", "Desconto", "Total Venda")
        self.tv = ttk.Treeview(t_frame, columns=cols, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols: self.tv.heading(c, text=c)

        self.tv.column("Venda Nº",    width=80,  anchor="center")
        self.tv.column("Data e Hora", width=140, anchor="center")
        self.tv.column("Cliente",     width=220)
        self.tv.column("Operador",    width=130, anchor="center")
        self.tv.column("Forma Pgto",  width=130, anchor="center")
        self.tv.column("Subtotal",    width=90,  anchor="e")
        self.tv.column("Desconto",    width=85,  anchor="e")
        self.tv.column("Total Venda", width=105, anchor="e")

        self.tv.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        sb = ttk.Scrollbar(t_frame, orient="vertical", command=self.tv.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=10)
        self.tv.configure(yscrollcommand=sb.set)

    def _filtrar(self, periodo):
        for k, btn in self.btn_filtros.items():
            btn.configure(fg_color=COR if k == periodo else "gray80",
                          text_color="white" if k == periodo else "black")

        for r in self.tv.get_children():
            self.tv.delete(r)

        hoje = date.today()
        q = db_session.query(Venda).filter_by(status="CONCLUIDA")

        if periodo == "HOJE":
            q = q.filter(Venda.data >= datetime(hoje.year, hoje.month, hoje.day, 0, 0, 0))
        elif periodo == "7DIAS":
            d7 = hoje - timedelta(days=7)
            q = q.filter(Venda.data >= datetime(d7.year, d7.month, d7.day, 0, 0, 0))
        elif periodo == "MES":
            q = q.filter(Venda.data >= datetime(hoje.year, hoje.month, 1, 0, 0, 0))

        vendas = q.order_by(Venda.id.desc()).all()
        total_acumulado = sum(v.total for v in vendas)
        self.lbl_resumo.configure(text=f"Total: R$ {total_acumulado:,.2f}  |  Qtd: {len(vendas)} vendas".replace(",", "X").replace(".", ",").replace("X", "."))

        for v in vendas:
            cli = v.cliente.nome if v.cliente else "Consumidor Final"
            op = v.usuario.nome if v.usuario else "Operador"
            self.tv.insert("", "end", iid=str(v.id), values=(
                f"#{v.numero:06d}",
                v.data.strftime("%d/%m/%Y %H:%M"),
                cli,
                op,
                v.forma_pgto,
                f"R$ {v.subtotal:.2f}",
                f"R$ {v.desconto:.2f}",
                f"R$ {v.total:.2f}"
            ))

    def _reemitir(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma venda na lista para reemitir o comprovante.")
            return

        v = db_session.query(Venda).get(int(sel[0]))
        if v:
            op_nome = v.usuario.nome if v.usuario else "Operador"
            emitir_comprovante(v, v.itens, operador=op_nome, abrir_visualizacao=True)
