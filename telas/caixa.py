"""
Tela de Fluxo e Movimentação de Caixa Diário (Abertura, Sangria, Suprimento e Fechamento com Resumo por Forma de Pagamento).
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
from core.database import db_session, MovimentoCaixa, Venda
from datetime import datetime, date

COR = "#0288d1"
VM  = "#d32f2f"
VD  = "#2e7d32"


class ModalMovimento(ctk.CTkToplevel):
    def __init__(self, master, tipo="SANGRIA", usuario=None, on_sucesso=None):
        super().__init__(master)
        self.tipo = tipo
        self.usuario = usuario
        self.on_sucesso = on_sucesso

        titulos = {
            "ABERTURA": "🟢 Abertura de Caixa (Troco Inicial)",
            "SUPRIMENTO": "➕ Suprimento de Caixa (Entrada de Dinheiro)",
            "SANGRIA": "➖ Sangria de Caixa (Retirada de Dinheiro)"
        }

        self.title(titulos.get(tipo, "Movimentação de Caixa"))
        self.geometry("420x340")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"420x340+{(sw-420)//2}+{(sh-340)//2}")

        self._build(titulos.get(tipo, "Movimento"))

    def _build(self, titulo):
        self.grid_columnconfigure(0, weight=1)

        cor_h = VD if self.tipo in ["ABERTURA", "SUPRIMENTO"] else VM
        h = ctk.CTkFrame(self, fg_color=cor_h, height=45, corner_radius=0)
        h.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(h, text=titulo, font=("Segoe UI", 13, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)
        f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(f, text="Valor (R$):", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.ent_valor = ctk.CTkEntry(f, height=36, font=("Segoe UI", 13))
        self.ent_valor.pack(fill="x", pady=(0, 12))
        self.ent_valor.focus()

        ctk.CTkLabel(f, text="Motivo / Descrição:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.ent_desc = ctk.CTkEntry(f, height=36, placeholder_text="Ex: Troco inicial, Pagamento de despesa, etc.")
        self.ent_desc.pack(fill="x", pady=(0, 16))

        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
        ctk.CTkButton(bot, text="Confirmar Lançamento", font=("Segoe UI", 12, "bold"), fg_color=cor_h,
                      height=40, command=self._confirmar).pack(side="right", padx=4)
        ctk.CTkButton(bot, text="Cancelar", fg_color="gray40", height=40, command=self.destroy).pack(side="right", padx=4)

    def _confirmar(self):
        try:
            val = float(self.ent_valor.get().replace(",", "."))
            if val <= 0: raise ValueError
        except:
            messagebox.showerror("Aviso", "Informe um valor numérico válido!", parent=self)
            return

        desc = self.ent_desc.get().strip() or self.tipo.capitalize()
        mov = MovimentoCaixa(
            data_hora=datetime.now(),
            tipo=self.tipo,
            valor=val,
            descricao=desc,
            usuario_id=self.usuario.id if self.usuario else None
        )
        try:
            db_session.add(mov)
            db_session.commit()
            if self.on_sucesso:
                self.on_sucesso()
            self.destroy()
        except Exception as ex:
            db_session.rollback()
            messagebox.showerror("Erro", str(ex), parent=self)


class TelaCaixa(ctk.CTkFrame):
    def __init__(self, master, usuario=None, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.usuario = usuario
        self._ui()
        self._load()

    def _ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        h = ctk.CTkFrame(self, fg_color=COR, corner_radius=8)
        h.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        ctk.CTkLabel(h, text="💵  Fluxo e Movimento de Caixa Diário", font=("Segoe UI", 16, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        ctk.CTkButton(h, text="➖ Sangria (Retirada)", width=140, height=34, font=("Segoe UI", 11, "bold"),
                      fg_color=VM, hover_color="#b71c1c", command=lambda: self._abrir_modal("SANGRIA")).pack(side="right", padx=6, pady=8)
        ctk.CTkButton(h, text="➕ Suprimento (Entrada)", width=150, height=34, font=("Segoe UI", 11, "bold"),
                      fg_color=VD, hover_color="#1b5e20", command=lambda: self._abrir_modal("SUPRIMENTO")).pack(side="right", padx=6, pady=8)
        ctk.CTkButton(h, text="🟢 Abertura de Caixa", width=140, height=34, font=("Segoe UI", 11, "bold"),
                      fg_color="#00695c", hover_color="#004d40", command=lambda: self._abrir_modal("ABERTURA")).pack(side="right", padx=6, pady=8)

        # Cards de Resumo do Dia
        card_f = ctk.CTkFrame(self, fg_color="transparent")
        card_f.grid(row=1, column=0, sticky="ew", padx=16, pady=6)
        card_f.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.cards = {}
        itens_cards = [
            ("Saldo Atual em Gaveta", "#00897b", "saldo"),
            ("Total Vendas Hoje",     "#1a73e8", "vendas"),
            ("Entradas / Suprimentos","#2e7d32", "entradas"),
            ("Retiradas / Sangrias",  "#d32f2f", "saidas"),
        ]
        for col, (titulo, cor, k) in enumerate(itens_cards):
            c = ctk.CTkFrame(card_f, fg_color=cor, corner_radius=8)
            c.grid(row=0, column=col, padx=(0 if col==0 else 6, 0 if col==3 else 6), sticky="ew")
            ctk.CTkLabel(c, text=titulo, font=("Segoe UI", 11), text_color="white").pack(padx=12, pady=(10, 2))
            lbl = ctk.CTkLabel(c, text="R$ 0,00", font=("Segoe UI", 20, "bold"), text_color="white")
            lbl.pack(padx=12, pady=(0, 10))
            self.cards[k] = lbl

        # Tabela de Movimentações
        t_frame = ctk.CTkFrame(self, corner_radius=8)
        t_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(6, 16))
        t_frame.grid_columnconfigure(0, weight=1)
        t_frame.grid_rowconfigure(0, weight=1)

        cols = ("Hora", "Tipo", "Valor", "Descrição", "Operador")
        self.tv = ttk.Treeview(t_frame, columns=cols, show="headings", selectmode="browse", style="SAC.Treeview")
        for col in cols: self.tv.heading(col, text=col)

        self.tv.column("Hora",      width=100, anchor="center")
        self.tv.column("Tipo",      width=130, anchor="center")
        self.tv.column("Valor",     width=110, anchor="e")
        self.tv.column("Descrição", width=340)
        self.tv.column("Operador",  width=140, anchor="center")

        self.tv.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        sb = ttk.Scrollbar(t_frame, orient="vertical", command=self.tv.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=10)
        self.tv.configure(yscrollcommand=sb.set)

    def _abrir_modal(self, tipo):
        ModalMovimento(self, tipo=tipo, usuario=self.usuario, on_sucesso=self._load)

    def _load(self):
        for r in self.tv.get_children():
            self.tv.delete(r)

        hoje = date.today()
        movs = db_session.query(MovimentoCaixa).filter(
            MovimentoCaixa.data_hora >= datetime(hoje.year, hoje.month, hoje.day, 0, 0, 0)
        ).order_by(MovimentoCaixa.data_hora.desc()).all()

        vendas_hoje = db_session.query(Venda).filter(
            Venda.status == "CONCLUIDA",
            Venda.data >= datetime(hoje.year, hoje.month, hoje.day, 0, 0, 0)
        ).all()

        tot_vendas = sum(v.total for v in vendas_hoje)
        vendas_dinheiro = sum(v.total for v in vendas_hoje if v.forma_pgto == "DINHEIRO")
        tot_entradas = sum(m.valor for m in movs if m.tipo in ["ABERTURA", "SUPRIMENTO"])
        tot_saidas   = sum(m.valor for m in movs if m.tipo == "SANGRIA")

        saldo_gaveta = (tot_entradas + vendas_dinheiro) - tot_saidas

        self.cards["saldo"].configure(text=f"R$ {saldo_gaveta:.2f}")
        self.cards["vendas"].configure(text=f"R$ {tot_vendas:.2f}")
        self.cards["entradas"].configure(text=f"R$ {tot_entradas:.2f}")
        self.cards["saidas"].configure(text=f"R$ {tot_saidas:.2f}")

        for m in movs:
            op = m.usuario.nome if m.usuario else "Sistema"
            self.tv.insert("", "end", values=(
                m.data_hora.strftime("%H:%M:%S"),
                m.tipo,
                f"R$ {m.valor:.2f}",
                m.descricao or "",
                op
            ))
