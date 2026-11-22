"""
Tela Modal de Ativação / Bloqueio por Licença Expirada.
Com botão direto para abrir conversa no WhatsApp de Suporte.
"""
import customtkinter as ctk
import webbrowser
from tkinter import messagebox
from core.licenca import salvar_chave_ativacao, verificar_licenca

COR_BLOQUEIO = "#b71c1c"
VERDE        = "#2e7d32"
WHATSAPP_NUM = "5587999308939"


class ModalAtivacao(ctk.CTkToplevel):
    def __init__(self, master, motivo="", on_ativado=None, bloqueio_total=False):
        super().__init__(master)
        self.motivo = motivo
        self.on_ativado = on_ativado
        self.bloqueio_total = bloqueio_total

        self.title("Licença & Ativação — Xenos PDV")
        self.geometry("490x470")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"490x470+{(sw-490)//2}+{(sh-470)//2}")

        if bloqueio_total:
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
            aviso.pack(fill="x", pady=(0, 10))
            cor_txt = "#c62828" if self.bloqueio_total else "#1565c0"
            ctk.CTkLabel(aviso, text=self.motivo, font=("Segoe UI", 11, "bold"), text_color=cor_txt, wraplength=430).pack(padx=12, pady=8)

        ctk.CTkLabel(f, text="Cole aqui sua Chave de Ativação / Renovação:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 4))
        self.txt_chave = ctk.CTkTextbox(f, height=90, font=("Consolas", 10))
        self.txt_chave.pack(fill="x", pady=(0, 10))
        self.txt_chave.focus()

        # Botão do WhatsApp de Suporte
        btn_whats = ctk.CTkButton(
            f, text="💬 Falar no WhatsApp com o Suporte (Renovar)", font=("Segoe UI", 11, "bold"),
            fg_color="#25D366", hover_color="#128C7E", height=36,
            command=self._abrir_whatsapp
        )
        btn_whats.pack(fill="x", pady=(0, 14))

        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))

        ctk.CTkButton(bot, text="ATIVAR / LIBERAR", font=("Segoe UI", 12, "bold"), fg_color=VERDE,
                      height=42, command=self._ativar).pack(side="right", padx=4)

        if not self.bloqueio_total:
            ctk.CTkButton(bot, text="Cancelar", fg_color="gray40", height=42, command=self.destroy).pack(side="right", padx=4)

    def _abrir_whatsapp(self):
        msg = "Ola! Gostaria de renovar/ativar a licenca do meu Xenos PDV."
        link = f"https://wa.me/{WHATSAPP_NUM}?text={msg.replace(' ', '%20')}"
        webbrowser.open(link)

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
        import sys
        sys.exit(0)
