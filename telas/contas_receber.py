"""
Módulo de Contas a Receber / Fiado dos Clientes.
Permite visualizar dívidas, histórico de compras a prazo e realizar baixas/pagamentos totais ou parciais.
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
from core.database import db_session, ContaReceber, Cliente, MovimentoCaixa, HistoricoPagamentoConta, Venda
from datetime import datetime

COR = "#c2185b"
VD  = "#2e7d32"


class ModalBaixaConta(ctk.CTkToplevel):
    def __init__(self, master, conta, usuario=None, on_sucesso=None):
        super().__init__(master)
        self.conta = conta
        self.usuario = usuario
        self.on_sucesso = on_sucesso

        self.title("Receber Pagamento de Conta")
        self.geometry("450x460")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"450x460+{(sw-450)//2}+{(sh-460)//2}")

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        h = ctk.CTkFrame(self, fg_color=COR, height=45, corner_radius=0)
        h.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(h, text=f"💰 Recebimento de Conta — ID #{self.conta.id}",
                     font=("Segoe UI", 13, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)

        cli_nome = self.conta.cliente.nome if self.conta.cliente else "Desconhecido"
        ctk.CTkLabel(f, text=f"Cliente: {cli_nome}", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(f, text=f"Venda Origem: #{self.conta.venda.numero:06d}" if self.conta.venda else "Lançamento Avulso",
                     font=("Segoe UI", 11), text_color="gray40").pack(anchor="w", pady=(0, 10))

        # Quadro do saldo
        saldo_card = ctk.CTkFrame(f, fg_color="#fce4ec", corner_radius=6)
        saldo_card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(saldo_card, text="Saldo Devedor Atual", font=("Segoe UI", 10), text_color="#880e4f").pack(pady=(8, 2))
        ctk.CTkLabel(saldo_card, text=f"R$ {self.conta.saldo_devedor:.2f}", font=("Segoe UI", 22, "bold"), text_color="#ad1457").pack(pady=(0, 8))

        ctk.CTkLabel(f, text="Valor do Pagamento / Acerto (R$):", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.ent_valor = ctk.CTkEntry(f, height=36, font=("Segoe UI", 13, "bold"))
        self.ent_valor.insert(0, f"{self.conta.saldo_devedor:.2f}".replace(".", ","))
        self.ent_valor.pack(fill="x", pady=(0, 10))
        self.ent_valor.bind("<Return>", lambda e: self._confirmar())
        self.ent_valor.focus()

        ctk.CTkLabel(f, text="Forma de Entrada no Caixa:", font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 2))
        self.combo_forma = ctk.CTkComboBox(f, values=["DINHEIRO", "PIX", "CARTAO DEBITO", "CARTAO CREDITO"], height=34)
        self.combo_forma.set("DINHEIRO")
        self.combo_forma.pack(fill="x", pady=(0, 14))

        self.check_comprovante = ctk.CTkCheckBox(f, text="Imprimir Comprovante de Pagamento / Abate",
                                                 font=("Segoe UI", 11, "bold"), text_color="#ad1457")
        self.check_comprovante.select()
        self.check_comprovante.pack(anchor="w", pady=(0, 10))

        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
        ctk.CTkButton(bot, text="Confirmar Recebimento", font=("Segoe UI", 12, "bold"), fg_color=VD,
                      height=40, command=self._confirmar).pack(side="right", padx=4)
        ctk.CTkButton(bot, text="Cancelar", fg_color="gray40", height=40, command=self.destroy).pack(side="right", padx=4)

    def _confirmar(self):
        txt = self.ent_valor.get().strip().replace("R$", "").replace("r$", "").replace(" ", "")
        try:
            val = float(txt.replace(",", "."))
            if val <= 0: raise ValueError
        except:
            messagebox.showerror("Aviso", "Informe um valor de pagamento válido!", parent=self)
            return

        # Tolerância de 1 centavo para arredondamentos de ponto flutuante
        if val > (self.conta.saldo_devedor + 0.01):
            messagebox.showerror("Aviso", f"O valor informado (R$ {val:.2f}) é maior que a dívida restante (R$ {self.conta.saldo_devedor:.2f})!", parent=self)
            return

        # Se for praticamente igual ao saldo devedor, quita o saldo exato
        if abs(val - self.conta.saldo_devedor) <= 0.01:
            val = self.conta.saldo_devedor

        saldo_anterior = self.conta.saldo_devedor
        self.conta.valor_pago = (self.conta.valor_pago or 0.0) + val
        self.conta.saldo_devedor = max(0.0, self.conta.saldo_devedor - val)

        if self.conta.saldo_devedor <= 0.001:
            self.conta.saldo_devedor = 0.0
            self.conta.status = "PAGO"
        else:
            self.conta.status = "PARCIAL"

        forma = self.combo_forma.get()

        # Registrar no histórico de pagamentos/abatimentos
        hist = HistoricoPagamentoConta(
            conta_id=self.conta.id,
            cliente_id=self.conta.cliente_id,
            data_hora=datetime.now(),
            valor_pago=val,
            forma_pgto=forma,
            saldo_anterior=saldo_anterior,
            saldo_restante=self.conta.saldo_devedor,
            usuario_id=self.usuario.id if self.usuario else None,
            observacao=f"Abate/Pgto Conta #{self.conta.id}"
        )
        db_session.add(hist)

        # Se for em dinheiro, lança entrada de caixa
        if forma == "DINHEIRO":
            mov = MovimentoCaixa(
                data_hora=datetime.now(),
                tipo="RECEBIMENTO_CONTA",
                valor=val,
                descricao=f"Receb. Conta #{self.conta.id} - {self.conta.cliente.nome}",
                usuario_id=self.usuario.id if self.usuario else None
            )
            db_session.add(mov)

        try:
            db_session.commit()
            
            # Emissão do comprovante térmico se selecionado
            if self.check_comprovante.get():
                from core.impressao import emitir_recibo_pagamento
                op_nome = self.usuario.nome if self.usuario else "Operador"
                emitir_recibo_pagamento(self.conta, valor_pago=val, forma_pgto=forma, operador=op_nome, abrir_visualizacao=True)

            messagebox.showinfo("Sucesso", f"Recebimento de R$ {val:.2f} registrado com sucesso!\nSaldo devedor restante: R$ {self.conta.saldo_devedor:.2f}", parent=self)
            if self.on_sucesso:
                self.on_sucesso()
            self.destroy()
        except Exception as ex:
            db_session.rollback()
            messagebox.showerror("Erro", str(ex), parent=self)



class ModalExtratoCliente(ctk.CTkToplevel):
    def __init__(self, master, cliente, usuario=None):
        super().__init__(master)
        self.cliente = cliente
        self.usuario = usuario

        self.title(f"Extrato / Histórico do Cliente — {self.cliente.nome}")
        self.geometry("820x620")
        self.minsize(750, 500)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"820x620+{(sw-820)//2}+{(sh-620)//2}")

        self._carregar_dados()
        self._build()

    def _carregar_dados(self):
        """
        Carrega todas as compras a prazo e abatimentos do cliente em ordem cronológica.
        """
        self.timeline = [] # list of dicts: {'data', 'tipo', 'ref', 'valor', 'saldo_apos', 'detalhe'}
        
        # 1. Obter todas as vendas a prazo do cliente
        vendas_prazo = db_session.query(Venda).filter(
            Venda.cliente_id == self.cliente.id,
            Venda.forma_pgto.ilike("%A PRAZO%")
        ).order_by(Venda.data.asc()).all()

        # 2. Obter todas as contas a receber do cliente (caso haja avulsas sem venda)
        contas = db_session.query(ContaReceber).filter(
            ContaReceber.cliente_id == self.cliente.id
        ).order_by(ContaReceber.data_emissao.asc()).all()

        # 3. Obter todos os pagamentos/abatimentos registrados
        pagamentos = db_session.query(HistoricoPagamentoConta).filter(
            HistoricoPagamentoConta.cliente_id == self.cliente.id
        ).order_by(HistoricoPagamentoConta.data_hora.asc()).all()

        # Montar lista bruta de eventos
        eventos = []
        
        # Se existem vendas a prazo registradas:
        vendas_ids_registradas = set()
        for v in vendas_prazo:
            vendas_ids_registradas.add(v.id)
            eventos.append({
                "data": v.data,
                "tipo_raw": "COMPRA",
                "tipo": f"COMPRA #{v.numero:06d}",
                "ref": f"Venda #{v.numero:06d}",
                "debito": float(v.total or 0.0),
                "credito": 0.0,
                "detalhe": f"Forma: {v.forma_pgto}"
            })

        # Adicionar contas que eventualmente foram lançadas sem venda associada
        for c in contas:
            if c.venda_id and c.venda_id in vendas_ids_registradas:
                continue
            if not c.venda_id and c.valor_total > 0:
                eventos.append({
                    "data": c.data_emissao,
                    "tipo_raw": "CONTA_INICIAL",
                    "tipo": f"CONTA #{c.id}",
                    "ref": f"Lançamento #{c.id}",
                    "debito": float(c.valor_total),
                    "credito": 0.0,
                    "detalhe": c.descricao or "Abertura de conta"
                })

        # Adicionar os pagamentos do histórico
        total_pago_historico = 0.0
        for p in pagamentos:
            total_pago_historico += p.valor_pago
            eventos.append({
                "data": p.data_hora,
                "tipo_raw": "PAGAMENTO",
                "tipo": "PAGAMENTO / ABATE",
                "ref": f"Recibo #{p.id:06d}",
                "debito": 0.0,
                "credito": float(p.valor_pago),
                "detalhe": f"{p.forma_pgto} ({p.observacao or ''})"
            })

        # Caso a conta tenha valor_pago anterior à criação da tabela historico_pagamentos
        total_pago_contas = sum(c.valor_pago or 0.0 for c in contas)
        if total_pago_contas > (total_pago_historico + 0.01):
            diferenca = total_pago_contas - total_pago_historico
            eventos.append({
                "data": contas[0].data_emissao if contas else datetime.now(),
                "tipo_raw": "PAGAMENTO_ANTERIOR",
                "tipo": "ABATIMENTO ANTERIOR",
                "ref": "Saldo Anterior",
                "debito": 0.0,
                "credito": float(diferenca),
                "detalhe": "Abatimentos anteriores registrados"
            })

        # Ordenar cronologicamente
        eventos.sort(key=lambda x: x["data"])

        # Calcular saldos progressivos acumulados
        saldo = 0.0
        self.resumo = {"total_compras": 0.0, "total_abates": 0.0, "saldo_atual": 0.0}
        
        for ev in eventos:
            if ev["debito"] > 0:
                saldo += ev["debito"]
                self.resumo["total_compras"] += ev["debito"]
                valor_mov = ev["debito"]
                tipo_display = f"+ {ev['tipo']}"
            else:
                saldo = max(0.0, saldo - ev["credito"])
                self.resumo["total_abates"] += ev["credito"]
                valor_mov = ev["credito"]
                tipo_display = f"- {ev['tipo']}"

            self.timeline.append({
                "data": ev["data"],
                "tipo": tipo_display,
                "ref": ev["ref"],
                "valor": valor_mov,
                "saldo_apos": saldo,
                "detalhe": ev["detalhe"],
                "tipo_raw": ev["tipo_raw"]
            })

        # O saldo devedor atual consolidado oficial vem das contas em aberto
        saldo_real_contas = sum(c.saldo_devedor for c in contas if c.status != "PAGO")
        if abs(saldo - saldo_real_contas) > 0.05 and saldo_real_contas > 0:
            self.resumo["saldo_atual"] = saldo_real_contas
        else:
            self.resumo["saldo_atual"] = saldo

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        h = ctk.CTkFrame(self, fg_color=COR, height=50, corner_radius=0)
        h.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(h, text=f"📜 Histórico / Extrato Financeiro — {self.cliente.nome}",
                     font=("Segoe UI", 14, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        ctk.CTkButton(h, text="🖨️ Imprimir Extrato Térmico", font=("Segoe UI", 11, "bold"),
                      fg_color="white", text_color=COR, hover_color="#f8bbd0", height=32,
                      command=self._imprimir).pack(side="right", padx=14, pady=8)

        # Cards de Resumo Financeiro
        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew", padx=16, pady=10)
        cards.grid_columnconfigure((0, 1, 2), weight=1)

        # Card 1: Compras a Prazo
        c1 = ctk.CTkFrame(cards, fg_color="#e3f2fd", corner_radius=8)
        c1.grid(row=0, column=0, sticky="ew", padx=4)
        ctk.CTkLabel(c1, text="Total Comprado a Prazo", font=("Segoe UI", 10, "bold"), text_color="#1565c0").pack(pady=(6, 1))
        ctk.CTkLabel(c1, text=f"R$ {self.resumo['total_compras']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                     font=("Segoe UI", 15, "bold"), text_color="#0d47a1").pack(pady=(0, 6))

        # Card 2: Total Abatido/Pago
        c2 = ctk.CTkFrame(cards, fg_color="#e8f5e9", corner_radius=8)
        c2.grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkLabel(c2, text="Total Abatido / Pago", font=("Segoe UI", 10, "bold"), text_color="#2e7d32").pack(pady=(6, 1))
        ctk.CTkLabel(c2, text=f"R$ {self.resumo['total_abates']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                     font=("Segoe UI", 15, "bold"), text_color="#1b5e20").pack(pady=(0, 6))

        # Card 3: Saldo Devedor Atual
        cor_bg = "#fce4ec" if self.resumo['saldo_atual'] > 0 else "#e0f2f1"
        cor_tx = "#ad1457" if self.resumo['saldo_atual'] > 0 else "#00695c"
        txt_status = "Dívida em Aberto" if self.resumo['saldo_atual'] > 0 else "CONTA 100% QUITADA"

        c3 = ctk.CTkFrame(cards, fg_color=cor_bg, corner_radius=8)
        c3.grid(row=0, column=2, sticky="ew", padx=4)
        ctk.CTkLabel(c3, text=f"Saldo Restante ({txt_status})", font=("Segoe UI", 10, "bold"), text_color=cor_tx).pack(pady=(6, 1))
        ctk.CTkLabel(c3, text=f"R$ {self.resumo['saldo_atual']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                     font=("Segoe UI", 16, "bold"), text_color=cor_tx).pack(pady=(0, 6))

        # Tabela / Timeline
        t_frame = ctk.CTkFrame(self, corner_radius=8)
        t_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 10))
        t_frame.grid_columnconfigure(0, weight=1)
        t_frame.grid_rowconfigure(0, weight=1)

        cols = ("Data/Hora", "Tipo de Movimentação", "Referência", "Valor (R$)", "Saldo Após (R$)", "Detalhes")
        self.tv = ttk.Treeview(t_frame, columns=cols, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols:
            self.tv.heading(c, text=c)

        self.tv.column("Data/Hora", width=120, anchor="center")
        self.tv.column("Tipo de Movimentação", width=170, anchor="w")
        self.tv.column("Referência", width=110, anchor="center")
        self.tv.column("Valor (R$)", width=100, anchor="e")
        self.tv.column("Saldo Após (R$)", width=110, anchor="e")
        self.tv.column("Detalhes", width=170, anchor="w")

        sb = ttk.Scrollbar(t_frame, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

        # Tags para colorir compras e pagamentos
        self.tv.tag_configure("COMPRA", foreground="#b71c1c")
        self.tv.tag_configure("PAGAMENTO", foreground="#1b5e20")

        for m in self.timeline:
            dt_str = m["data"].strftime("%d/%m/%Y %H:%M") if hasattr(m["data"], "strftime") else str(m["data"])
            tag = "COMPRA" if "+" in m["tipo"] else "PAGAMENTO"
            self.tv.insert("", "end", values=(
                dt_str,
                m["tipo"],
                m["ref"],
                f"R$ {m['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                f"R$ {m['saldo_apos']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                m["detalhe"]
            ), tags=(tag,))

        # Rodapé com botões
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))

        ctk.CTkLabel(bot, text="* Compras a prazo aumentam a dívida (+) | Pagamentos e abatimentos abatem a dívida (-)",
                     font=("Segoe UI", 9), text_color="gray50").pack(side="left")

        ctk.CTkButton(bot, text="Fechar", width=100, height=34, fg_color="gray40", command=self.destroy).pack(side="right")
        ctk.CTkButton(bot, text="🖨️ Imprimir na Bobina Térmica", width=200, height=34, font=("Segoe UI", 11, "bold"),
                      fg_color=COR, command=self._imprimir).pack(side="right", padx=8)

    def _imprimir(self):
        from core.impressao import emitir_extrato_cliente
        op_nome = self.usuario.nome if self.usuario else "Operador"
        emitir_extrato_cliente(self.cliente, self.timeline, self.resumo, operador=op_nome, abrir_visualizacao=True)


class TelaContasReceber(ctk.CTkFrame):
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
        ctk.CTkLabel(h, text="📖  Contas a Receber (Vendas a Prazo / Fiado)",
                     font=("Segoe UI", 16, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        ctk.CTkButton(h, text="💰 Baixa / Receber", width=150, height=34, font=("Segoe UI", 12, "bold"),
                      fg_color="white", text_color=COR, hover_color="#f8bbd0", command=self._baixar_conta).pack(side="right", padx=8, pady=8)

        ctk.CTkButton(h, text="📜 Extrato do Cliente", width=160, height=34, font=("Segoe UI", 12, "bold"),
                      fg_color="#f06292", text_color="white", hover_color="#e91e63", command=self._ver_extrato).pack(side="right", padx=4, pady=8)

        # Barra de Filtros e Totalizadores
        bar = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        bar.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        bar.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(bar, text="Filtrar Situação:", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, padx=12, pady=10)

        self.filtro_status = ctk.CTkSegmentedButton(bar, values=["TODAS", "PENDENTES", "QUITADAS"],
                                                     command=lambda v: self._load())
        self.filtro_status.set("PENDENTES")
        self.filtro_status.grid(row=0, column=1, padx=6, pady=10)

        self.ent_busca_cli = ctk.CTkEntry(bar, placeholder_text="🔍 Filtrar por nome do cliente...", width=260)
        self.ent_busca_cli.grid(row=0, column=2, padx=10, pady=10)
        self.ent_busca_cli.bind("<KeyRelease>", lambda e: self._load())

        self.lbl_total_pendente = ctk.CTkLabel(bar, text="Total a Receber: R$ 0,00", font=("Segoe UI", 13, "bold"), text_color=COR)
        self.lbl_total_pendente.grid(row=0, column=3, sticky="e", padx=20)

        # Tabela
        t_frame = ctk.CTkFrame(self, corner_radius=8)
        t_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(6, 16))
        t_frame.grid_columnconfigure(0, weight=1)
        t_frame.grid_rowconfigure(0, weight=1)

        cols = ("Conta Nº", "Data Emissão", "Cliente", "Venda Origem", "Total Original", "Valor Pago", "Saldo Devedor", "Situação")
        self.tv = ttk.Treeview(t_frame, columns=cols, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols: self.tv.heading(c, text=c)

        self.tv.column("Conta Nº",        width=70,  anchor="center")
        self.tv.column("Data Emissão",    width=130, anchor="center")
        self.tv.column("Cliente",         width=230)
        self.tv.column("Venda Origem",    width=110, anchor="center")
        self.tv.column("Total Original",  width=100, anchor="e")
        self.tv.column("Valor Pago",      width=100, anchor="e")
        self.tv.column("Saldo Devedor",   width=110, anchor="e")
        self.tv.column("Situação",        width=100, anchor="center")

        self.tv.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        sb = ttk.Scrollbar(t_frame, orient="vertical", command=self.tv.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=10)
        self.tv.configure(yscrollcommand=sb.set)

        self.tv.bind("<Double-1>", lambda e: self._baixar_conta())

    def _load(self):
        for r in self.tv.get_children():
            self.tv.delete(r)

        st = self.filtro_status.get()
        busca = self.ent_busca_cli.get().strip()

        q = db_session.query(ContaReceber).join(Cliente)

        if st == "PENDENTES":
            q = q.filter(ContaReceber.status.in_(["PENDENTE", "PARCIAL"]))
        elif st == "QUITADAS":
            q = q.filter(ContaReceber.status == "PAGO")

        if busca:
            q = q.filter(Cliente.nome.ilike(f"%{busca}%"))

        contas = q.order_by(ContaReceber.id.desc()).all()

        total_a_receber = sum(c.saldo_devedor for c in contas if c.status != "PAGO")
        self.lbl_total_pendente.configure(
            text=f"Total a Receber: R$ {total_a_receber:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

        for c in contas:
            v_num = f"#{c.venda.numero:06d}" if c.venda else "-"
            self.tv.insert("", "end", iid=str(c.id), values=(
                f"#{c.id:04d}",
                c.data_emissao.strftime("%d/%m/%Y %H:%M"),
                c.cliente.nome if c.cliente else "Consumidor",
                v_num,
                f"R$ {c.valor_total:.2f}",
                f"R$ {c.valor_pago:.2f}",
                f"R$ {c.saldo_devedor:.2f}",
                c.status
            ))

    def _ver_extrato(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma conta na lista para visualizar o extrato do cliente!")
            return
        cid = int(self.tv.item(sel[0])["values"][0])
        conta = db_session.query(ContaReceber).get(cid)
        if not conta or not conta.cliente:
            messagebox.showerror("Erro", "Cliente não encontrado para esta conta!")
            return
        ModalExtratoCliente(self, conta.cliente, usuario=self.usuario)

    def _baixar_conta(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma conta na lista para registrar pagamento.")
            return

        conta = db_session.query(ContaReceber).get(int(sel[0]))
        if conta:
            if conta.status == "PAGO" or conta.saldo_devedor <= 0:
                messagebox.showinfo("Conta Quitada", "Esta conta já foi totalmente paga e quitada!")
                return
            ModalBaixaConta(self, conta=conta, usuario=self.usuario, on_sucesso=self._load)
