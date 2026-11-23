"""
Tela de Gestão de Usuários / Operadores e Controle de Acesso (Xenos PDV).
Permite cadastrar novos operadores, gerentes, alterar login, senha e perfil do admin.
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from core.database import db_session, Usuario
from core.auth import _hash
from telas.widgets import estilo_tree

COR = "#37474f"
VD  = "#2e7d32"
VM  = "#c62828"


class ModalUsuario(ctk.CTkToplevel):
    def __init__(self, master, usuario=None, on_salvar=None):
        super().__init__(master)
        self.usuario = usuario
        self.on_salvar = on_salvar

        titulo = "✏️ Editar Usuário" if usuario else "👤 Novo Usuário"
        self.title(titulo)
        self.geometry("450x420")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"450x420+{(sw-450)//2}+{(sh-420)//2}")

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        h = ctk.CTkFrame(self, fg_color=COR, height=45, corner_radius=0)
        h.grid(row=0, column=0, sticky="ew")
        u_txt = "✏️ EDITAR USUÁRIO" if self.usuario else "👤 CADASTRAR NOVO USUÁRIO"
        ctk.CTkLabel(h, text=u_txt, font=("Segoe UI", 12, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=1, column=0, sticky="nsew", padx=24, pady=14)
        f.grid_columnconfigure(0, weight=1)

        # Nome Completo
        ctk.CTkLabel(f, text="Nome Completo:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.ent_nome = ctk.CTkEntry(f, height=34, placeholder_text="Ex: Maria Clara / Operador Caixa 1")
        self.ent_nome.pack(fill="x", pady=(0, 10))

        # Login de Acesso
        ctk.CTkLabel(f, text="Nome de Usuário (Login):", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.ent_login = ctk.CTkEntry(f, height=34, placeholder_text="Ex: maria / caixa1")
        self.ent_login.pack(fill="x", pady=(0, 10))

        # Perfil / Nível
        ctk.CTkLabel(f, text="Nível de Acesso (Perfil):", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.combo_perfil = ctk.CTkComboBox(f, values=["ADMINISTRADOR", "OPERADOR", "GERENTE"], height=34)
        self.combo_perfil.set("OPERADOR")
        self.combo_perfil.pack(fill="x", pady=(0, 10))

        # Senha
        lbl_senha_txt = "Nova Senha (deixe em branco para manter a atual):" if self.usuario else "Senha de Acesso:"
        ctk.CTkLabel(f, text=lbl_senha_txt, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.ent_senha = ctk.CTkEntry(f, height=34, show="•", placeholder_text="Digite a senha")
        self.ent_senha.pack(fill="x", pady=(0, 14))

        # Preenchimento se for edição
        if self.usuario:
            self.ent_nome.insert(0, self.usuario.nome or "")
            self.ent_login.insert(0, self.usuario.login or "")
            perfil_upper = (self.usuario.perfil or "OPERADOR").upper()
            if perfil_upper in ["ADMIN", "ADMINISTRADOR"]:
                self.combo_perfil.set("ADMINISTRADOR")
            elif perfil_upper == "GERENTE":
                self.combo_perfil.set("GERENTE")
            else:
                self.combo_perfil.set("OPERADOR")

        # Botões
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 14))
        ctk.CTkButton(bot, text="Salvar", font=("Segoe UI", 12, "bold"), fg_color=VD,
                      hover_color="#1b5e20", height=38, command=self._salvar).pack(side="right", padx=4)
        ctk.CTkButton(bot, text="Cancelar", fg_color="gray40", height=38,
                      command=self.destroy).pack(side="right", padx=4)

    def _salvar(self):
        nome = self.ent_nome.get().strip()
        login_val = self.ent_login.get().strip().lower()
        perfil_val = "admin" if "ADMIN" in self.combo_perfil.get().upper() else self.combo_perfil.get().lower()
        senha = self.ent_senha.get().strip()

        if not nome or not login_val:
            messagebox.showerror("Erro", "Nome e Login são obrigatórios!", parent=self)
            return

        if not self.usuario and not senha:
            messagebox.showerror("Erro", "Informe uma senha para o novo usuário!", parent=self)
            return

        # Verifica duplicidade de login
        existente = db_session.query(Usuario).filter(Usuario.login == login_val).first()
        if existente and (not self.usuario or existente.id != self.usuario.id):
            messagebox.showerror("Erro", f"O login '{login_val}' já está em uso por outro usuário!", parent=self)
            return

        try:
            if self.usuario:
                u = db_session.query(Usuario).get(self.usuario.id)
                u.nome = nome
                u.login = login_val
                u.perfil = perfil_val
                if senha:
                    u.senha_hash = _hash(senha)
            else:
                novo_u = Usuario(
                    nome=nome,
                    login=login_val,
                    senha_hash=_hash(senha),
                    perfil=perfil_val,
                    ativo=True
                )
                db_session.add(novo_u)

            db_session.commit()
            messagebox.showinfo("Sucesso", "Usuário salvo com sucesso!", parent=self)
            if self.on_salvar:
                self.on_salvar()
            self.destroy()
        except Exception as ex:
            db_session.rollback()
            messagebox.showerror("Erro ao Salvar", str(ex), parent=self)


class TelaUsuarios(ctk.CTkFrame):
    def __init__(self, master, usuario_atual=None, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.usuario_atual = usuario_atual
        self._ui()
        self._load()

    def _ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        estilo_tree()

        # Header
        h = ctk.CTkFrame(self, fg_color=COR, corner_radius=8)
        h.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        ctk.CTkLabel(h, text="👥  Gestão de Usuários e Acessos ao Sistema",
                     font=("Segoe UI", 16, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        ctk.CTkButton(h, text="+ Novo Usuário", width=140, height=34, font=("Segoe UI", 12, "bold"),
                      fg_color="white", text_color=COR, hover_color="#cfd8dc",
                      command=self._novo).pack(side="right", padx=14, pady=8)

        # Barra de Ações e Filtro
        bar = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        bar.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        bar.grid_columnconfigure(0, weight=1)

        self.ent_busca = ctk.CTkEntry(bar, placeholder_text="🔍 Pesquisar por nome ou login...", height=34)
        self.ent_busca.grid(row=0, column=0, padx=12, pady=10, sticky="ew")
        self.ent_busca.bind("<KeyRelease>", lambda e: self._load())

        ctk.CTkButton(bar, text="✏️ Editar", width=90, height=32, font=("Segoe UI", 11, "bold"),
                      fg_color="#455a64", hover_color="#263238", command=self._editar).grid(row=0, column=1, padx=4, pady=10)

        ctk.CTkButton(bar, text="🗑️ Desativar", width=100, height=32, font=("Segoe UI", 11, "bold"),
                      fg_color=VM, hover_color="#b71c1c", command=self._inativar).grid(row=0, column=2, padx=(4, 12), pady=10)

        # Tabela
        t_frame = ctk.CTkFrame(self, corner_radius=8)
        t_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(6, 16))
        t_frame.grid_columnconfigure(0, weight=1)
        t_frame.grid_rowconfigure(0, weight=1)

        cols = ("ID", "Nome do Usuário", "Login de Acesso", "Perfil / Nível", "Situação", "Criado Em")
        self.tv = ttk.Treeview(t_frame, columns=cols, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols:
            self.tv.heading(c, text=c)

        self.tv.column("ID",              width=60,  anchor="center")
        self.tv.column("Nome do Usuário", width=220)
        self.tv.column("Login de Acesso", width=160)
        self.tv.column("Perfil / Nível",  width=140, anchor="center")
        self.tv.column("Situação",        width=100, anchor="center")
        self.tv.column("Criado Em",       width=140, anchor="center")

        self.tv.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        sb = ttk.Scrollbar(t_frame, orient="vertical", command=self.tv.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=10)
        self.tv.configure(yscrollcommand=sb.set)

        self.tv.bind("<Double-1>", lambda e: self._editar())

    def _load(self):
        for r in self.tv.get_children():
            self.tv.delete(r)

        busca = self.ent_busca.get().strip()
        q = db_session.query(Usuario).filter(Usuario.ativo == True)
        if busca:
            q = q.filter(
                (Usuario.nome.ilike(f"%{busca}%")) |
                (Usuario.login.ilike(f"%{busca}%"))
            )
        usuarios = q.order_by(Usuario.id).all()

        for u in usuarios:
            dt = u.criado_em.strftime("%d/%m/%Y %H:%M") if u.criado_em else "-"
            st = "ATIVO" if u.ativo else "INATIVO"
            perfil_nome = u.perfil.upper() if u.perfil else "OPERADOR"
            self.tv.insert("", "end", iid=str(u.id), values=(
                f"#{u.id:02d}",
                u.nome,
                u.login,
                perfil_nome,
                st,
                dt
            ))

    def _sel(self):
        s = self.tv.selection()
        if not s:
            messagebox.showwarning("Atenção", "Selecione um usuário na tabela.")
            return None
        return db_session.query(Usuario).get(int(s[0]))

    def _novo(self):
        ModalUsuario(self, on_salvar=self._load)

    def _editar(self):
        u = self._sel()
        if u:
            ModalUsuario(self, usuario=u, on_salvar=self._load)

    def _inativar(self):
        u = self._sel()
        if not u:
            return

        if self.usuario_atual and self.usuario_atual.id == u.id:
            messagebox.showwarning("Atenção", "Você não pode desativar o seu próprio usuário logado!", parent=self)
            return

        if u.login.lower() == "admin":
            # Se for o admin principal, checa se há outro admin
            outros_admins = db_session.query(Usuario).filter(
                Usuario.ativo == True,
                Usuario.id != u.id,
                Usuario.perfil.in_(["admin", "ADMIN", "ADMINISTRADOR"])
            ).count()
            if outros_admins == 0:
                messagebox.showerror("Ação Não Permitida", "O sistema deve ter pelo menos um usuário Administrador ativo!", parent=self)
                return

        if messagebox.askyesno("Confirmar", f"Deseja realmente desativar o usuário '{u.nome}' ({u.login})?"):
            u.ativo = False
            db_session.commit()
            self._load()
