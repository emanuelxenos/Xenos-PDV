"""
Tela de Seleção e Impressão de Etiquetas de Produtos (Folhas A4 / Etiquetas Adesivas).
Permite buscar produtos, definir quantidade de etiquetas e gerar o PDF com código de barras.
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
from core.database import db_session, Produto
from core.etiquetas import gerar_pdf_etiquetas
from telas.widgets import estilo_tree

COR = "#00796b"
VD  = "#2e7d32"


class ModalQtdEtiquetas(ctk.CTkToplevel):
    def __init__(self, master, produto, on_adicionar):
        super().__init__(master)
        self.produto = produto
        self.on_adicionar = on_adicionar

        self.title("Quantidade de Etiquetas")
        self.geometry("380x280")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"380x280+{(sw-380)//2}+{(sh-280)//2}")

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        h = ctk.CTkFrame(self, fg_color=COR, height=45, corner_radius=0)
        h.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(h, text="🏷️ Gerar Etiquetas para o Produto", font=("Segoe UI", 12, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)

        ctk.CTkLabel(f, text=f"{self.produto.descricao}", font=("Segoe UI", 12, "bold"), wraplength=340).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(f, text=f"Preço: R$ {self.produto.preco_venda:.2f}  |  Cód: {self.produto.codigo_barras or self.produto.id}",
                     font=("Segoe UI", 10), text_color="gray40").pack(anchor="w", pady=(0, 14))

        ctk.CTkLabel(f, text="Quantas etiquetas deseja imprimir?", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.ent_qtd = ctk.CTkEntry(f, height=36, font=("Segoe UI", 13))
        self.ent_qtd.insert(0, "3")
        self.ent_qtd.pack(fill="x", pady=(0, 14))
        self.ent_qtd.focus()

        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))

        ctk.CTkButton(bot, text="Adicionar à Fila", font=("Segoe UI", 12, "bold"), fg_color=VD,
                      height=38, command=self._confirmar).pack(side="right", padx=4)
        ctk.CTkButton(bot, text="Cancelar", fg_color="gray40", height=38, command=self.destroy).pack(side="right", padx=4)

    def _confirmar(self):
        try:
            qtd = int(self.ent_qtd.get().strip())
            if qtd <= 0: raise ValueError
        except:
            messagebox.showerror("Aviso", "Informe uma quantidade inteira válida!", parent=self)
            return

        self.on_adicionar(self.produto, qtd)
        self.destroy()


class TelaEtiquetas(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.fila_etiquetas = []  # [(produto, qtd), ...]
        self._ui()
        self._load_produtos()

    def _ui(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)
        estilo_tree()

        # ─── HEADER ───
        h = ctk.CTkFrame(self, fg_color=COR, corner_radius=8)
        h.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 8))
        ctk.CTkLabel(h, text="🏷️  Emissão e Impressão de Etiquetas com Código de Barras",
                     font=("Segoe UI", 16, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        ctk.CTkButton(h, text="🖨️ Gerar PDF para Impressão", width=220, height=34, font=("Segoe UI", 12, "bold"),
                      fg_color="white", text_color=COR, hover_color="#e0f2f1",
                      command=self._imprimir_pdf).pack(side="right", padx=14, pady=8)

        # ─── LADO ESQUERDO: Catálogo de Produtos para Escolha ───
        esq = ctk.CTkFrame(self, corner_radius=8)
        esq.grid(row=1, column=0, sticky="nsew", padx=(16, 6), pady=(0, 16))
        esq.grid_columnconfigure(0, weight=1)
        esq.grid_rowconfigure(1, weight=1)

        b_bar = ctk.CTkFrame(esq, fg_color="transparent")
        b_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        b_bar.grid_columnconfigure(0, weight=1)

        self.busca = ctk.CTkEntry(b_bar, placeholder_text="🔍 Buscar produto para gerar etiquetas...", height=32)
        self.busca.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.busca.bind("<KeyRelease>", lambda e: self._load_produtos(self.busca.get()))

        ctk.CTkButton(b_bar, text="+ Adicionar Etiqueta", width=140, height=32, fg_color=COR,
                      command=self._adicionar_selecionado).grid(row=0, column=1)

        cols_p = ("ID", "Cód. Barras", "Descrição", "Preço", "Unid")
        self.tv_prod = ttk.Treeview(esq, columns=cols_p, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols_p: self.tv_prod.heading(c, text=c)

        self.tv_prod.column("ID",          width=45,  anchor="center")
        self.tv_prod.column("Cód. Barras", width=110, anchor="center")
        self.tv_prod.column("Descrição",   width=220)
        self.tv_prod.column("Preço",       width=80,  anchor="e")
        self.tv_prod.column("Unid",        width=45,  anchor="center")

        self.tv_prod.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        sb_p = ttk.Scrollbar(esq, orient="vertical", command=self.tv_prod.yview)
        sb_p.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        self.tv_prod.configure(yscrollcommand=sb_p.set)
        self.tv_prod.bind("<Double-1>", lambda e: self._adicionar_selecionado())

        # ─── LADO DIREITO: Fila de Impressão ───
        dir_frame = ctk.CTkFrame(self, corner_radius=8)
        dir_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 16), pady=(0, 16))
        dir_frame.grid_columnconfigure(0, weight=1)
        dir_frame.grid_rowconfigure(1, weight=1)

        f_topo = ctk.CTkFrame(dir_frame, fg_color="transparent")
        f_topo.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(f_topo, text="📋 Fila de Etiquetas a Imprimir", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.lbl_total_etiq = ctk.CTkLabel(f_topo, text="Total: 0 etiquetas", font=("Segoe UI", 11, "bold"), text_color=COR)
        self.lbl_total_etiq.pack(side="right")

        cols_f = ("Produto", "Preço", "Qtd Etiquetas")
        self.tv_fila = ttk.Treeview(dir_frame, columns=cols_f, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols_f: self.tv_fila.heading(c, text=c)

        self.tv_fila.column("Produto",       width=200)
        self.tv_fila.column("Preço",         width=75, anchor="e")
        self.tv_fila.column("Qtd Etiquetas", width=85, anchor="center")

        self.tv_fila.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        sb_f = ttk.Scrollbar(dir_frame, orient="vertical", command=self.tv_fila.yview)
        sb_f.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        self.tv_fila.configure(yscrollcommand=sb_f.set)

        b_acoes = ctk.CTkFrame(dir_frame, fg_color="transparent")
        b_acoes.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        ctk.CTkButton(b_acoes, text="Remover da Fila", width=120, height=30, fg_color="#d32f2f", command=self._remover_fila).pack(side="left")
        ctk.CTkButton(b_acoes, text="Limpar Fila", width=100, height=30, fg_color="gray40", command=self._limpar_fila).pack(side="right")

    def _load_produtos(self, f=""):
        for r in self.tv_prod.get_children(): self.tv_prod.delete(r)
        q = db_session.query(Produto).filter_by(ativo=True)
        if f:
            q = q.filter(
                Produto.descricao.ilike(f"%{f}%") |
                Produto.codigo_barras.ilike(f"%{f}%") |
                (Produto.id == f if f.isdigit() else False)
            )
        for p in q.order_by(Produto.descricao):
            self.tv_prod.insert("", "end", iid=str(p.id), values=(
                p.id, p.codigo_barras or "", p.descricao, f"R$ {p.preco_venda:.2f}", p.unidade or "UN"
            ))

    def _adicionar_selecionado(self):
        sel = self.tv_prod.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um produto da lista à esquerda para gerar etiquetas.")
            return

        prod = db_session.query(Produto).get(int(sel[0]))
        if prod:
            ModalQtdEtiquetas(self, produto=prod, on_adicionar=self._adicionar_a_fila)

    def _adicionar_a_fila(self, produto, qtd):
        # Se o produto já estiver na fila, soma a quantidade
        for i, (p, q) in enumerate(self.fila_etiquetas):
            if p.id == produto.id:
                self.fila_etiquetas[i] = (p, q + qtd)
                self._atualizar_tabela_fila()
                return

        self.fila_etiquetas.append((produto, qtd))
        self._atualizar_tabela_fila()

    def _remover_fila(self):
        sel = self.tv_fila.selection()
        if not sel: return
        idx = int(sel[0])
        if 0 <= idx < len(self.fila_etiquetas):
            self.fila_etiquetas.pop(idx)
            self._atualizar_tabela_fila()

    def _limpar_fila(self):
        self.fila_etiquetas.clear()
        self._atualizar_tabela_fila()

    def _atualizar_tabela_fila(self):
        for r in self.tv_fila.get_children(): self.tv_fila.delete(r)
        total_etiquetas = 0
        for i, (prod, qtd) in enumerate(self.fila_etiquetas):
            total_etiquetas += qtd
            self.tv_fila.insert("", "end", iid=str(i), values=(
                prod.descricao, f"R$ {prod.preco_venda:.2f}", f"{qtd} un."
            ))
        self.lbl_total_etiq.configure(text=f"Total: {total_etiquetas} etiqueta(s)")

    def _imprimir_pdf(self):
        if not self.fila_etiquetas:
            messagebox.showwarning("Fila Vazia", "Adicione ao menos um produto à fila de etiquetas para gerar a impressão!")
            return

        try:
            caminho = gerar_pdf_etiquetas(self.fila_etiquetas, parent_window=self)
            if caminho:
                messagebox.showinfo("Etiquetas Geradas", "O arquivo PDF com as etiquetas e código de barras foi gerado e aberto para impressão!")
        except Exception as ex:
            messagebox.showerror("Erro ao Gerar PDF", f"Falha ao renderizar etiquetas:\n{str(ex)}")
