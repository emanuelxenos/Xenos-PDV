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
        self.geometry("860x660")
        self.minsize(780, 520)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"860x660+{(sw-860)//2}+{(sh-660)//2}")

        # Paginação e ordenação
        self.ordem_decrescente = True  # Padrão: Mais recentes primeiro (Decrescente)
        self.pagina_atual = 1
        self.itens_por_pagina = 20

        self._carregar_dados()
        self._build()
        self._atualizar_tabela()

    def _carregar_dados(self):
        """
        Carrega todas as compras a prazo e abatimentos do cliente em ordem cronológica para cálculo,
        guardando o timeline completo.
        """
        self.timeline = []  # Todos os registros com saldos progressivos calculados cronologicamente
        
        # 1. Obter todas as vendas a prazo do cliente
        vendas_prazo = db_session.query(Venda).filter(
            Venda.cliente_id == self.cliente.id,
            Venda.forma_pgto.ilike("%A PRAZO%"),
            Venda.status != "CANCELADA"
        ).order_by(Venda.data.asc()).all()

        # 2. Obter todas as contas a receber do cliente (caso haja avulsas/migradas sem venda)
        contas = db_session.query(ContaReceber).filter(
            ContaReceber.cliente_id == self.cliente.id
        ).order_by(ContaReceber.data_emissao.asc()).all()

        # 3. Obter todos os pagamentos/abatimentos registrados
        pagamentos = db_session.query(HistoricoPagamentoConta).filter(
            HistoricoPagamentoConta.cliente_id == self.cliente.id
        ).order_by(HistoricoPagamentoConta.data_hora.asc()).all()

        eventos = []
        
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
                "detalhe": f"Forma: {v.forma_pgto}",
                "venda_id": v.id,
                "numero_venda": v.numero
            })

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

        # Ordenar cronologicamente para calcular o saldo devedor progressivo corretamente
        eventos.sort(key=lambda x: x["data"])

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
                "tipo_raw": ev["tipo_raw"],
                "venda_id": ev.get("venda_id"),
                "numero_venda": ev.get("numero_venda")
            })

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
        cards.grid(row=1, column=0, sticky="ew", padx=16, pady=(10, 4))
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

        # Barra de controles da lista: Ordenação e Itens por página
        ctrl_bar = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_bar.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 4))
        ctrl_bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(ctrl_bar, text="Ordenar por:", font=("Segoe UI", 11, "bold")).pack(side="left", padx=(4, 6))
        self.btn_ordem = ctk.CTkSegmentedButton(
            ctrl_bar,
            values=["Mais Recentes Primeiro (Decrescente)", "Mais Antigos Primeiro (Crescente)"],
            command=self._on_mudar_ordem
        )
        self.btn_ordem.set("Mais Recentes Primeiro (Decrescente)")
        self.btn_ordem.pack(side="left", padx=4)

        ctk.CTkLabel(ctrl_bar, text="Itens por página:", font=("Segoe UI", 11)).pack(side="right", padx=(4, 4))
        self.combo_itens_pag = ctk.CTkComboBox(
            ctrl_bar,
            values=["10", "20", "50", "100", "Todos"],
            width=85,
            command=self._on_mudar_itens_por_pag
        )
        self.combo_itens_pag.set("20")
        self.combo_itens_pag.pack(side="right", padx=4)

        # Container da Tabela
        t_frame = ctk.CTkFrame(self, corner_radius=8)
        t_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 4))
        self.grid_rowconfigure(3, weight=1)
        t_frame.grid_columnconfigure(0, weight=1)
        t_frame.grid_rowconfigure(0, weight=1)

        cols = ("Data/Hora", "Tipo de Movimentação", "Referência", "Valor (R$)", "Saldo Restante Após (R$)", "Detalhes")
        self.tv = ttk.Treeview(t_frame, columns=cols, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols:
            self.tv.heading(c, text=c)

        self.tv.column("Data/Hora", width=125, anchor="center")
        self.tv.column("Tipo de Movimentação", width=175, anchor="w")
        self.tv.column("Referência", width=110, anchor="center")
        self.tv.column("Valor (R$)", width=105, anchor="e")
        self.tv.column("Saldo Restante Após (R$)", width=150, anchor="e")
        self.tv.column("Detalhes", width=175, anchor="w")

        sb = ttk.Scrollbar(t_frame, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

        self.tv.tag_configure("COMPRA", foreground="#b71c1c")
        self.tv.tag_configure("PAGAMENTO", foreground="#1b5e20")

        # Barra de Paginação
        pag_bar = ctk.CTkFrame(self, fg_color="transparent")
        pag_bar.grid(row=4, column=0, sticky="ew", padx=16, pady=(2, 6))

        self.btn_pag_ant = ctk.CTkButton(pag_bar, text="◀ Anterior", width=90, height=28, fg_color="gray30",
                                         command=self._pag_anterior)
        self.btn_pag_ant.pack(side="left", padx=4)

        self.lbl_paginacao = ctk.CTkLabel(pag_bar, text="Página 1 de 1 (0 registros)", font=("Segoe UI", 11, "bold"))
        self.lbl_paginacao.pack(side="left", padx=12)

        self.btn_pag_prox = ctk.CTkButton(pag_bar, text="Próxima ▶", width=90, height=28, fg_color="gray30",
                                          command=self._pag_proxima)
        self.btn_pag_prox.pack(side="left", padx=4)

        # Rodapé com botões de fechar e imprimir
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=5, column=0, sticky="ew", padx=16, pady=(0, 12))

        ctk.CTkLabel(bot, text="* Compras a prazo aumentam a dívida (+) | Pagamentos e abatimentos abatem a dívida (-)",
                     font=("Segoe UI", 9), text_color="gray50").pack(side="left")

        ctk.CTkButton(bot, text="Fechar", width=100, height=34, fg_color="gray40", command=self.destroy).pack(side="right")
        ctk.CTkButton(bot, text="🖨️ Imprimir na Bobina Térmica", width=190, height=34, font=("Segoe UI", 11, "bold"),
                      fg_color=COR, command=self._imprimir).pack(side="right", padx=6)
        ctk.CTkButton(bot, text="🗑️ Cancelar Venda Selecionada", width=220, height=34, font=("Segoe UI", 11, "bold"),
                      fg_color="#c62828", hover_color="#b71c1c", command=self._cancelar_venda_selecionada).pack(side="right", padx=6)

    def _get_dados_ordenados(self):
        """Retorna a lista completa ordenada conforme a preferência atual"""
        dados = list(self.timeline)
        if self.ordem_decrescente:
            dados.reverse()  # Mais recentes no topo
        return dados

    def _atualizar_tabela(self):
        for r in self.tv.get_children():
            self.tv.delete(r)

        dados = self._get_dados_ordenados()
        total_itens = len(dados)

        if total_itens == 0:
            self.lbl_paginacao.configure(text="Nenhum registro encontrado.")
            self.btn_pag_ant.configure(state="disabled")
            self.btn_pag_prox.configure(state="disabled")
            return

        if self.itens_por_pagina is None:
            # Mostrar todos
            itens_pagina = dados
            total_paginas = 1
            self.pagina_atual = 1
        else:
            total_paginas = max(1, (total_itens + self.itens_por_pagina - 1) // self.itens_por_pagina)
            if self.pagina_atual > total_paginas:
                self.pagina_atual = total_paginas
            if self.pagina_atual < 1:
                self.pagina_atual = 1

            inicio = (self.pagina_atual - 1) * self.itens_por_pagina
            fim = inicio + self.itens_por_pagina
            itens_pagina = dados[inicio:fim]

        self._mapa_itens_pagina = {}
        for idx_row, m in enumerate(itens_pagina):
            row_id = str(idx_row)
            self._mapa_itens_pagina[row_id] = m
            dt_str = m["data"].strftime("%d/%m/%Y %H:%M") if hasattr(m["data"], "strftime") else str(m["data"])
            tag = "COMPRA" if "+" in m["tipo"] else "PAGAMENTO"
            self.tv.insert("", "end", iid=row_id, values=(
                dt_str,
                m["tipo"],
                m["ref"],
                f"R$ {m['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                f"R$ {m['saldo_apos']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                m["detalhe"]
            ), tags=(tag,))

        # Atualizar status da paginação
        txt_pag = f"Página {self.pagina_atual} de {total_paginas} ({total_itens} lançamentos)"
        self.lbl_paginacao.configure(text=txt_pag)

        self.btn_pag_ant.configure(state="normal" if self.pagina_atual > 1 else "disabled")
        self.btn_pag_prox.configure(state="normal" if self.pagina_atual < total_paginas else "disabled")

    def _on_mudar_ordem(self, valor):
        self.ordem_decrescente = "Decrescente" in valor
        self.pagina_atual = 1
        self._atualizar_tabela()

    def _on_mudar_itens_por_pag(self, valor):
        if valor == "Todos":
            self.itens_por_pagina = None
        else:
            self.itens_por_pagina = int(valor)
        self.pagina_atual = 1
        self._atualizar_tabela()

    def _pag_anterior(self):
        if self.pagina_atual > 1:
            self.pagina_atual -= 1
            self._atualizar_tabela()

    def _pag_proxima(self):
        self.pagina_atual += 1
        self._atualizar_tabela()

    def _cancelar_venda_selecionada(self):
        """
        Permite ao operador cancelar uma venda feita acidentalmente para o cliente,
        estornando o estoque dos itens, cancelando a venda e deduzindo o valor exato
        da dívida em aberto sem necessidade de simular pagamento.
        """
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma compra na lista para cancelar/excluir!", parent=self)
            return

        item = getattr(self, "_mapa_itens_pagina", {}).get(sel[0])
        if not item:
            messagebox.showwarning("Aviso", "Não foi possível identificar o lançamento selecionado.", parent=self)
            return

        if item.get("tipo_raw") != "COMPRA" or not item.get("venda_id"):
            messagebox.showinfo("Informação", "Apenas lançamentos de VENDA/COMPRA podem ser cancelados aqui.\nPara pagamentos ou abatimentos, consulte o caixa.", parent=self)
            return

        venda_id = item["venda_id"]
        venda = db_session.query(Venda).get(venda_id)
        if not venda:
            messagebox.showerror("Erro", "Venda não encontrada no banco de dados!", parent=self)
            return

        valor_venda = float(venda.total or 0.0)
        num_venda = venda.numero

        msg_conf = (
            f"Deseja realmente CANCELAR e EXCLUIR a Venda #{num_venda:06d}?\n\n"
            f"• Cliente: {self.cliente.nome}\n"
            f"• Valor Total: R$ {valor_venda:.2f}\n"
            f"• Os itens da venda serão estornados de volta ao Estoque.\n"
            f"• O saldo devedor do cliente será reduzido em R$ {valor_venda:.2f}."
        )

        if not messagebox.askyesno("Confirmar Cancelamento de Venda", msg_conf, parent=self):
            return

        try:
            # 1. Devolver itens ao estoque
            for it in (venda.itens or []):
                if it.produto:
                    it.produto.estoque = (it.produto.estoque or 0.0) + (it.quantidade or 0.0)

            # 2. Deduzir o valor da venda da conta a receber do cliente
            # Procura conta associada à venda ou a conta em aberto do cliente
            contas_cliente = db_session.query(ContaReceber).filter(
                ContaReceber.cliente_id == self.cliente.id,
                ContaReceber.status.in_(["PENDENTE", "PARCIAL"])
            ).order_by(ContaReceber.id.desc()).all()

            # Desconta o valor da dívida
            valor_restante_abater = valor_venda
            for c in contas_cliente:
                if valor_restante_abater <= 0:
                    break
                abatimento = min(c.saldo_devedor, valor_restante_abater)
                c.saldo_devedor = max(0.0, c.saldo_devedor - abatimento)
                c.valor_total = max(0.0, (c.valor_total or 0.0) - abatimento)
                if c.saldo_devedor <= 0.001:
                    c.saldo_devedor = 0.0
                    c.status = "PAGO" if (c.valor_pago or 0.0) > 0 else "CANCELADO"
                valor_restante_abater -= abatimento

            # 3. Marcar a venda como CANCELADA
            venda.status = "CANCELADA"
            venda.observacao = f"{(venda.observacao or '')} [CANCELADA NO EXTRATO EM {datetime.now().strftime('%d/%m/%Y %H:%M')}]".strip()

            db_session.commit()
            messagebox.showinfo("Sucesso", f"Venda #{num_venda:06d} cancelada com sucesso!\nEstoque devolvido e dívida abatida.", parent=self)

            # Recarrega os dados do extrato
            self._carregar_dados()
            self._atualizar_tabela()

            # Se o master for TelaContasReceber, atualizar a lista de trás
            if hasattr(self.master, "_load"):
                self.master._load()

        except Exception as ex:
            db_session.rollback()
            messagebox.showerror("Erro ao Cancelar Venda", f"Falha ao cancelar a venda:\n{str(ex)}", parent=self)

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
        try:
            cid = int(sel[0])
        except (ValueError, TypeError):
            val0 = str(self.tv.item(sel[0])["values"][0]).replace("#", "").strip()
            cid = int(val0)

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
