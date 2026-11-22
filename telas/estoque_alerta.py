"""
Tela de Gestão de Estoque e Alerta de Reposição (Produtos com Estoque Crítico ou Abaixo do Mínimo).
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
from core.database import db_session, Produto
from telas.widgets import estilo_tree

COR = "#e65100"
VM  = "#d32f2f"
VD  = "#2e7d32"


class ModalAjusteRapido(ctk.CTkToplevel):
    def __init__(self, master, produto, on_sucesso=None):
        super().__init__(master)
        self.produto = produto
        self.on_sucesso = on_sucesso

        self.title("Ajuste Rápido de Estoque")
        self.geometry("420x360")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"420x360+{(sw-420)//2}+{(sh-360)//2}")

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        h = ctk.CTkFrame(self, fg_color=COR, height=45, corner_radius=0)
        h.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(h, text=f"📦 Reposição / Ajuste — #{self.produto.id}",
                     font=("Segoe UI", 13, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)

        ctk.CTkLabel(f, text=f"{self.produto.descricao}", font=("Segoe UI", 12, "bold"), wraplength=380).pack(anchor="w", pady=(0, 6))

        info_box = ctk.CTkFrame(f, fg_color="#fff3e0", corner_radius=6)
        info_box.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(info_box, text=f"Estoque Atual: {self.produto.estoque:.2f} {self.produto.unidade}   |   Mínimo: {self.produto.estoque_minimo:.2f}",
                     font=("Segoe UI", 11, "bold"), text_color="#bf360c").pack(padx=12, pady=8)

        ctk.CTkLabel(f, text="Quantidade a Adicionar ao Estoque (+):", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.ent_adicionar = ctk.CTkEntry(f, height=36, font=("Segoe UI", 13))
        self.ent_adicionar.insert(0, "10")
        self.ent_adicionar.pack(fill="x", pady=(0, 10))
        self.ent_adicionar.focus()

        ctk.CTkLabel(f, text="Ou Definir Novo Estoque Total Exato:", font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 2))
        self.ent_exato = ctk.CTkEntry(f, height=36, placeholder_text="Opcional")
        self.ent_exato.pack(fill="x", pady=(0, 14))

        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))

        ctk.CTkButton(bot, text="Confirmar Reposição", font=("Segoe UI", 12, "bold"), fg_color=VD,
                      height=40, command=self._confirmar).pack(side="right", padx=4)
        ctk.CTkButton(bot, text="Cancelar", fg_color="gray40", height=40, command=self.destroy).pack(side="right", padx=4)

    def _confirmar(self):
        exato = self.ent_exato.get().strip()
        adicionar = self.ent_adicionar.get().strip()

        try:
            if exato:
                novo_estoque = float(exato.replace(",", "."))
            else:
                qtd_add = float(adicionar.replace(",", "."))
                novo_estoque = (self.produto.estoque or 0.0) + qtd_add

            self.produto.estoque = novo_estoque
            db_session.commit()
            messagebox.showinfo("Sucesso", f"Estoque atualizado para {novo_estoque:.2f} {self.produto.unidade}!", parent=self)
            if self.on_sucesso:
                self.on_sucesso()
            self.destroy()
        except Exception as ex:
            db_session.rollback()
            messagebox.showerror("Erro", str(ex), parent=self)


class TelaEstoqueAlerta(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._ui()
        self._load()

    def _ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        estilo_tree()

        # Header
        h = ctk.CTkFrame(self, fg_color=COR, corner_radius=8)
        h.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        ctk.CTkLabel(h, text="⚠️  Alerta de Estoque Baixo / Reposição",
                     font=("Segoe UI", 16, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        ctk.CTkButton(h, text="📦 Repor Estoque do Selecionado", width=220, height=34, font=("Segoe UI", 12, "bold"),
                      fg_color="white", text_color=COR, hover_color="#ffe0b2",
                      command=self._ajustar_selecionado).pack(side="right", padx=14, pady=8)

        # Barra de Status
        bar = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        bar.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        bar.grid_columnconfigure(2, weight=1)

        self.filtro_tipo = ctk.CTkSegmentedButton(bar, values=["ABAIXO DO MÍNIMO", "ZERADOS", "TODOS"],
                                                  command=lambda v: self._load())
        self.filtro_tipo.set("ABAIXO DO MÍNIMO")
        self.filtro_tipo.grid(row=0, column=0, padx=12, pady=10)

        self.ent_busca = ctk.CTkEntry(bar, placeholder_text="🔍 Filtrar produto...", width=260)
        self.ent_busca.grid(row=0, column=1, padx=6, pady=10)
        self.ent_busca.bind("<KeyRelease>", lambda e: self._load())

        self.lbl_contagem = ctk.CTkLabel(bar, text="0 itens em alerta", font=("Segoe UI", 13, "bold"), text_color=COR)
        self.lbl_contagem.grid(row=0, column=2, sticky="e", padx=20)

        # Tabela
        t_frame = ctk.CTkFrame(self, corner_radius=8)
        t_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(6, 16))
        t_frame.grid_columnconfigure(0, weight=1)
        t_frame.grid_rowconfigure(0, weight=1)

        cols = ("ID", "Cód. Barras", "Descrição do Produto", "Unid", "Estoque Atual", "Estoque Mínimo", "Déficit / Falta", "Fornecedor")
        self.tv = ttk.Treeview(t_frame, columns=cols, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols: self.tv.heading(c, text=c)

        self.tv.column("ID",                   width=50,  anchor="center")
        self.tv.column("Cód. Barras",           width=110, anchor="center")
        self.tv.column("Descrição do Produto",   width=260)
        self.tv.column("Unid",                  width=50,  anchor="center")
        self.tv.column("Estoque Atual",         width=95,  anchor="e")
        self.tv.column("Estoque Mínimo",        width=95,  anchor="e")
        self.tv.column("Déficit / Falta",       width=100, anchor="e")
        self.tv.column("Fornecedor",            width=160)

        self.tv.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        sb = ttk.Scrollbar(t_frame, orient="vertical", command=self.tv.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=10)
        self.tv.configure(yscrollcommand=sb.set)

        self.tv.bind("<Double-1>", lambda e: self._ajustar_selecionado())

    def _load(self):
        for r in self.tv.get_children():
            self.tv.delete(r)

        tipo = self.filtro_tipo.get()
        busca = self.ent_busca.get().strip()

        q = db_session.query(Produto).filter_by(ativo=True)

        if tipo == "ZERADOS":
            q = q.filter(Produto.estoque <= 0.0)
        elif tipo == "ABAIXO DO MÍNIMO":
            q = q.filter((Produto.estoque <= Produto.estoque_minimo) | (Produto.estoque <= 0.0))

        if busca:
            q = q.filter(
                Produto.descricao.ilike(f"%{busca}%") |
                Produto.codigo_barras.ilike(f"%{busca}%")
            )

        produtos = q.order_by(Produto.estoque.asc()).all()

        self.lbl_contagem.configure(text=f"{len(produtos)} produto(s) precisando de reposição")

        for p in produtos:
            forn_nome = p.fornecedor.nome if p.fornecedor else "(Sem Fornecedor)"
            falta = max(0.0, (p.estoque_minimo or 0.0) - (p.estoque or 0.0))
            self.tv.insert("", "end", iid=str(p.id), values=(
                p.id,
                p.codigo_barras or "",
                p.descricao,
                p.unidade or "UN",
                f"{p.estoque:.2f}",
                f"{p.estoque_minimo:.2f}",
                f"{falta:.2f}" if falta > 0 else "0.00",
                forn_nome
            ))

    def _ajustar_selecionado(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um produto da lista para repor o estoque.")
            return

        prod = db_session.query(Produto).get(int(sel[0]))
        if prod:
            ModalAjusteRapido(self, produto=prod, on_sucesso=self._load)
