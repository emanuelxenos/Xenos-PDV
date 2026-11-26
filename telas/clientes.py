"""
Tela de Listagem de Clientes (Código manual removido - chave primária ID automática).
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
from telas.widgets import estilo_tree, label, entry
from core.database import db_session, Cliente

COR = "#1a73e8"
VM  = "#e53935"
VD  = "#2e7d32"


class ModalCliente(ctk.CTkToplevel):
    def __init__(self, master, cliente=None, on_salvar=None):
        super().__init__(master)
        self.cliente = cliente
        self.on_salvar = on_salvar
        self.title("Editar Cliente" if cliente else "Novo Cliente")
        self.geometry("540x580")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"540x580+{(sw-540)//2}+{(sh-580)//2}")

        self._build()
        if cliente:
            self._preencher()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        h = ctk.CTkFrame(self, fg_color=COR, corner_radius=0, height=50)
        h.grid(row=0, column=0, sticky="ew")
        titulo = "✏️ Editar Cliente" if self.cliente else "👤 Novo Cliente"
        ctk.CTkLabel(h, text=titulo, font=("Segoe UI", 16, "bold"), text_color="white").pack(side="left", padx=20, pady=12)

        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        form.grid_columnconfigure(1, weight=1)

        # Sem campo de código manual: o ID é automático
        campos = [
            ("Nome do Cliente *", "nome"),
            ("Apelido / Vulgo",   "apelido"),
            ("CPF / CNPJ",        "cpf_cnpj"),
            ("Telefone",          "telefone"),
            ("Celular",           "celular"),
            ("E-mail",            "email"),
            ("Endereço",          "endereco"),
            ("Número",            "numero"),
            ("Bairro",            "bairro"),
            ("Cidade",            "cidade"),
            ("Estado (UF)",       "estado"),
            ("CEP",               "cep"),
            ("Limite Crédito (R$)","limite_credito")
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
        ctk.CTkButton(bot, text="Salvar Cliente", font=("Segoe UI", 12, "bold"), fg_color=VD,
                      height=38, command=self._salvar).pack(side="right", padx=6)
        ctk.CTkButton(bot, text="Cancelar", fg_color="gray40", height=38,
                      command=self.destroy).pack(side="right", padx=6)

    def _preencher(self):
        c = self.cliente
        for k, e in self.ents.items():
            val = getattr(c, k)
            e.insert(0, "" if val is None else str(val))
        self.obs.insert("1.0", c.observacao or "")

    def _salvar(self):
        d = {k: e.get().strip() for k, e in self.ents.items()}
        if not d["nome"]:
            messagebox.showerror("Aviso", "O Nome do cliente é obrigatório!", parent=self)
            return

        c = self.cliente or Cliente()
        if not self.cliente:
            db_session.add(c)

        for k, v in d.items():
            if k == "limite_credito":
                try: setattr(c, k, float(v.replace(",", ".")))
                except: setattr(c, k, 0.0)
            else:
                setattr(c, k, v or None)

        c.observacao = self.obs.get("1.0", "end").strip() or None

        eh_novo = (self.cliente is None)
        try:
            db_session.commit()
            msg = f"Cliente '{c.nome}' cadastrado com sucesso!" if eh_novo else f"Cliente '{c.nome}' atualizado com sucesso!"
            messagebox.showinfo("Sucesso", msg, parent=self)
            if self.on_salvar:
                self.on_salvar()
            self.destroy()
        except Exception as ex:
            db_session.rollback()
            messagebox.showerror("Erro ao Salvar Cliente", f"Não foi possível salvar o cliente:\n\n{str(ex)}", parent=self)


class ModalVisualizarCliente(ctk.CTkToplevel):
    """
    Modal de visualização detalhada dos dados do cliente em modo somente-leitura.
    Permite conferir dados cadastrais, endereço, contatos, apelido e filiação
    sem risco de alterar nada por acidente.
    """
    def __init__(self, master, cliente, on_editar=None):
        super().__init__(master)
        self.cliente = cliente
        self.on_editar = on_editar

        self.title(f"Ficha do Cliente — {self.cliente.nome}")
        self.geometry("560x620")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"560x620+{(sw-560)//2}+{(sh-620)//2}")

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        h = ctk.CTkFrame(self, fg_color=COR, corner_radius=0, height=50)
        h.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(h, text=f"👤 Ficha do Cliente #{self.cliente.id:04d}", font=("Segoe UI", 15, "bold"), text_color="white").pack(side="left", padx=20, pady=12)
        if self.cliente.ativo:
            ctk.CTkLabel(h, text="ATIVO", font=("Segoe UI", 10, "bold"), text_color="#c8e6c9").pack(side="right", padx=20)
        else:
            ctk.CTkLabel(h, text="INATIVO", font=("Segoe UI", 10, "bold"), text_color="#ffcdd2").pack(side="right", padx=20)

        # Corpo com Scroll
        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        form.grid_columnconfigure(0, weight=1)

        def _bloco(titulo):
            sec = ctk.CTkFrame(form, fg_color="#eceff1", corner_radius=6)
            sec.pack(fill="x", pady=(10, 4))
            ctk.CTkLabel(sec, text=titulo, font=("Segoe UI", 11, "bold"), text_color="#37474f").pack(anchor="w", padx=10, pady=4)

        def _campo(rotulo, valor, cor_valor=None):
            f_linha = ctk.CTkFrame(form, fg_color="white", corner_radius=6)
            f_linha.pack(fill="x", pady=2)
            f_linha.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(f_linha, text=rotulo, font=("Segoe UI", 10, "bold"), text_color="gray40", width=130, anchor="w").grid(row=0, column=0, padx=12, pady=6, sticky="w")
            txt = str(valor) if valor not in [None, ""] else "—"
            cor = cor_valor if cor_valor else ("#1b5e20" if rotulo == "Limite de Crédito" else "black")
            ctk.CTkLabel(f_linha, text=txt, font=("Segoe UI", 11), text_color=cor, anchor="w").grid(row=0, column=1, padx=(0, 12), pady=6, sticky="ew")

        # Dados Principais
        _bloco("DADOS PRINCIPAIS")
        _campo("Nome Completo", self.cliente.nome)
        _campo("Apelido / Vulgo", self.cliente.apelido)
        _campo("CPF / CNPJ", self.cliente.cpf_cnpj)
        lim_txt = f"R$ {self.cliente.limite_credito:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if self.cliente.limite_credito else "R$ 0,00"
        _campo("Limite de Crédito", lim_txt)

        # Contato
        _bloco("CONTATO")
        _campo("Celular", self.cliente.celular)
        _campo("Telefone Fixo", self.cliente.telefone)
        _campo("E-mail", self.cliente.email)

        # Endereço
        _bloco("ENDEREÇO")
        _campo("Logradouro", self.cliente.endereco)
        _campo("Número", self.cliente.numero)
        _campo("Bairro", self.cliente.bairro)
        _campo("Cidade / UF", f"{self.cliente.cidade or 'QUIXABA'} - {self.cliente.estado or 'PE'}")
        _campo("CEP", self.cliente.cep)

        # Observações e Filiação
        _bloco("OBSERVAÇÕES / OUTROS DADOS")
        obs_txt = self.cliente.observacao or "Nenhuma observação registrada."
        f_obs = ctk.CTkFrame(form, fg_color="white", corner_radius=6)
        f_obs.pack(fill="x", pady=2)
        ctk.CTkLabel(f_obs, text=obs_txt, font=("Segoe UI", 11), text_color="#37474f", wraplength=480, justify="left").pack(anchor="w", padx=12, pady=8)

        # Data de Cadastro
        if self.cliente.criado_em:
            dt_cad = self.cliente.criado_em.strftime("%d/%m/%Y às %H:%M") if hasattr(self.cliente.criado_em, "strftime") else str(self.cliente.criado_em)
            _campo("Cadastrado em", dt_cad)

        # Rodapé
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 14))

        ctk.CTkButton(bot, text="Fechar", width=100, height=36, fg_color="gray40", command=self.destroy).pack(side="right")
        if self.on_editar:
            ctk.CTkButton(bot, text="✏️ Editar Dados", width=130, height=36, font=("Segoe UI", 11, "bold"),
                          fg_color=COR, command=self._chamar_editar).pack(side="right", padx=8)

    def _chamar_editar(self):
        self.destroy()
        if self.on_editar:
            self.on_editar(self.cliente)


class TelaClientes(ctk.CTkFrame):
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
        label(h, "👤  Gestão de Clientes", font=("Segoe UI", 16, "bold"), text_color="white").pack(side="left", padx=16, pady=10)
        ctk.CTkButton(h, text="+ Novo Cliente", width=130, height=34, font=("Segoe UI", 12, "bold"),
                      fg_color="white", text_color=COR, hover_color="#d0e4ff",
                      command=self._novo).pack(side="right", padx=14, pady=8)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        bar.grid_columnconfigure(0, weight=1)

        self.busca = entry(bar, placeholder_text="🔍 Pesquisar cliente por nome, CPF/CNPJ, telefone ou cidade...")
        self.busca.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.busca.bind("<KeyRelease>", lambda e: self._load(self.busca.get()))

        ctk.CTkButton(bar, text="👁️ Visualizar", width=105, height=32, font=("Segoe UI", 11, "bold"), fg_color="#00695c", hover_color="#004d40", command=self._visualizar).grid(row=0, column=1, padx=3)
        ctk.CTkButton(bar, text="📜 Extrato", width=100, height=32, fg_color="#880e4f", hover_color="#ad1457", command=self._extrato).grid(row=0, column=2, padx=3)
        ctk.CTkButton(bar, text="✏️ Editar", width=90, height=32, fg_color=COR, command=self._editar).grid(row=0, column=3, padx=3)
        ctk.CTkButton(bar, text="🗑️ Excluir", width=90, height=32, fg_color=VM, command=self._excluir).grid(row=0, column=4, padx=3)

        t_frame = ctk.CTkFrame(self, corner_radius=8)
        t_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 16))
        t_frame.grid_columnconfigure(0, weight=1)
        t_frame.grid_rowconfigure(0, weight=1)

        cols = ("#", "Nome", "Apelido", "CPF / CNPJ", "Telefone", "Celular", "Cidade", "UF", "Limite Crédito")
        self.tv = ttk.Treeview(t_frame, columns=cols, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols:
            self.tv.heading(c, text=c)

        self.tv.column("#",               width=50,  anchor="center")
        self.tv.column("Nome",            width=240)
        self.tv.column("CPF / CNPJ",      width=140, anchor="center")
        self.tv.column("Telefone",        width=110, anchor="center")
        self.tv.column("Celular",         width=110, anchor="center")
        self.tv.column("Cidade",          width=130)
        self.tv.column("UF",              width=45,  anchor="center")
        self.tv.column("Limite Crédito",  width=110, anchor="e")

        self.tv.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        sb = ttk.Scrollbar(t_frame, orient="vertical", command=self.tv.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=10)
        self.tv.configure(yscrollcommand=sb.set)

        self.tv.bind("<Double-1>", lambda e: self._visualizar())

    def _load(self, f=""):
        for r in self.tv.get_children():
            self.tv.delete(r)
        q = db_session.query(Cliente).filter_by(ativo=True)
        if f:
            q = q.filter(
                Cliente.nome.ilike(f"%{f}%") |
                Cliente.apelido.ilike(f"%{f}%") |
                Cliente.cpf_cnpj.ilike(f"%{f}%") |
                Cliente.telefone.ilike(f"%{f}%") |
                Cliente.cidade.ilike(f"%{f}%")
            )
        for c in q.order_by(Cliente.nome):
            lim = f"R$ {c.limite_credito:.2f}" if c.limite_credito else "R$ 0,00"
            self.tv.insert("", "end", iid=str(c.id),
                           values=(c.id, c.nome, c.apelido or "", c.cpf_cnpj or "",
                                   c.telefone or "", c.celular or "",
                                   c.cidade or "", c.estado or "", lim))

    def _sel(self):
        s = self.tv.selection()
        if not s:
            messagebox.showwarning("Atenção", "Selecione um cliente na lista.")
            return None
        return db_session.query(Cliente).get(int(s[0]))

    def _novo(self):
        ModalCliente(self, on_salvar=self._load)

    def _extrato(self):
        cli = self._sel()
        if not cli:
            return
        from telas.contas_receber import ModalExtratoCliente
        ModalExtratoCliente(self, cli)

    def _visualizar(self):
        c = self._sel()
        if c:
            ModalVisualizarCliente(self, cliente=c, on_editar=lambda cli: ModalCliente(self, cliente=cli, on_salvar=self._load))

    def _editar(self):
        c = self._sel()
        if c:
            ModalCliente(self, cliente=c, on_salvar=self._load)

    def _excluir(self):
        c = self._sel()
        if not c:
            return
        if not messagebox.askyesno("Confirmar Exclusão", f"Deseja realmente inativar o cliente '{c.nome}'?"):
            return
        c.ativo = False
        try:
            db_session.commit()
            self._load(self.busca.get())
        except Exception as ex:
            db_session.rollback()
            messagebox.showerror("Erro", str(ex))
