"""
Tela de Listagem de Fornecedores (Código manual removido - chave primária ID automática).
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
from telas.widgets import estilo_tree, label, entry
from core.database import db_session, Fornecedor

COR = "#f57c00"
VM  = "#e53935"
VD  = "#2e7d32"


class ModalFornecedor(ctk.CTkToplevel):
    def __init__(self, master, fornecedor=None, on_salvar=None):
        super().__init__(master)
        self.fornecedor = fornecedor
        self.on_salvar = on_salvar
        self.title("Editar Fornecedor" if fornecedor else "Novo Fornecedor")
        self.geometry("520x520")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"520x520+{(sw-520)//2}+{(sh-520)//2}")

        self._build()
        if fornecedor:
            self._preencher()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        h = ctk.CTkFrame(self, fg_color=COR, corner_radius=0, height=50)
        h.grid(row=0, column=0, sticky="ew")
        titulo = "✏️ Editar Fornecedor" if self.fornecedor else "🏭 Novo Fornecedor"
        ctk.CTkLabel(h, text=titulo, font=("Segoe UI", 16, "bold"), text_color="white").pack(side="left", padx=20, pady=12)

        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        form.grid_columnconfigure(1, weight=1)

        campos = [
            ("Nome / Razão Social *", "nome"),
            ("CNPJ",                  "cnpj"),
            ("Telefone",              "telefone"),
            ("E-mail",                "email"),
            ("Pessoa de Contato",     "contato"),
            ("Endereço",              "endereco"),
            ("Cidade",                "cidade"),
            ("Estado (UF)",           "estado"),
        ]

        self.ents = {}
        for r, (lbl, key) in enumerate(campos):
            ctk.CTkLabel(form, text=lbl, font=("Segoe UI", 11, "bold")).grid(row=r, column=0, sticky="w", padx=10, pady=4)
            e = ctk.CTkEntry(form, height=32)
            e.grid(row=r, column=1, sticky="ew", padx=10, pady=4)
            self.ents[key] = e

        r_obs = len(campos)
        ctk.CTkLabel(form, text="Observação", font=("Segoe UI", 11, "bold")).grid(row=r_obs, column=0, sticky="nw", padx=10, pady=4)
        self.obs = ctk.CTkTextbox(form, height=60)
        self.obs.grid(row=r_obs, column=1, sticky="ew", padx=10, pady=4)

        bot = ctk.CTkFrame(self, fg_color="transparent", height=55)
        bot.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 15))
        ctk.CTkButton(bot, text="Salvar Fornecedor", font=("Segoe UI", 12, "bold"), fg_color=VD,
                      height=38, command=self._salvar).pack(side="right", padx=6)
        ctk.CTkButton(bot, text="Cancelar", fg_color="gray40", height=38,
                      command=self.destroy).pack(side="right", padx=6)

    def _preencher(self):
        f = self.fornecedor
        for k, e in self.ents.items():
            val = getattr(f, k)
            e.insert(0, "" if val is None else str(val))
        self.obs.insert("1.0", f.observacao or "")

    def _salvar(self):
        d = {k: e.get().strip() for k, e in self.ents.items()}
        if not d["nome"]:
            messagebox.showerror("Aviso", "O Nome / Razão Social é obrigatório!", parent=self)
            return

        f = self.fornecedor or Fornecedor()
        if not self.fornecedor:
            db_session.add(f)

        for k, v in d.items():
            setattr(f, k, v or None)

        f.observacao = self.obs.get("1.0", "end").strip() or None

        try:
            db_session.commit()
            if self.on_salvar:
                self.on_salvar()
            self.destroy()
        except Exception as ex:
            db_session.rollback()
            messagebox.showerror("Erro ao Salvar", str(ex), parent=self)


class TelaFornecedores(ctk.CTkFrame):
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
        label(h, "🏭  Gestão de Fornecedores", font=("Segoe UI", 16, "bold"), text_color="white").pack(side="left", padx=16, pady=10)
        ctk.CTkButton(h, text="+ Novo Fornecedor", width=140, height=34, font=("Segoe UI", 12, "bold"),
                      fg_color="white", text_color=COR, hover_color="#ffe0b2",
                      command=self._novo).pack(side="right", padx=14, pady=8)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        bar.grid_columnconfigure(0, weight=1)

        self.busca = entry(bar, placeholder_text="🔍 Pesquisar fornecedor por nome, CNPJ, telefone...")
        self.busca.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.busca.bind("<KeyRelease>", lambda e: self._load(self.busca.get()))

        ctk.CTkButton(bar, text="✏️ Editar", width=100, height=32, fg_color="#1a73e8", command=self._editar).grid(row=0, column=1, padx=4)
        ctk.CTkButton(bar, text="🗑️ Excluir", width=100, height=32, fg_color=VM, command=self._excluir).grid(row=0, column=2, padx=4)

        t_frame = ctk.CTkFrame(self, corner_radius=8)
        t_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 16))
        t_frame.grid_columnconfigure(0, weight=1)
        t_frame.grid_rowconfigure(0, weight=1)

        cols = ("#", "Nome / Razão Social", "CNPJ", "Telefone", "E-mail", "Contato", "Cidade", "UF")
        self.tv = ttk.Treeview(t_frame, columns=cols, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols:
            self.tv.heading(c, text=c)

        self.tv.column("#",                     width=50,  anchor="center")
        self.tv.column("Nome / Razão Social",    width=240)
        self.tv.column("CNPJ",                  width=140, anchor="center")
        self.tv.column("Telefone",              width=110, anchor="center")
        self.tv.column("E-mail",                width=160)
        self.tv.column("Contato",               width=120)
        self.tv.column("Cidade",                width=120)
        self.tv.column("UF",                    width=45,  anchor="center")

        self.tv.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        sb = ttk.Scrollbar(t_frame, orient="vertical", command=self.tv.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=10)
        self.tv.configure(yscrollcommand=sb.set)

        self.tv.bind("<Double-1>", lambda e: self._editar())

    def _load(self, f=""):
        for r in self.tv.get_children():
            self.tv.delete(r)
        q = db_session.query(Fornecedor).filter_by(ativo=True)
        if f:
            q = q.filter(
                Fornecedor.nome.ilike(f"%{f}%") |
                Fornecedor.cnpj.ilike(f"%{f}%") |
                Fornecedor.telefone.ilike(f"%{f}%")
            )
        for fo in q.order_by(Fornecedor.nome):
            self.tv.insert("", "end", iid=str(fo.id),
                           values=(fo.id, fo.nome, fo.cnpj or "",
                                   fo.telefone or "", fo.email or "",
                                   fo.contato or "", fo.cidade or "", fo.estado or ""))

    def _sel(self):
        s = self.tv.selection()
        if not s:
            messagebox.showwarning("Atenção", "Selecione um fornecedor.")
            return None
        return db_session.query(Fornecedor).get(int(s[0]))

    def _novo(self):
        ModalFornecedor(self, on_salvar=self._load)

    def _editar(self):
        fo = self._sel()
        if fo:
            ModalFornecedor(self, fornecedor=fo, on_salvar=self._load)

    def _excluir(self):
        fo = self._sel()
        if not fo:
            return
        if not messagebox.askyesno("Confirmar Exclusão", f"Excluir fornecedor '{fo.nome}'?"):
            return
        fo.ativo = False
        try:
            db_session.commit()
            self._load(self.busca.get())
        except Exception as ex:
            db_session.rollback()
            messagebox.showerror("Erro", str(ex))
