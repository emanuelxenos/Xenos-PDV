"""
Tela de Listagem de Produtos (Código manual removido - chave primária ID automática).
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
from telas.widgets import estilo_tree, label, entry
from core.database import db_session, Produto, Fornecedor

COR = "#6a1b9a"
VM  = "#e53935"
VD  = "#2e7d32"


class ModalProduto(ctk.CTkToplevel):
    def __init__(self, master, produto=None, on_salvar=None):
        super().__init__(master)
        self.produto = produto
        self.on_salvar = on_salvar
        self._mapa_forn = {}
        self.title("Editar Produto" if produto else "Novo Produto")
        self.geometry("540x580")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"540x580+{(sw-540)//2}+{(sh-580)//2}")

        self._build()
        if produto:
            self._preencher()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        h = ctk.CTkFrame(self, fg_color=COR, corner_radius=0, height=50)
        h.grid(row=0, column=0, sticky="ew")
        titulo = "✏️ Editar Produto" if self.produto else "📦 Novo Produto"
        ctk.CTkLabel(h, text=titulo, font=("Segoe UI", 16, "bold"), text_color="white").pack(side="left", padx=20, pady=12)

        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        form.grid_columnconfigure(1, weight=1)

        # Sem código manual: só Descrição e Cód. Barras opcional
        campos_txt = [
            ("Descrição do Produto *", "descricao"),
            ("Cód. Barras (EAN)",       "codigo_barras"),
            ("NCM",                     "ncm"),
        ]

        self.ents = {}
        r = 0
        for lbl, key in campos_txt:
            ctk.CTkLabel(form, text=lbl, font=("Segoe UI", 11, "bold")).grid(row=r, column=0, sticky="w", padx=10, pady=4)
            e = ctk.CTkEntry(form, height=32)
            e.grid(row=r, column=1, sticky="ew", padx=10, pady=4)
            self.ents[key] = e
            r += 1

        ctk.CTkLabel(form, text="Unidade Medida", font=("Segoe UI", 11, "bold")).grid(row=r, column=0, sticky="w", padx=10, pady=4)
        self.combo_unid = ctk.CTkComboBox(form, values=["UN", "KG", "M", "L", "CX", "PCT", "PAR", "FARDO", "SACO"], height=32)
        self.combo_unid.set("UN")
        self.combo_unid.grid(row=r, column=1, sticky="ew", padx=10, pady=4)
        r += 1

        campos_num = [
            ("Preço Compra (R$)", "preco_compra"),
            ("Preço Venda (R$)",  "preco_venda"),
            ("Estoque Atual",     "estoque"),
            ("Estoque Mínimo",    "estoque_minimo"),
        ]
        for lbl, key in campos_num:
            ctk.CTkLabel(form, text=lbl, font=("Segoe UI", 11, "bold")).grid(row=r, column=0, sticky="w", padx=10, pady=4)
            e = ctk.CTkEntry(form, height=32)
            e.grid(row=r, column=1, sticky="ew", padx=10, pady=4)
            self.ents[key] = e
            r += 1

        ctk.CTkLabel(form, text="Fornecedor", font=("Segoe UI", 11, "bold")).grid(row=r, column=0, sticky="w", padx=10, pady=4)
        self.combo_forn = ctk.CTkComboBox(form, values=self._listar_fornecedores(), height=32)
        self.combo_forn.grid(row=r, column=1, sticky="ew", padx=10, pady=4)
        r += 1

        ctk.CTkLabel(form, text="Observação", font=("Segoe UI", 11, "bold")).grid(row=r, column=0, sticky="nw", padx=10, pady=4)
        self.obs = ctk.CTkTextbox(form, height=55)
        self.obs.grid(row=r, column=1, sticky="ew", padx=10, pady=4)

        bot = ctk.CTkFrame(self, fg_color="transparent", height=55)
        bot.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 15))
        ctk.CTkButton(bot, text="Salvar Produto", font=("Segoe UI", 12, "bold"), fg_color=VD,
                      height=38, command=self._salvar).pack(side="right", padx=6)
        ctk.CTkButton(bot, text="Cancelar", fg_color="gray40", height=38,
                      command=self.destroy).pack(side="right", padx=6)

    def _listar_fornecedores(self):
        forns = db_session.query(Fornecedor).filter_by(ativo=True).order_by(Fornecedor.nome).all()
        self._mapa_forn = {f.nome: f.id for f in forns}
        return ["(Nenhum)"] + [f.nome for f in forns]

    def _preencher(self):
        p = self.produto
        for k, e in self.ents.items():
            val = getattr(p, k)
            e.insert(0, "" if val is None else str(val))
        if p.unidade:
            self.combo_unid.set(p.unidade)
        if p.fornecedor:
            self.combo_forn.set(p.fornecedor.nome)
        else:
            self.combo_forn.set("(Nenhum)")
        self.obs.insert("1.0", p.observacao or "")

    def _salvar(self):
        d = {k: e.get().strip() for k, e in self.ents.items()}
        if not d["descricao"]:
            messagebox.showerror("Aviso", "A Descrição do produto é obrigatória!", parent=self)
            return

        def _val(k):
            try: return float(d[k].replace(",", "."))
            except: return 0.0

        p = self.produto or Produto()
        if not self.produto:
            db_session.add(p)

        p.codigo_barras = d["codigo_barras"] or None
        p.descricao = d["descricao"]
        p.ncm = d["ncm"] or None
        p.unidade = self.combo_unid.get() or "UN"
        p.preco_compra = _val("preco_compra")
        p.preco_venda = _val("preco_venda")
        p.estoque = _val("estoque")
        p.estoque_minimo = _val("estoque_minimo")

        forn_nome = self.combo_forn.get()
        p.fornecedor_id = self._mapa_forn.get(forn_nome)
        p.observacao = self.obs.get("1.0", "end").strip() or None

        eh_novo = (self.produto is None)
        try:
            db_session.commit()
            msg = f"Produto '{p.descricao}' cadastrado com sucesso!" if eh_novo else f"Produto '{p.descricao}' atualizado com sucesso!"
            messagebox.showinfo("Sucesso", msg, parent=self)
            if self.on_salvar:
                self.on_salvar()
            self.destroy()
        except Exception as ex:
            db_session.rollback()
            messagebox.showerror("Erro ao Salvar Produto", f"Não foi possível salvar o produto:\n\n{str(ex)}", parent=self)


class TelaProdutos(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._ui()
        self._load()

    def _ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        estilo_tree()

        h = ctk.CTkFrame(self, fg_color=COR, corner_radius=8)
        h.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        label(h, "📦  Gestão de Produtos e Estoque", font=("Segoe UI", 16, "bold"), text_color="white").pack(side="left", padx=16, pady=10)
        ctk.CTkButton(h, text="+ Novo Produto", width=140, height=34, font=("Segoe UI", 12, "bold"),
                      fg_color="white", text_color=COR, hover_color="#e1bee7",
                      command=self._novo).pack(side="right", padx=14, pady=8)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        bar.grid_columnconfigure(0, weight=1)

        self.busca = entry(bar, placeholder_text="🔍 Pesquisar por ID, código de barras ou descrição...")
        self.busca.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.busca.bind("<KeyRelease>", lambda e: self._load(self.busca.get()))

        ctk.CTkButton(bar, text="✏️ Editar", width=100, height=32, fg_color="#1a73e8", command=self._editar).grid(row=0, column=1, padx=4)
        ctk.CTkButton(bar, text="🗑️ Excluir", width=100, height=32, fg_color=VM, command=self._excluir).grid(row=0, column=2, padx=4)

        t_frame = ctk.CTkFrame(self, corner_radius=8)
        t_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 16))
        t_frame.grid_columnconfigure(0, weight=1)
        t_frame.grid_rowconfigure(0, weight=1)

        cols = ("#", "Cód. Barras", "Descrição do Produto", "Unid", "R$ Compra", "R$ Venda", "Estoque", "Estoque Mín.")
        self.tv = ttk.Treeview(t_frame, columns=cols, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols:
            self.tv.heading(c, text=c)

        self.tv.column("#",                     width=50,  anchor="center")
        self.tv.column("Cód. Barras",           width=120, anchor="center")
        self.tv.column("Descrição do Produto",   width=280)
        self.tv.column("Unid",                  width=50,  anchor="center")
        self.tv.column("R$ Compra",             width=85,  anchor="e")
        self.tv.column("R$ Venda",              width=85,  anchor="e")
        self.tv.column("Estoque",               width=75,  anchor="e")
        self.tv.column("Estoque Mín.",          width=80,  anchor="e")

        self.tv.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        sb = ttk.Scrollbar(t_frame, orient="vertical", command=self.tv.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=10)
        self.tv.configure(yscrollcommand=sb.set)

        self.tv.bind("<Double-1>", lambda e: self._editar())

    def _load(self, f=""):
        for r in self.tv.get_children():
            self.tv.delete(r)
        q = db_session.query(Produto).filter_by(ativo=True)
        if f:
            q = q.filter(
                Produto.descricao.ilike(f"%{f}%") |
                Produto.codigo_barras.ilike(f"%{f}%") |
                (Produto.id == f if f.isdigit() else False)
            )
        for p in q.order_by(Produto.descricao):
            self.tv.insert("", "end", iid=str(p.id),
                           values=(p.id, p.codigo_barras or "", p.descricao,
                                   p.unidade or "UN", f"R$ {p.preco_compra:.2f}",
                                   f"R$ {p.preco_venda:.2f}", f"{p.estoque:.2f}", f"{p.estoque_minimo:.2f}"))

    def _sel(self):
        s = self.tv.selection()
        if not s:
            messagebox.showwarning("Atenção", "Selecione um produto.")
            return None
        return db_session.query(Produto).get(int(s[0]))

    def _novo(self):
        ModalProduto(self, on_salvar=self._load)

    def _editar(self):
        p = self._sel()
        if p:
            ModalProduto(self, produto=p, on_salvar=self._load)

    def _excluir(self):
        p = self._sel()
        if not p:
            return
        if not messagebox.askyesno("Confirmar Exclusão", f"Excluir '{p.descricao}'?"):
            return
        p.ativo = False
        try:
            db_session.commit()
            self._load(self.busca.get())
        except Exception as ex:
            db_session.rollback()
            messagebox.showerror("Erro", str(ex))
