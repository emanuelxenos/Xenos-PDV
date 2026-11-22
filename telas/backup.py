"""
Tela Única de Central de Backup e Restauração de Dados (Xenos PDV).
Tudo integrado na mesma tela: Gerar Agora, Importar Backup, Configuração de Intervalo e Histórico de Arquivos.
"""
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import os
from datetime import datetime
from core.backup import (
    carregar_config_backup, salvar_config_backup,
    executar_backup_silencioso, restaurar_backup, PASTA_BACKUPS_PADRAO
)
from telas.widgets import estilo_tree

COR = "#37474f"
AZUL = "#1565c0"
VD   = "#2e7d32"


class TelaBackup(ctk.CTkFrame):
    def __init__(self, master, on_atualizado=None, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.on_atualizado = on_atualizado
        self.cfg = carregar_config_backup()
        self._ui()
        self._listar_backups_disco()

    def _ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        estilo_tree()

        # ─── HEADER ───
        h = ctk.CTkFrame(self, fg_color=COR, corner_radius=8)
        h.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        ctk.CTkLabel(h, text="💾  Central de Backup e Restauração de Dados",
                     font=("Segoe UI", 16, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        # Botões Principais de Ação Direta no Topo
        ctk.CTkButton(h, text="📥 Importar / Restaurar Backup (.zip)", width=230, height=34, font=("Segoe UI", 11, "bold"),
                      fg_color=AZUL, hover_color="#0d47a1", command=self._restaurar).pack(side="right", padx=10, pady=8)
        ctk.CTkButton(h, text="⚡ Gerar Backup Agora", width=180, height=34, font=("Segoe UI", 11, "bold"),
                      fg_color=VD, hover_color="#1b5e20", command=self._fazer_backup_agora).pack(side="right", padx=4, pady=8)

        # ─── PAINEL CENTRAL DE CONFIGURAÇÃO (EM LINHA LIMPA) ───
        cfg_bar = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        cfg_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        cfg_bar.grid_columnconfigure(4, weight=1)

        # 1. Switch Ativo
        self.switch_ativo = ctk.CTkSwitch(cfg_bar, text="Backup Automático:", font=("Segoe UI", 11, "bold"))
        if self.cfg.get("ativo", True): self.switch_ativo.select()
        else: self.switch_ativo.deselect()
        self.switch_ativo.grid(row=0, column=0, padx=(14, 8), pady=12)

        # 2. Combo de Horas
        ctk.CTkLabel(cfg_bar, text="Intervalo:", font=("Segoe UI", 11)).grid(row=0, column=1, padx=(4, 4), pady=12)
        opcoes = ["1 hora", "2 horas", "4 horas", "6 horas", "8 horas", "12 horas", "24 horas (Diário)"]
        self.combo_horas = ctk.CTkComboBox(cfg_bar, values=opcoes, width=130, height=30, font=("Segoe UI", 10))
        
        mapa_rotulos = {1: "1 hora", 2: "2 horas", 4: "4 horas", 6: "6 horas", 8: "8 horas", 12: "12 horas", 24: "24 horas (Diário)"}
        self.combo_horas.set(mapa_rotulos.get(self.cfg.get("intervalo_horas", 2), "2 horas"))
        self.combo_horas.grid(row=0, column=2, padx=(0, 12), pady=12)

        # 3. Pasta de Destino
        ctk.CTkLabel(cfg_bar, text="Pasta Destino:", font=("Segoe UI", 11)).grid(row=0, column=3, padx=(4, 4), pady=12)
        self.ent_pasta = ctk.CTkEntry(cfg_bar, height=30, font=("Segoe UI", 10))
        self.ent_pasta.insert(0, self.cfg.get("pasta_destino", PASTA_BACKUPS_PADRAO))
        self.ent_pasta.grid(row=0, column=4, sticky="ew", padx=(0, 6), pady=12)

        ctk.CTkButton(cfg_bar, text="Alterar Pasta...", width=110, height=30, command=self._escolher_pasta).grid(row=0, column=5, padx=(0, 8), pady=12)
        ctk.CTkButton(cfg_bar, text="💾 Salvar Config", width=120, height=30, fg_color=VD, command=self._salvar_config).grid(row=0, column=6, padx=(0, 14), pady=12)

        # ─── HISTÓRICO DE BACKUPS EXISTENTES EM DISCO ───
        t_frame = ctk.CTkFrame(self, corner_radius=8)
        t_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(6, 16))
        t_frame.grid_columnconfigure(0, weight=1)
        t_frame.grid_rowconfigure(1, weight=1)

        # Cabeçalho da tabela
        sub_h = ctk.CTkFrame(t_frame, fg_color="transparent")
        sub_h.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(10, 4))
        ctk.CTkLabel(sub_h, text="📁 Arquivos de Backup Encontrados na Pasta", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.lbl_status = ctk.CTkLabel(sub_h, text=f"Último backup: {self.cfg.get('ultimo_backup', 'Nunca')}", font=("Segoe UI", 10), text_color="gray40")
        self.lbl_status.pack(side="right")

        cols = ("Nome do Arquivo", "Data e Hora da Cópia", "Tamanho (KB)", "Caminho Completo")
        self.tv = ttk.Treeview(t_frame, columns=cols, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols: self.tv.heading(c, text=c)

        self.tv.column("Nome do Arquivo",        width=250)
        self.tv.column("Data e Hora da Cópia",   width=150, anchor="center")
        self.tv.column("Tamanho (KB)",           width=100, anchor="e")
        self.tv.column("Caminho Completo",       width=380)

        self.tv.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        sb = ttk.Scrollbar(t_frame, orient="vertical", command=self.tv.yview)
        sb.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        self.tv.configure(yscrollcommand=sb.set)

    def _listar_backups_disco(self):
        for r in self.tv.get_children():
            self.tv.delete(r)

        pasta = self.cfg.get("pasta_destino", PASTA_BACKUPS_PADRAO)
        if not os.path.exists(pasta):
            return

        arquivos = [f for f in os.listdir(pasta) if f.endswith(".zip")]
        arquivos_com_data = []

        for a in arquivos:
            p = os.path.join(pasta, a)
            try:
                mtime = os.path.getmtime(p)
                tam_kb = os.path.getsize(p) / 1024
                dt_str = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M:%S")
                arquivos_com_data.append((a, dt_str, f"{tam_kb:.1f} KB", p, mtime))
            except Exception:
                pass

        arquivos_com_data.sort(key=lambda x: x[4], reverse=True)

        for a, dt, tam, p, _ in arquivos_com_data:
            self.tv.insert("", "end", values=(a, dt, tam, p))

    def _escolher_pasta(self):
        p = filedialog.askdirectory(parent=self, title="Selecione a Pasta para Salvar os Backups")
        if p:
            self.ent_pasta.delete(0, "end")
            self.ent_pasta.insert(0, p)

    def _salvar_config(self):
        pasta = self.ent_pasta.get().strip()
        if not pasta:
            messagebox.showwarning("Aviso", "A pasta de destino não pode ficar vazia!", parent=self)
            return

        mapa_horas = {"1 hora": 1, "2 horas": 2, "4 horas": 4, "6 horas": 6, "8 horas": 8, "12 horas": 12, "24 horas (Diário)": 24}
        horas = mapa_horas.get(self.combo_horas.get(), 2)

        self.cfg["ativo"] = bool(self.switch_ativo.get())
        self.cfg["intervalo_horas"] = horas
        self.cfg["pasta_destino"] = pasta

        salvar_config_backup(self.cfg)
        messagebox.showinfo("Salvo", f"Configurações atualizadas!\nBackup automático configurado para cada {horas} hora(s).", parent=self)
        self._listar_backups_disco()

    def _fazer_backup_agora(self):
        pasta = self.ent_pasta.get().strip()
        caminho = executar_backup_silencioso(pasta_destino=pasta if pasta else None)
        if caminho:
            self.cfg = carregar_config_backup()
            self.lbl_status.configure(text=f"Último backup: {self.cfg.get('ultimo_backup', '')}")
            self._listar_backups_disco()
            messagebox.showinfo("Sucesso", f"Backup gerado com sucesso em:\n{caminho}", parent=self)
        else:
            messagebox.showerror("Erro", "Falha ao gerar cópia de segurança!", parent=self)

    def _restaurar(self):
        sucesso = restaurar_backup(parent_window=self, on_sucesso=self._listar_backups_disco)
        if sucesso:
            if self.on_atualizado:
                self.on_atualizado()
