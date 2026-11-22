"""
Tela de Frente de Caixa / PDV com Integração Automática ao Contas a Receber (Venda a Prazo).
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
from core.database import db_session, Produto, Cliente, Venda, ItemVenda, ContaReceber
from core.impressao import emitir_comprovante
from datetime import datetime

COR_PDV      = "#00897b"
COR_DESTAQUE = "#004d40"
VERDE        = "#2e7d32"
VERMELHO     = "#d32f2f"


class ModalComprovante(ctk.CTkToplevel):
    def __init__(self, master, venda, itens, operador="Operador"):
        super().__init__(master)
        self.venda = venda
        self.itens = itens
        self.operador = operador

        self.title(f"Comprovante de Venda #{venda.numero:06d}")
        self.geometry("450x600")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"450x600+{(sw-450)//2}+{(sh-600)//2}")

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        h = ctk.CTkFrame(self, fg_color=COR_PDV, corner_radius=0, height=45)
        h.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(h, text=f"🧾 Comprovante Não Fiscal — Venda #{self.venda.numero:06d}",
                     font=("Segoe UI", 13, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        from core.impressao import formatar_cupom
        texto_cupom = formatar_cupom(self.venda, self.itens, operador=self.operador)

        txt_box = ctk.CTkTextbox(self, font=("Consolas", 11), wrap="none")
        txt_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)
        txt_box.insert("1.0", texto_cupom)
        txt_box.configure(state="disabled")

        bot = ctk.CTkFrame(self, fg_color="transparent", height=50)
        bot.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))

        ctk.CTkButton(bot, text="🖨️ Imprimir na Térmica (Abrir)", font=("Segoe UI", 12, "bold"),
                      fg_color=VERDE, height=38, command=self._imprimir).pack(side="right", padx=6)
        ctk.CTkButton(bot, text="Fechar", fg_color="gray40", height=38,
                      command=self.destroy).pack(side="right", padx=6)

    def _imprimir(self):
        emitir_comprovante(self.venda, self.itens, operador=self.operador, abrir_visualizacao=True)
        self.destroy()


class TelaPDV(ctk.CTkFrame):
    def __init__(self, master, usuario=None, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.usuario = usuario
        self.carrinho = []
        self.cliente_selecionado = None
        self._ui()
        self.focar_pesquisa()

    def focar_pesquisa(self):
        """Coloca o foco imediatamente no campo de código de barras/pesquisa."""
        self.after(100, lambda: self.ent_codigo.focus_set())

    def _ui(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        col_esq = ctk.CTkFrame(self, corner_radius=8)
        col_esq.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        col_esq.grid_columnconfigure(0, weight=1)
        col_esq.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(col_esq, fg_color=COR_PDV, corner_radius=6)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(top, text="🛒  FRENTE DE CAIXA / PDV", font=("Segoe UI", 16, "bold"), text_color="white").pack(side="left", padx=14, pady=10)
        u_nome = self.usuario.nome if self.usuario else "Operador"
        ctk.CTkLabel(top, text=f"Operador: {u_nome}", font=("Segoe UI", 11), text_color="#e0f2f1").pack(side="right", padx=14)

        form_item = ctk.CTkFrame(col_esq, fg_color="#f0f4f8", corner_radius=6)
        form_item.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        form_item.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form_item, text="Cód. Barras / ID / Nome:", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.ent_codigo = ctk.CTkEntry(form_item, placeholder_text="Digite ou passe o leitor...", height=34)
        self.ent_codigo.grid(row=0, column=1, padx=(0, 10), pady=8, sticky="ew")
        self.ent_codigo.bind("<Return>", lambda e: self._adicionar_item())

        ctk.CTkLabel(form_item, text="Qtd:", font=("Segoe UI", 11, "bold")).grid(row=0, column=2, padx=5, pady=8, sticky="w")
        self.ent_qtd = ctk.CTkEntry(form_item, width=70, height=34)
        self.ent_qtd.insert(0, "1")
        self.ent_qtd.grid(row=0, column=3, padx=5, pady=8)
        self.ent_qtd.bind("<Return>", lambda e: self._adicionar_item())

        btn_add = ctk.CTkButton(form_item, text="Adicionar", width=90, height=34, fg_color=COR_PDV, command=self._adicionar_item)
        btn_add.grid(row=0, column=4, padx=10, pady=8)

        frame_tv = ctk.CTkFrame(col_esq, fg_color="transparent")
        frame_tv.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 5))
        frame_tv.grid_columnconfigure(0, weight=1)
        frame_tv.grid_rowconfigure(0, weight=1)

        cols = ("Item", "ID", "Descrição", "Qtd", "R$ Unit.", "R$ Total")
        self.tv = ttk.Treeview(frame_tv, columns=cols, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols: self.tv.heading(c, text=c)
        self.tv.column("Item",      width=40,  anchor="center")
        self.tv.column("ID",        width=50,  anchor="center")
        self.tv.column("Descrição", width=230)
        self.tv.column("Qtd",       width=60,  anchor="e")
        self.tv.column("R$ Unit.",  width=80,  anchor="e")
        self.tv.column("R$ Total",  width=90,  anchor="e")
        self.tv.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(frame_tv, orient="vertical", command=self.tv.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tv.configure(yscrollcommand=sb.set)

        b_bar = ctk.CTkFrame(col_esq, fg_color="transparent")
        b_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=8)
        ctk.CTkButton(b_bar, text="Remover Item Selecionado", fg_color=VERMELHO, command=self._remover_item).pack(side="left")
        ctk.CTkButton(b_bar, text="Cancelar Venda", fg_color="gray45", command=self._cancelar_venda).pack(side="right")

        # ─── LADO DIREITO: Totais e Fechamento ───
        col_dir = ctk.CTkFrame(self, corner_radius=8)
        col_dir.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        col_dir.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(col_dir, text="Resumo da Venda", font=("Segoe UI", 14, "bold")).pack(pady=(14, 10))

        cli_box = ctk.CTkFrame(col_dir, fg_color="#f0f4f8", corner_radius=6)
        cli_box.pack(fill="x", padx=14, pady=5)
        ctk.CTkLabel(cli_box, text="Cliente (Obrigatório para Venda a Prazo):", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(6, 2))
        self.combo_cli = ctk.CTkComboBox(cli_box, values=self._listar_clientes())
        self.combo_cli.pack(fill="x", padx=10, pady=(0, 8))

        card_total = ctk.CTkFrame(col_dir, fg_color=COR_DESTAQUE, corner_radius=8)
        card_total.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(card_total, text="TOTAL A PAGAR", font=("Segoe UI", 12), text_color="#80cbc4").pack(pady=(10, 2))
        self.lbl_total = ctk.CTkLabel(card_total, text="R$ 0,00", font=("Segoe UI", 32, "bold"), text_color="white")
        self.lbl_total.pack(pady=(0, 10))

        pgto_box = ctk.CTkFrame(col_dir, fg_color="transparent")
        pgto_box.pack(fill="x", padx=14, pady=4)
        pgto_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(pgto_box, text="Forma de Pgto:", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w", pady=4)
        self.combo_pgto = ctk.CTkComboBox(pgto_box, values=["DINHEIRO", "PIX", "CARTAO DEBITO", "CARTAO CREDITO", "A PRAZO (FIADO)"])
        self.combo_pgto.set("DINHEIRO")
        self.combo_pgto.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)

        ctk.CTkLabel(pgto_box, text="Desconto (R$):", font=("Segoe UI", 11)).grid(row=1, column=0, sticky="w", pady=4)
        self.ent_desc = ctk.CTkEntry(pgto_box)
        self.ent_desc.insert(0, "0,00")
        self.ent_desc.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)
        self.ent_desc.bind("<KeyRelease>", lambda e: self._atualizar_totais())

        ctk.CTkLabel(pgto_box, text="Valor Recebido (R$):", font=("Segoe UI", 11)).grid(row=2, column=0, sticky="w", pady=4)
        self.ent_recebido = ctk.CTkEntry(pgto_box)
        self.ent_recebido.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=4)
        self.ent_recebido.bind("<KeyRelease>", lambda e: self._atualizar_troco())

        self.lbl_troco = ctk.CTkLabel(col_dir, text="Troco: R$ 0,00", font=("Segoe UI", 14, "bold"), text_color=COR_PDV)
        self.lbl_troco.pack(pady=10)

        self.check_imprimir = ctk.CTkCheckBox(col_dir, text="Emitir Comprovante Térmico", font=("Segoe UI", 11))
        self.check_imprimir.select()
        self.check_imprimir.pack(pady=(0, 10))

        btn_finalizar = ctk.CTkButton(col_dir, text="✔  FINALIZAR VENDA", height=48, font=("Segoe UI", 14, "bold"),
                                      fg_color=VERDE, hover_color="#1b5e20", command=self._finalizar_venda)
        btn_finalizar.pack(fill="x", padx=14, pady=(10, 14), side="bottom")

    def _listar_clientes(self):
        clis = db_session.query(Cliente).filter_by(ativo=True).order_by(Cliente.nome).all()
        self._mapa_cli = {f"{c.id} - {c.nome}": c.id for c in clis}
        return ["Consumidor Final"] + list(self._mapa_cli.keys())

    def _adicionar_item(self):
        termo = self.ent_codigo.get().strip()
        if not termo: return

        try:
            qtd = float(self.ent_qtd.get().replace(",", "."))
            if qtd <= 0: qtd = 1.0
        except: qtd = 1.0

        condicoes = [Produto.codigo_barras == termo, Produto.descricao.ilike(f"%{termo}%")]
        if termo.isdigit(): condicoes.append(Produto.id == int(termo))

        prod = db_session.query(Produto).filter(
            Produto.ativo == True,
            (condicoes[0] | condicoes[1] | condicoes[2]) if len(condicoes) == 3 else (condicoes[0] | condicoes[1])
        ).first()

        if not prod:
            messagebox.showwarning("Não Encontrado", f"Produto '{termo}' não localizado!")
            return

        total_item = qtd * prod.preco_venda
        idx = len(self.carrinho) + 1
        item = {
            "num": idx, "produto_id": prod.id, "descricao": prod.descricao,
            "qtd": qtd, "preco": prod.preco_venda, "total": total_item
        }
        self.carrinho.append(item)
        self.tv.insert("", "end", iid=str(idx),
                       values=(idx, prod.id, prod.descricao, f"{qtd:.2f}",
                               f"{prod.preco_venda:.2f}", f"{total_item:.2f}"))

        self.ent_codigo.delete(0, "end")
        self.ent_qtd.delete(0, "end"); self.ent_qtd.insert(0, "1")
        self.ent_codigo.focus()
        self._atualizar_totais()

    def _remover_item(self):
        sel = self.tv.selection()
        if not sel: return
        item_idx = int(sel[0]) - 1
        if 0 <= item_idx < len(self.carrinho):
            self.carrinho.pop(item_idx)
            for r in self.tv.get_children(): self.tv.delete(r)
            for i, it in enumerate(self.carrinho, 1):
                it["num"] = i
                self.tv.insert("", "end", iid=str(i),
                               values=(i, it["produto_id"], it["descricao"], f"{it['qtd']:.2f}",
                                       f"{it['preco']:.2f}", f"{it['total']:.2f}"))
            self._atualizar_totais()

    def _atualizar_totais(self):
        subtotal = sum(i["total"] for i in self.carrinho)
        try: desc = float(self.ent_desc.get().replace(",", "."))
        except: desc = 0.0
        total = max(0.0, subtotal - desc)
        self.lbl_total.configure(text=f"R$ {total:.2f}")
        self._atualizar_troco()

    def _atualizar_troco(self):
        subtotal = sum(i["total"] for i in self.carrinho)
        try: desc = float(self.ent_desc.get().replace(",", "."))
        except: desc = 0.0
        total = max(0.0, subtotal - desc)
        try:
            rec = float(self.ent_recebido.get().replace(",", "."))
            troco = max(0.0, rec - total)
            self.lbl_troco.configure(text=f"Troco: R$ {troco:.2f}")
        except:
            self.lbl_troco.configure(text="Troco: R$ 0,00")

    def _finalizar_venda(self):
        if not self.carrinho:
            messagebox.showwarning("Venda Vazia", "Adicione ao menos um item para finalizar!")
            return

        forma = self.combo_pgto.get()
        cli_str = self.combo_cli.get()
        cli_id = self._mapa_cli.get(cli_str, None)

        if "A PRAZO" in forma and not cli_id:
            messagebox.showerror("Atenção", "Para realizar venda A PRAZO (FIADO), selecione um Cliente cadastrado!", parent=self)
            return

        subtotal = sum(i["total"] for i in self.carrinho)
        try: desc = float(self.ent_desc.get().replace(",", "."))
        except: desc = 0.0
        total = max(0.0, subtotal - desc)

        try: rec = float(self.ent_recebido.get().replace(",", "."))
        except: rec = 0.0 if "A PRAZO" in forma else total

        troco = 0.0 if "A PRAZO" in forma else max(0.0, rec - total)

        ultima = db_session.query(Venda).order_by(Venda.id.desc()).first()
        proximo_num = (ultima.numero + 1) if ultima and ultima.numero else 1

        try:
            nova_venda = Venda(
                numero=proximo_num,
                data=datetime.now(),
                cliente_id=cli_id,
                usuario_id=self.usuario.id if self.usuario else None,
                subtotal=subtotal,
                desconto=desc,
                total=total,
                forma_pgto=forma,
                valor_pago=rec,
                troco=troco,
                status="CONCLUIDA"
            )
            db_session.add(nova_venda)
            db_session.flush()

            # Criação dos itens e baixa de estoque
            itens_criados = []
            for item in self.carrinho:
                item_obj = ItemVenda(
                    venda_id=nova_venda.id,
                    produto_id=item["produto_id"],
                    descricao=item["descricao"],
                    quantidade=item["qtd"],
                    preco_unit=item["preco"],
                    total=item["total"]
                )
                db_session.add(item_obj)
                itens_criados.append(item_obj)

                p = db_session.query(Produto).get(item["produto_id"])
                if p: p.estoque = (p.estoque or 0.0) - item["qtd"]

            # SE FOR VENDA A PRAZO: Cria automaticamente a Conta a Receber vinculada ao Cliente
            if "A PRAZO" in forma:
                saldo_restante = max(0.0, total - rec)
                st_conta = "PAGO" if saldo_restante <= 0 else ("PARCIAL" if rec > 0 else "PENDENTE")
                nova_conta = ContaReceber(
                    cliente_id=cli_id,
                    venda_id=nova_venda.id,
                    data_emissao=datetime.now(),
                    valor_total=total,
                    valor_pago=rec,
                    saldo_devedor=saldo_restante,
                    status=st_conta,
                    descricao=f"Venda a Prazo #{nova_venda.numero:06d}"
                )
                db_session.add(nova_conta)

            db_session.commit()

            if self.check_imprimir.get():
                op_nome = self.usuario.nome if self.usuario else "Operador"
                ModalComprovante(self, venda=nova_venda, itens=itens_criados, operador=op_nome)
            else:
                messagebox.showinfo("Sucesso", f"Venda nº {proximo_num} finalizada com sucesso!")

            self._cancelar_venda()

        except Exception as ex:
            db_session.rollback()
            messagebox.showerror("Erro ao Concluir Venda", str(ex))

    def _cancelar_venda(self):
        self.carrinho.clear()
        for r in self.tv.get_children(): self.tv.delete(r)
        self.ent_desc.delete(0, "end"); self.ent_desc.insert(0, "0,00")
        self.ent_recebido.delete(0, "end")
        self.lbl_total.configure(text="R$ 0,00")
        self.lbl_troco.configure(text="Troco: R$ 0,00")
        self.combo_cli.configure(values=self._listar_clientes())
        self.combo_cli.set("Consumidor Final")
        self.combo_pgto.set("DINHEIRO")
        self.ent_codigo.focus()
