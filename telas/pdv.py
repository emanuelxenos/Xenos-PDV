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


class ModalSelecionarProduto(ctk.CTkToplevel):
    def __init__(self, master, produtos, on_selecionado):
        super().__init__(master)
        self.produtos = produtos
        self.on_selecionado = on_selecionado

        self.title("Selecione o Produto")
        self.geometry("700x420")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"700x420+{(sw-700)//2}+{(sh-420)//2}")

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        h = ctk.CTkFrame(self, fg_color=COR_PDV, corner_radius=0, height=45)
        h.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(h, text=f"🔍 Vários produtos encontrados ({len(self.produtos)} opções). Escolha o correto:",
                     font=("Segoe UI", 12, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        f_tv = ctk.CTkFrame(self, fg_color="transparent")
        f_tv.grid(row=1, column=0, sticky="nsew", padx=16, pady=10)
        f_tv.grid_columnconfigure(0, weight=1)
        f_tv.grid_rowconfigure(0, weight=1)

        cols = ("ID", "Cód. Barras", "Descrição", "Unidade", "Preço Venda", "Estoque")
        self.tv = ttk.Treeview(f_tv, columns=cols, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols: self.tv.heading(c, text=c)

        self.tv.column("ID",          width=60,  anchor="center")
        self.tv.column("Cód. Barras", width=120, anchor="center")
        self.tv.column("Descrição",   width=260)
        self.tv.column("Unidade",     width=60,  anchor="center")
        self.tv.column("Preço Venda", width=90,  anchor="e")
        self.tv.column("Estoque",     width=70,  anchor="e")

        self.tv.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(f_tv, orient="vertical", command=self.tv.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tv.configure(yscrollcommand=sb.set)

        self._mapa = {}
        for p in self.produtos:
            self._mapa[str(p.id)] = p
            self.tv.insert("", "end", iid=str(p.id), values=(
                p.id,
                p.codigo_barras or "-",
                p.descricao,
                p.unidade or "UN",
                f"R$ {p.preco_venda:.2f}",
                f"{p.estoque:.1f}" if p.estoque is not None else "0.0"
            ))

        # Selecionar o primeiro por padrão
        if self.produtos:
            primeiro = str(self.produtos[0].id)
            self.tv.selection_set(primeiro)
            self.tv.focus(primeiro)

        self.tv.bind("<Double-1>", lambda e: self._confirmar())
        self.bind("<Return>", lambda e: self._confirmar())
        self.bind("<Escape>", lambda e: self.destroy())

        bot = ctk.CTkFrame(self, fg_color="transparent", height=45)
        bot.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))

        ctk.CTkLabel(bot, text="[Enter] ou Duplo Clique para selecionar | [Esc] Cancelar",
                     font=("Segoe UI", 10), text_color="gray40").pack(side="left")

        ctk.CTkButton(bot, text="✔ Selecionar", font=("Segoe UI", 12, "bold"), fg_color=COR_PDV,
                       width=120, height=36, command=self._confirmar).pack(side="right", padx=4)
        ctk.CTkButton(bot, text="Cancelar", fg_color="gray40", width=90, height=36,
                       command=self.destroy).pack(side="right", padx=4)

    def _confirmar(self):
        sel = self.tv.selection()
        if not sel: return
        p = self._mapa.get(sel[0])
        if p and self.on_selecionado:
            self.on_selecionado(p)
        self.destroy()
        if hasattr(self.master, "_focar_codigo"):
            self.master._focar_codigo()


class ModalPesagemProduto(ctk.CTkToplevel):
    """
    Mini-quadro inteligente para produtos vendidos por KG ou granel.
    Permite ao operador digitar tanto o PESO (kg) quanto o VALOR DESEJADO (R$).
    Atualiza ambos automaticamente em tempo real!
    """
    def __init__(self, master, produto, on_confirmar):
        super().__init__(master)
        self.produto = produto
        self.on_confirmar = on_confirmar
        self.preco_unit = produto.preco_venda or 0.0

        self.title("Pesagem / Valor — Produto por Quilo")
        self.geometry("440x330")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"440x330+{(sw-440)//2}+{(sh-330)//2}")

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        h = ctk.CTkFrame(self, fg_color=COR_PDV, corner_radius=0, height=45)
        h.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(h, text="⚖️  PRODUTO POR QUILO (PESAGEM / VALOR)",
                     font=("Segoe UI", 12, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=1, column=0, sticky="nsew", padx=20, pady=14)

        ctk.CTkLabel(f, text=self.produto.descricao, font=("Segoe UI", 13, "bold"), wraplength=400).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(f, text=f"Preço do Quilo: R$ {self.preco_unit:.2f} / KG",
                     font=("Segoe UI", 11), text_color="gray35").pack(anchor="w", pady=(0, 14))

        box = ctk.CTkFrame(f, fg_color="#f0f4f8", corner_radius=8)
        box.pack(fill="x", pady=(0, 10))
        box.grid_columnconfigure((0, 1), weight=1)

        # Opção 1: Peso em KG
        ctk.CTkLabel(box, text="Peso na Balança (KG):", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, padx=14, pady=(10, 2), sticky="w")
        self.ent_peso = ctk.CTkEntry(box, font=("Segoe UI", 14, "bold"), height=36, placeholder_text="Ex: 1,500")
        self.ent_peso.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="ew")
        self.ent_peso.bind("<KeyRelease>", self._calc_por_peso)
        self.ent_peso.bind("<Return>", lambda e: self._confirmar())

        # Opção 2: Valor que o cliente pediu (R$)
        ctk.CTkLabel(box, text="OU Valor Pedido (R$):", font=("Segoe UI", 11, "bold")).grid(row=0, column=1, padx=14, pady=(10, 2), sticky="w")
        self.ent_reais = ctk.CTkEntry(box, font=("Segoe UI", 14, "bold"), height=36, placeholder_text="Ex: 13,00")
        self.ent_reais.grid(row=1, column=1, padx=14, pady=(0, 12), sticky="ew")
        self.ent_reais.bind("<KeyRelease>", self._calc_por_reais)
        self.ent_reais.bind("<Return>", lambda e: self._confirmar())

        self.lbl_resumo = ctk.CTkLabel(f, text=f"Total: R$ 0,00  |  Peso: 0,000 KG",
                                       font=("Segoe UI", 13, "bold"), text_color=COR_DESTAQUE)
        self.lbl_resumo.pack(pady=4)

        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 14))

        ctk.CTkLabel(bot, text="[Enter] Confirmar | [Esc] Cancelar", font=("Segoe UI", 10), text_color="gray40").pack(side="left")

        ctk.CTkButton(bot, text="✔ Confirmar Item", font=("Segoe UI", 12, "bold"), fg_color=VERDE,
                      height=38, width=130, command=self._confirmar).pack(side="right", padx=4)
        ctk.CTkButton(bot, text="Cancelar", fg_color="gray40", height=38, width=80,
                      command=self.destroy).pack(side="right", padx=4)

        self.bind("<Escape>", lambda e: self.destroy())
        self.after(100, lambda: self.ent_peso.focus())

    def _calc_por_peso(self, event=None):
        txt = self.ent_peso.get().replace(",", ".").strip()
        try:
            peso = float(txt)
            total = peso * self.preco_unit
            self.ent_reais.delete(0, "end")
            self.ent_reais.insert(0, f"{total:.2f}".replace(".", ","))
            self.lbl_resumo.configure(text=f"Total: R$ {total:.2f}  |  Peso: {peso:.3f} KG")
        except:
            if not txt:
                self.ent_reais.delete(0, "end")
                self.lbl_resumo.configure(text=f"Total: R$ 0,00  |  Peso: 0,000 KG")

    def _calc_por_reais(self, event=None):
        txt = self.ent_reais.get().replace(",", ".").strip()
        try:
            total = float(txt)
            if self.preco_unit > 0:
                peso = round(total / self.preco_unit, 3)
            else:
                peso = 0.0
            self.ent_peso.delete(0, "end")
            self.ent_peso.insert(0, f"{peso:.3f}".replace(".", ","))
            self.lbl_resumo.configure(text=f"Total: R$ {total:.2f}  |  Peso: {peso:.3f} KG")
        except:
            if not txt:
                self.ent_peso.delete(0, "end")
                self.lbl_resumo.configure(text=f"Total: R$ 0,00  |  Peso: 0,000 KG")

    def _confirmar(self):
        try:
            peso = float(self.ent_peso.get().replace(",", ".").strip())
            total = float(self.ent_reais.get().replace(",", ".").strip())
            if peso <= 0 or total <= 0: raise ValueError
        except:
            messagebox.showwarning("Aviso", "Informe um peso ou valor válido!", parent=self)
            return

        if self.on_confirmar:
            self.on_confirmar(peso, total)
        self.destroy()
        if hasattr(self.master, "_focar_codigo"):
            self.master._focar_codigo()


