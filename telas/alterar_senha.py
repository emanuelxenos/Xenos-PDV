"""
Tela Modal para Alteração de Senha do Usuário Logado.
"""
import customtkinter as ctk
from tkinter import messagebox
from core.database import db_session, Usuario
from core.auth import _hash

COR = "#37474f"
VD  = "#2e7d32"


class ModalAlterarSenha(ctk.CTkToplevel):
    def __init__(self, master, usuario):
        super().__init__(master)
        self.usuario = usuario

        self.title("Alterar Senha de Acesso")
        self.geometry("400x380")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"400x380+{(sw-400)//2}+{(sh-380)//2}")

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        h = ctk.CTkFrame(self, fg_color=COR, height=45, corner_radius=0)
        h.grid(row=0, column=0, sticky="ew")
        u_nome = self.usuario.nome if self.usuario else "Usuário"
        ctk.CTkLabel(h, text=f"🔒 Alterar Senha — {u_nome}", font=("Segoe UI", 13, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=1, column=0, sticky="nsew", padx=24, pady=16)

        ctk.CTkLabel(f, text="Senha Atual:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.ent_atual = ctk.CTkEntry(f, height=36, show="●")
        self.ent_atual.pack(fill="x", pady=(0, 10))
        self.ent_atual.focus()

        ctk.CTkLabel(f, text="Nova Senha:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.ent_nova = ctk.CTkEntry(f, height=36, show="●")
        self.ent_nova.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(f, text="Confirmar Nova Senha:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.ent_conf = ctk.CTkEntry(f, height=36, show="●")
        self.ent_conf.pack(fill="x", pady=(0, 14))
        self.ent_conf.bind("<Return>", lambda e: self._salvar())

        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 16))

        ctk.CTkButton(bot, text="Salvar Nova Senha", font=("Segoe UI", 12, "bold"), fg_color=VD,
                      height=40, command=self._salvar).pack(side="right", padx=4)
        ctk.CTkButton(bot, text="Cancelar", fg_color="gray40", height=40, command=self.destroy).pack(side="right", padx=4)

    def _salvar(self):
        atual = self.ent_atual.get().strip()
        nova = self.ent_nova.get().strip()
        conf = self.ent_conf.get().strip()

        if not atual or not nova:
            messagebox.showwarning("Aviso", "Preencha a senha atual e a nova senha!", parent=self)
            return

        # Verifica senha atual no banco
        u = db_session.query(Usuario).get(self.usuario.id)
        if not u or u.senha_hash != _hash(atual):
            messagebox.showerror("Erro", "A senha atual informada está incorreta!", parent=self)
            self.ent_atual.delete(0, "end")
            self.ent_atual.focus()
            return

        if len(nova) < 3:
            messagebox.showwarning("Aviso", "A nova senha deve ter pelo menos 3 caracteres!", parent=self)
            return

        if nova != conf:
            messagebox.showerror("Erro", "A confirmação da nova senha não confere!", parent=self)
            self.ent_conf.delete(0, "end")
            self.ent_conf.focus()
            return

        # Atualiza a senha
        u.senha_hash = _hash(nova)
        try:
            db_session.commit()
            self.usuario.senha_hash = u.senha_hash
            messagebox.showinfo("Sucesso", "Sua senha foi alterada com sucesso!", parent=self)
            self.destroy()
        except Exception as ex:
            db_session.rollback()
            messagebox.showerror("Erro ao Salvar", str(ex), parent=self)
