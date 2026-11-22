"""
Tela Modal de Configuração e Painel do Backup Automático.
Permite ativar/desativar, escolher intervalo de horas, selecionar pasta de destino,
forçar backup imediato e RESTAURAR / IMPORTAR BACKUP (.ZIP).
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from core.backup import carregar_config_backup, salvar_config_backup, executar_backup_silencioso, restaurar_backup

COR = "#37474f"
VD  = "#2e7d32"
AZUL = "#1565c0"


class ModalConfigBackup(ctk.CTkToplevel):
    def __init__(self, master, on_atualizado=None):
        super().__init__(master)
        self.on_atualizado = on_atualizado
        self.cfg = carregar_config_backup()

        self.title("Backup e Restauração de Dados — Xenos PDV")
        self.geometry("540x560")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"540x560+{(sw-540)//2}+{(sh-560)//2}")

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        h = ctk.CTkFrame(self, fg_color=COR, height=45, corner_radius=0)
        h.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(h, text="💾  Backup Automático & Importação de Dados",
                     font=("Segoe UI", 13, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        f = ctk.CTkScrollableFrame(self, fg_color="transparent")
        f.grid(row=1, column=0, sticky="nsew", padx=20, pady=12)
        f.grid_columnconfigure(0, weight=1)

        # ─── SEÇÃO 1: RESTAURAR / IMPORTAR BACKUP ───
        ctk.CTkLabel(f, text="📥 RESTAURAR / IMPORTAR DADOS DE BACKUP",
                     font=("Segoe UI", 11, "bold"), text_color=AZUL).pack(anchor="w", pady=(0, 2))

        box_restaurar = ctk.CTkFrame(f, fg_color="#e3f2fd", corner_radius=6)
        box_restaurar.pack(fill="x", pady=(0, 16))
        
        ctk.CTkLabel(box_restaurar, text="Selecione um arquivo .zip de backup salvo anteriormente para restaurar o banco de dados:",
                     font=("Segoe UI", 10), text_color="#0d47a1", wraplength=460, justify="left").pack(anchor="w", padx=12, pady=(10, 6))

        ctk.CTkButton(box_restaurar, text="📥 Selecionar Arquivo de Backup para Restaurar (.zip)",
                      fg_color=AZUL, hover_color="#0d47a1", height=36, font=("Segoe UI", 11, "bold"),
                      command=self._executar_restauracao).pack(fill="x", padx=12, pady=(0, 10))

        # Divisória
        ctk.CTkFrame(f, height=1, fg_color="gray75").pack(fill="x", pady=(0, 14))

        # ─── SEÇÃO 2: CONFIGURAÇÃO DO BACKUP AUTOMÁTICO ───
        ctk.CTkLabel(f, text="⚙️ CONFIGURAÇÃO DO BACKUP AUTOMÁTICO",
                     font=("Segoe UI", 11, "bold"), text_color="#37474f").pack(anchor="w", pady=(0, 6))

        self.check_ativo = ctk.CTkSwitch(f, text="Backup Automático Ativo em Segundo Plano", font=("Segoe UI", 11, "bold"))
        if self.cfg.get("ativo", True):
            self.check_ativo.select()
        else:
            self.check_ativo.deselect()
        self.check_ativo.pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(f, text="Fazer backup a cada quantas horas?", font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 2))
        opcoes_horas = ["1 hora", "2 horas", "4 horas", "6 horas", "8 horas", "12 horas", "24 horas (Diário)"]
        self.combo_horas = ctk.CTkComboBox(f, values=opcoes_horas, height=32, font=("Segoe UI", 11))
        
        hora_atual = self.cfg.get("intervalo_horas", 2)
        mapa_rotulos = {1: "1 hora", 2: "2 horas", 4: "4 horas", 6: "6 horas", 8: "8 horas", 12: "12 horas", 24: "24 horas (Diário)"}
        self.combo_horas.set(mapa_rotulos.get(hora_atual, "2 horas"))
        self.combo_horas.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(f, text="Pasta onde os backups automáticos serão salvos:", font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 2))
        
        pasta_box = ctk.CTkFrame(f, fg_color="transparent")
        pasta_box.pack(fill="x", pady=(0, 10))
        pasta_box.grid_columnconfigure(0, weight=1)

        self.ent_pasta = ctk.CTkEntry(pasta_box, height=32, font=("Segoe UI", 10))
        self.ent_pasta.insert(0, self.cfg.get("pasta_destino", ""))
        self.ent_pasta.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(pasta_box, text="Procurar...", width=90, height=32, command=self._escolher_pasta).grid(row=0, column=1)

        # Status do Último Backup
        info_box = ctk.CTkFrame(f, fg_color="#eceff1", corner_radius=6)
        info_box.pack(fill="x", pady=(0, 12))
        ult = self.cfg.get("ultimo_backup", "Nenhum backup realizado ainda.")
        ctk.CTkLabel(info_box, text=f"Último backup automático: {ult}", font=("Segoe UI", 10), text_color="#37474f").pack(padx=12, pady=6)

        ctk.CTkButton(f, text="⚡ Forçar Cópia de Backup Agora", fg_color="#00695c", hover_color="#004d40", height=32,
                      command=self._forcar_backup_agora).pack(fill="x", pady=(0, 10))

        # Rodapé
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 14))

        ctk.CTkButton(bot, text="Salvar Configurações", font=("Segoe UI", 12, "bold"), fg_color=VD,
                      height=38, command=self._salvar).pack(side="right", padx=4)
        ctk.CTkButton(bot, text="Fechar", fg_color="gray40", height=38, command=self.destroy).pack(side="right", padx=4)

    def _executar_restauracao(self):
        sucesso = restaurar_backup(parent_window=self, on_sucesso=self._pos_restauracao)
        if sucesso:
            self.destroy()

    def _pos_restauracao(self):
        messagebox.showinfo("Reinicialização Recomendada", "Os dados foram importados com sucesso!\nO sistema será atualizado.", parent=self)
        if self.on_atualizado:
            self.on_atualizado()

    def _escolher_pasta(self):
        p = filedialog.askdirectory(parent=self, title="Selecione a Pasta para Salvar os Backups")
        if p:
            self.ent_pasta.delete(0, "end")
            self.ent_pasta.insert(0, p)

    def _forcar_backup_agora(self):
        pasta = self.ent_pasta.get().strip()
        caminho = executar_backup_silencioso(pasta_destino=pasta if pasta else None)
        if caminho:
            messagebox.showinfo("Sucesso", f"Backup gerado com sucesso em:\n{caminho}", parent=self)
            self.cfg = carregar_config_backup()
            self.destroy()
        else:
            messagebox.showerror("Erro", "Falha ao gerar cópia de segurança!", parent=self)

    def _salvar(self):
        pasta = self.ent_pasta.get().strip()
        if not pasta:
            messagebox.showwarning("Aviso", "Por favor, defina a pasta de destino!", parent=self)
            return

        mapa_horas = {"1 hora": 1, "2 horas": 2, "4 horas": 4, "6 horas": 6, "8 horas": 8, "12 horas": 12, "24 horas (Diário)": 24}
        horas_escolhidas = mapa_horas.get(self.combo_horas.get(), 2)

        self.cfg["ativo"] = bool(self.check_ativo.get())
        self.cfg["intervalo_horas"] = horas_escolhidas
        self.cfg["pasta_destino"] = pasta

        salvar_config_backup(self.cfg)
        messagebox.showinfo("Salvo", f"Configurações atualizadas!\nO sistema fará cópia automática a cada {horas_escolhidas} hora(s).", parent=self)
        if self.on_atualizado:
            self.on_atualizado()
        self.destroy()