class ModalBuscarCliente(ctk.CTkToplevel):
    """
    Modal rápido para busca de cliente por Nome, CPF ou Apelido/Observação.
    Evita travar o PDV com listas gigantescas de milhares de clientes.
    """
    def __init__(self, master, on_selecionado):
        super().__init__(master)
        self.on_selecionado = on_selecionado

        self.title("Buscar Cliente")
        self.geometry("650x420")
        self.resizable(False, False)
        self.grab_set()

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"650x420+{(sw-650)//2}+{(sh-420)//2}")

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        h = ctk.CTkFrame(self, fg_color=COR_PDV, corner_radius=0, height=45)
        h.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(h, text="👤  BUSCAR CLIENTE (Venda a Prazo / Identificação)",
                     font=("Segoe UI", 12, "bold"), text_color="white").pack(side="left", padx=16, pady=10)

        f_busca = ctk.CTkFrame(self, fg_color="#f0f4f8", corner_radius=6)
        f_busca.grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 6))
        f_busca.grid_columnconfigure(0, weight=1)

        self.ent_busca = ctk.CTkEntry(f_busca, placeholder_text="Digite o nome, CPF ou apelido do cliente...", height=36)
        self.ent_busca.grid(row=0, column=0, padx=10, pady=8, sticky="ew")
        self.ent_busca.bind("<KeyRelease>", lambda e: self._filtrar())
        self.ent_busca.bind("<Return>", lambda e: self._confirmar())

        f_tv = ctk.CTkFrame(self, fg_color="transparent")
        f_tv.grid(row=2, column=0, sticky="nsew", padx=16, pady=6)
        f_tv.grid_columnconfigure(0, weight=1)
        f_tv.grid_rowconfigure(0, weight=1)

        cols = ("ID", "Nome do Cliente", "CPF/CNPJ", "Cidade", "Detalhes")
        self.tv = ttk.Treeview(f_tv, columns=cols, show="headings", selectmode="browse", style="SAC.Treeview")
        for c in cols: self.tv.heading(c, text=c)

        self.tv.column("ID",              width=50,  anchor="center")
        self.tv.column("Nome do Cliente", width=240)
        self.tv.column("CPF/CNPJ",        width=110, anchor="center")
        self.tv.column("Cidade",          width=100)
        self.tv.column("Detalhes",        width=130)

        self.tv.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(f_tv, orient="vertical", command=self.tv.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tv.configure(yscrollcommand=sb.set)

        self.tv.bind("<Double-1>", lambda e: self._confirmar())
        self.bind("<Escape>", lambda e: self.destroy())

        bot = ctk.CTkFrame(self, fg_color="transparent", height=45)
        bot.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))

        ctk.CTkLabel(bot, text="[Enter] ou Duplo Clique para selecionar | [Esc] Fechar",
                     font=("Segoe UI", 10), text_color="gray40").pack(side="left")

        ctk.CTkButton(bot, text="✔ Selecionar", font=("Segoe UI", 12, "bold"), fg_color=COR_PDV,
                      width=120, height=36, command=self._confirmar).pack(side="right", padx=4)
        ctk.CTkButton(bot, text="Cancelar", fg_color="gray40", width=80, height=36,
                      command=self.destroy).pack(side="right", padx=4)

        self.after(100, lambda: self.ent_busca.focus())
        self._filtrar()

    def _filtrar(self):
        termo = self.ent_busca.get().strip()
        for r in self.tv.get_children(): self.tv.delete(r)

        q = db_session.query(Cliente).filter(Cliente.ativo == True)
        if termo:
            q = q.filter(
                (Cliente.nome.ilike(f"%{termo}%")) |
                (Cliente.apelido.ilike(f"%{termo}%")) |
                (Cliente.cpf_cnpj.ilike(f"%{termo}%")) |
                (Cliente.observacao.ilike(f"%{termo}%"))
            )
        clis = q.order_by(Cliente.nome).limit(40).all()

        self._mapa = {}
        for c in clis:
            self._mapa[str(c.id)] = c
            self.tv.insert("", "end", iid=str(c.id), values=(
                c.id, c.nome, c.apelido or "-", c.cpf_cnpj or "-", c.cidade or "QUIXABA", c.observacao or ""
            ))

        if clis:
            primeiro = str(clis[0].id)
            self.tv.selection_set(primeiro)
            self.tv.focus(primeiro)

    def _confirmar(self):
        sel = self.tv.selection()
        if not sel: return
        c = self._mapa.get(sel[0])
        if c and self.on_selecionado:
            self.on_selecionado(c)
        self.destroy()
        if hasattr(self.master, "_focar_codigo"):
            self.master._focar_codigo()


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
        emitir_comprovante(self.venda, self.itens, operador=self.operador, abrir_visualizacao=False)
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
        self._focar_codigo()

    def _focar_codigo(self):
        """Garante que o campo de busca de produto receba o foco e o cursor."""
        try:
            self.after(50, lambda: self.ent_codigo.focus_set())
        except Exception:
            pass

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

        ctk.CTkLabel(form_item, text="Qtd / Peso:", font=("Segoe UI", 11, "bold")).grid(row=0, column=2, padx=5, pady=8, sticky="w")
        self.ent_qtd = ctk.CTkEntry(form_item, width=85, height=34, placeholder_text="Ex: 1 ou $13")
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
        ctk.CTkLabel(cli_box, text="Cliente da Venda:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(6, 2))

        box_btn_cli = ctk.CTkFrame(cli_box, fg_color="transparent")
        box_btn_cli.pack(fill="x", padx=10, pady=(0, 8))
        box_btn_cli.grid_columnconfigure(0, weight=1)

        self.lbl_cliente_nome = ctk.CTkLabel(box_btn_cli, text="Consumidor Final", font=("Segoe UI", 12, "bold"),
                                             anchor="w", text_color="#1e2a3a")
        self.lbl_cliente_nome.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.btn_buscar_cli = ctk.CTkButton(box_btn_cli, text="🔍 Buscar", width=75, height=30,
                                            font=("Segoe UI", 11, "bold"), fg_color=COR_PDV,
                                            command=self._abrir_busca_cliente)
        self.btn_buscar_cli.grid(row=0, column=1, padx=(0, 4))

        self.btn_remover_cli = ctk.CTkButton(box_btn_cli, text="✕", width=30, height=30,
                                             font=("Segoe UI", 11, "bold"), fg_color="gray45",
                                             hover_color="#c62828", command=self._limpar_cliente)
        self.btn_remover_cli.grid(row=0, column=2)

        card_total = ctk.CTkFrame(col_dir, fg_color=COR_DESTAQUE, corner_radius=8)
        card_total.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(card_total, text="TOTAL A PAGAR", font=("Segoe UI", 12), text_color="#80cbc4").pack(pady=(10, 2))
        self.lbl_total = ctk.CTkLabel(card_total, text="R$ 0,00", font=("Segoe UI", 32, "bold"), text_color="white")
        self.lbl_total.pack(pady=(0, 10))

        pgto_box = ctk.CTkFrame(col_dir, fg_color="transparent")
        pgto_box.pack(fill="x", padx=14, pady=4)
        pgto_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(pgto_box, text="Forma de Pgto:", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w", pady=4)
        self.combo_pgto = ctk.CTkComboBox(pgto_box, values=["DINHEIRO", "PIX", "CARTAO DEBITO", "CARTAO CREDITO", "A PRAZO (FIADO)"],
                                          command=self._on_trocar_forma_pgto)
        self.combo_pgto.set("DINHEIRO")
        self.combo_pgto.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)

        ctk.CTkLabel(pgto_box, text="Desconto (%):", font=("Segoe UI", 11)).grid(row=1, column=0, sticky="w", pady=4)
        self.ent_desc = ctk.CTkEntry(pgto_box, placeholder_text="0%")
        self.ent_desc.insert(0, "0")
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

    def _on_trocar_forma_pgto(self, escolha):
        if "A PRAZO" in escolha:
            self.ent_recebido.delete(0, "end")
            self.lbl_troco.configure(text="A Prazo: R$ 0,00 recebido")
        else:
            self._atualizar_troco()

    def _abrir_busca_cliente(self):
        ModalBuscarCliente(self, on_selecionado=self._definir_cliente)

    def _definir_cliente(self, cliente):
        self.cliente_selecionado = cliente
        txt_cli = f"{cliente.id} - {cliente.nome}" + (f" ({cliente.apelido})" if cliente.apelido else "")
        self.lbl_cliente_nome.configure(text=txt_cli)
        self._focar_codigo()

    def _limpar_cliente(self):
        self.cliente_selecionado = None
        self.lbl_cliente_nome.configure(text="Consumidor Final")
        self._focar_codigo()

    def _adicionar_item(self):
        termo = self.ent_codigo.get().strip()
        if not termo: return

        qtd_raw = self.ent_qtd.get().strip()

        # 1. Se for código de barras exato
        prod_barras = db_session.query(Produto).filter(
            Produto.ativo == True,
            Produto.codigo_barras == termo
        ).first()

        if prod_barras:
            self._processar_e_inserir(prod_barras, qtd_raw)
            return

        # 2. Se for ID exato
        if termo.isdigit():
            prod_id = db_session.query(Produto).filter(
                Produto.ativo == True,
                Produto.id == int(termo)
            ).first()
            if prod_id:
                self._processar_e_inserir(prod_id, qtd_raw)
                return

        # 3. Busca por nome/descrição
        prods = db_session.query(Produto).filter(
            Produto.ativo == True,
            Produto.descricao.ilike(f"%{termo}%")
        ).limit(50).all()

        if not prods:
            messagebox.showwarning("Não Encontrado", f"Produto '{termo}' não localizado!")
            return

        if len(prods) == 1:
            self._processar_e_inserir(prods[0], qtd_raw)
        else:
            # Se houver mais de um produto com nome parecido, abre modal para o usuário escolher o correto
            ModalSelecionarProduto(self, produtos=prods,
                                   on_selecionado=lambda p_sel: self._processar_e_inserir(p_sel, qtd_raw))

    def _processar_e_inserir(self, prod, qtd_raw):
        """
        Se o produto for vendido por KG (ou se tiver indicação de peso/valor),
        abre o mini-quadro interativo de pesagem/cálculo em tempo real!
        Se for produto unitário comum, insere direto.
        """
        unidade_limpa = (prod.unidade or "").upper().strip()
        eh_kg = unidade_limpa in ["KG", "QUILO", "KILO", "G", "GR", "GRAMA"]

        # Se o operador já digitou com cifrão (ex: $13)
        if "$" in qtd_raw or "R$" in qtd_raw.upper():
            qtd_limpa = qtd_raw.replace("R$", "").replace("r$", "").replace("$", "").replace(" ", "")
            try: val_reais = float(qtd_limpa.replace(",", "."))
            except: val_reais = 0.0
            if val_reais > 0 and prod.preco_venda:
                peso_calc = round(val_reais / prod.preco_venda, 3)
                self._inserir_no_carrinho(prod, peso_calc, val_reais)
                return

        # Se for produto por quilo e não foi especificado um peso prévio diferente de 1
        if eh_kg:
            ModalPesagemProduto(
                self, produto=prod,
                on_confirmar=lambda peso, total: self._inserir_no_carrinho(prod, peso, total)
            )
            return

        # Produto normal por unidade
        try:
            num = float(qtd_raw.replace(",", "."))
            if num <= 0: num = 1.0
        except:
            num = 1.0

        total_item = num * (prod.preco_venda or 0.0)
        self._inserir_no_carrinho(prod, num, total_item)

    def _inserir_no_carrinho(self, prod, qtd, total_item=None):
        if total_item is None:
            total_item = qtd * (prod.preco_venda or 0.0)

        idx = len(self.carrinho) + 1
        item = {
            "num": idx, "produto_id": prod.id, "descricao": prod.descricao,
            "qtd": qtd, "preco": prod.preco_venda, "total": total_item
        }
        self.carrinho.append(item)

        # Formata quantidade (se for fracionado tipo 1.625 kg mostra até 3 decimais, se for inteiro mostra 2)
        qtd_str = f"{qtd:.3f}" if (qtd % 1 != 0 and len(str(qtd).split('.')[-1]) > 2) else f"{qtd:.2f}"

        self.tv.insert("", "end", iid=str(idx),
                       values=(idx, prod.id, prod.descricao, qtd_str,
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
        self._focar_codigo()

        # Atalhos de conveniência do operador:
        # F2 ou Escape: foca imediatamente no campo de busca/código
        self.bind("<F2>", lambda e: self._focar_codigo())
        self.bind("<Escape>", lambda e: self._focar_codigo())
        self.tv.bind("<Delete>", lambda e: self._remover_item())

    def _calcular_desconto_valor(self, subtotal):
        try:
            desc_porc = float(self.ent_desc.get().replace(",", "."))
            if desc_porc < 0: desc_porc = 0.0
            if desc_porc > 100: desc_porc = 100.0
        except:
            desc_porc = 0.0
        return (subtotal * desc_porc) / 100.0

    def _atualizar_totais(self):
        subtotal = sum(i["total"] for i in self.carrinho)
        desc_reais = self._calcular_desconto_valor(subtotal)
        total = max(0.0, subtotal - desc_reais)
        self.lbl_total.configure(text=f"R$ {total:.2f}")
        self._atualizar_troco()

    def _atualizar_troco(self):
        subtotal = sum(i["total"] for i in self.carrinho)
        desc_reais = self._calcular_desconto_valor(subtotal)
        total = max(0.0, subtotal - desc_reais)
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
        cli_id = self.cliente_selecionado.id if self.cliente_selecionado else None

        if "A PRAZO" in forma and not cli_id:
            messagebox.showerror("Atenção", "Para realizar venda A PRAZO (FIADO), clique em 'Buscar' e selecione um Cliente cadastrado!", parent=self)
            return

        subtotal = sum(i["total"] for i in self.carrinho)
        desc_reais = self._calcular_desconto_valor(subtotal)
        total = max(0.0, subtotal - desc_reais)

        # Se for VENDA A PRAZO (FIADO), a dívida vai 100% integral como PENDENTE
        # O valor recebido no ato só é considerado se o operador tiver digitado expressamente uma entrada parcial menor que o total
        eh_a_prazo = "A PRAZO" in forma
        if eh_a_prazo:
            try:
                rec_val = float(self.ent_recebido.get().strip().replace(",", "."))
                # Se digitou exatamente o total ou mais, num fiado isso é engano de digitação: entrada deve ser 0
                if rec_val >= total:
                    rec = 0.0
                else:
                    rec = max(0.0, rec_val)
            except:
                rec = 0.0
            troco = 0.0
        else:
            try: rec = float(self.ent_recebido.get().replace(",", "."))
            except: rec = total
            troco = max(0.0, rec - total)

        ultima = db_session.query(Venda).order_by(Venda.id.desc()).first()
        proximo_num = (ultima.numero + 1) if ultima and ultima.numero else 1

        try:
            nova_venda = Venda(
                numero=proximo_num,
                data=datetime.now(),
                cliente_id=cli_id,
                usuario_id=self.usuario.id if self.usuario else None,
                subtotal=subtotal,
                desconto=desc_reais,
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

            # SE FOR VENDA A PRAZO: Soma na conta aberta do cliente (ou cria uma se não houver)
            if eh_a_prazo:
                saldo_adicionar = max(0.0, total - rec)

                # Busca se o cliente já possui conta em aberto (PENDENTE ou PARCIAL)
                conta_existente = db_session.query(ContaReceber).filter(
                    ContaReceber.cliente_id == cli_id,
                    ContaReceber.status.in_(["PENDENTE", "PARCIAL"])
                ).order_by(ContaReceber.id.desc()).first()

                if conta_existente:
                    # Acumula na conta existente do cliente
                    conta_existente.valor_total = (conta_existente.valor_total or 0.0) + total
                    conta_existente.valor_pago  = (conta_existente.valor_pago or 0.0) + rec
                    conta_existente.saldo_devedor = (conta_existente.saldo_devedor or 0.0) + saldo_adicionar
                    conta_existente.status = "PARCIAL" if conta_existente.valor_pago > 0 else "PENDENTE"
                    conta_existente.venda_id = nova_venda.id
                    # Anexa o histórico da nova venda na descrição
                    desc_venda = f"Venda #{nova_venda.numero:06d}"
                    if conta_existente.descricao:
                        if desc_venda not in conta_existente.descricao:
                            conta_existente.descricao = f"{conta_existente.descricao}, {desc_venda}"
                    else:
                        conta_existente.descricao = f"Venda a Prazo #{nova_venda.numero:06d}"
                else:
                    # Se não tem nenhuma conta aberta, cria a conta corrente do cliente
                    st_conta = "PARCIAL" if (0 < rec < total) else "PENDENTE"
                    nova_conta = ContaReceber(
                        cliente_id=cli_id,
                        venda_id=nova_venda.id,
                        data_emissao=datetime.now(),
                        valor_total=total,
                        valor_pago=rec,
                        saldo_devedor=saldo_adicionar,
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
        self.ent_desc.delete(0, "end"); self.ent_desc.insert(0, "0")
        self.ent_recebido.delete(0, "end")
        self.lbl_total.configure(text="R$ 0,00")
        self.lbl_troco.configure(text="Troco: R$ 0,00")
        self._limpar_cliente()
        self.combo_pgto.set("DINHEIRO")
        self._focar_codigo()
