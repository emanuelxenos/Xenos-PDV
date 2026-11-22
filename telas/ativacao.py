"""
Tela Modal de Ativação / Bloqueio por Licença Expirada.
"""
import customtkinter as ctk
from tkinter import messagebox
from core.licenca import salvar_chave_ativacao, verificar_licenca

COR_BLOQUEIO = "#b71c1c"
VERDE        = "#2e7d32"


class ModalAtivacao(ctk.CTkToplevel):
    def __init__(self, master, motivo="", on_ativado=None, bloqueio_total=False):
        super().__init__(master)
        self.motivo = motivo
        self.on_ativado = on_ativado
        self.bloqueio_total = bloqueio_total

        self.title("Licença & Ativação — Xenos PDV")
        self.geometry("480x440")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"480x440+{(sw-480)//2}+{(sh-440)//2}")

        if bloqueio_total:
            # Não deixa fechar pelo 'X' da janela se o sistema estiver bloqueado
            self.protocol("WM_DELETE_WINDOW", self._fechar_bloqueado)

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        cor_topo = COR_BLOQUEIO if self.bloqueio_total else "#1565c0"
        h = ctk.CTkFrame(self, fg_color=cor_topo, height=50, corner_radius=0)
        h.grid(row=0, column=0, sticky="ew")
        titulo = "🔒 SISTEMA BLOQUEADO / EXPIRADO" if self.bloqueio_total else "🔑 Ativação / Renovação de Licença"
        ctk.CTkLabel(h, text=titulo, font=("Segoe UI", 13, "bold"), text_color="white").pack(side="left", padx=16, pady=12)

        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)

        if self.motivo:
            aviso = ctk.CTkFrame(f, fg_color="#ffebee" if self.bloqueio_total else "#e3f2fd", corner_radius=6)
            aviso.pack(fill="x", pady=(0, 12))
            cor_txt = "#c62828" if self.bloqueio_total else "#1565c0"
            ctk.CTkLabel(aviso, text=self.motivo, font=("Segoe UI", 11, "bold"), text_color=cor_txt, wraplength=420).pack(padx=12, pady=10)

        ctk.CTkLabel(f, text="Cole aqui sua Chave de Ativação / Renovação:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 4))
        self.txt_chave = ctk.CTkTextbox(f, height=110, font=("Consolas", 10))
        self.txt_chave.pack(fill="x", pady=(0, 12))
        self.txt_chave.focus()

        ctk.CTkLabel(f, text="💬 Dúvidas ou renovação de mensalidade?\nEntre em contato com o suporte técnico para liberar seu código.",
                     font=("Segoe UI", 10), text_color="gray40", justify="center").pack(pady=(0, 14))

        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))

        ctk.CTkButton(bot, text="ATIVAR / LIBERAR", font=("Segoe UI", 12, "bold"), fg_color=VERDE,
                      height=42, command=self._ativar).pack(side="right", padx=4)

        if not self.bloqueio_total:
            ctk.CTkButton(bot, text="Cancelar", fg_color="gray40", height=42, command=self.destroy).pack(side="right", padx=4)

    def _ativar(self):
        chave = self.txt_chave.get("1.0", "end").strip()
        if not chave:
            messagebox.showwarning("Aviso", "Por favor, cole a chave de ativação!", parent=self)
            return

        if salvar_chave_ativacao(chave):
            st, dias, msg, data_fim = verificar_licenca()
            if st in ["VALIDO", "EXPIRANDO"]:
                messagebox.showinfo("Sucesso", f"Sistema liberado com sucesso até {data_fim}!", parent=self)
                if self.on_ativado:
                    self.on_ativado()
                self.destroy()
            else:
                messagebox.showerror("Chave Inválida", msg, parent=self)
        else:
            messagebox.showerror("Erro de Ativação", "Chave de ativação inválida ou incorreta!", parent=self)

    def _fechar_bloqueado(self):
        # Se fechar sem ativar, encerra o programa
        import sys
        sys.exit(0)
