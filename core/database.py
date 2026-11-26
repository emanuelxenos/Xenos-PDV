"""
Modelos do banco de dados — SQLite via SQLAlchemy.
Inclui modelo de Contas a Receber (Vendas a Prazo / Fiado e Histórico de Pagamentos).
"""
from sqlalchemy import (create_engine, Column, Integer, String, Float,
                        DateTime, Boolean, Text, ForeignKey)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, scoped_session
from datetime import datetime
import os
from core.caminhos import obter_caminho_dados

DB_PATH = obter_caminho_dados("xenos.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False}
)

SessionFactory = sessionmaker(bind=engine, autoflush=False)
ScopedSession = scoped_session(SessionFactory)
db_session = ScopedSession()

Base = declarative_base()


# ══════════════════════════════════════════════════════
#  MODELOS
# ══════════════════════════════════════════════════════
class Usuario(Base):
    __tablename__ = "usuarios"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    nome       = Column(String(80), nullable=False)
    login      = Column(String(40), unique=True, nullable=False)
    senha_hash = Column(String(128), nullable=False)
    perfil     = Column(String(20), default="operador")
    ativo      = Column(Boolean, default=True)
    criado_em  = Column(DateTime, default=datetime.now)


class MovimentoCaixa(Base):
    __tablename__ = "movimentos_caixa"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    data_hora  = Column(DateTime, default=datetime.now)
    tipo       = Column(String(20), nullable=False)  # SUPRIMENTO | SANGRIA | ABERTURA | RECEBIMENTO_CONTA
    valor      = Column(Float, default=0.0)
    descricao  = Column(String(150))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    usuario    = relationship("Usuario")


class Cliente(Base):
    __tablename__ = "clientes"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    nome           = Column(String(100), nullable=False)
    apelido        = Column(String(100), nullable=True)
    cpf_cnpj       = Column(String(20))
    telefone       = Column(String(20))
    celular        = Column(String(20))
    email          = Column(String(100))
    endereco       = Column(String(150))
    numero         = Column(String(10))
    bairro         = Column(String(60))
    cidade         = Column(String(60))
    estado         = Column(String(2))
    cep            = Column(String(10))
    limite_credito = Column(Float, default=0.0)
    observacao     = Column(Text)
    ativo          = Column(Boolean, default=True)
    criado_em      = Column(DateTime, default=datetime.now)
    vendas         = relationship("Venda", back_populates="cliente")
    contas         = relationship("ContaReceber", back_populates="cliente")


class Fornecedor(Base):
    __tablename__ = "fornecedores"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    nome       = Column(String(100), nullable=False)
    cnpj       = Column(String(20))
    telefone   = Column(String(20))
    email      = Column(String(100))
    contato    = Column(String(60))
    endereco   = Column(String(150))
    cidade     = Column(String(60))
    estado     = Column(String(2))
    observacao = Column(Text)
    ativo      = Column(Boolean, default=True)
    criado_em  = Column(DateTime, default=datetime.now)
    produtos   = relationship("Produto", back_populates="fornecedor")


class Categoria(Base):
    __tablename__ = "categorias"
    id       = Column(Integer, primary_key=True, autoincrement=True)
    nome     = Column(String(60), unique=True, nullable=False)
    produtos = relationship("Produto", back_populates="categoria")


class Produto(Base):
    __tablename__ = "produtos"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    codigo_barras  = Column(String(30))
    descricao      = Column(String(100), nullable=False)
    unidade        = Column(String(5), default="UN")
    preco_venda    = Column(Float, default=0.0)
    preco_compra   = Column(Float, default=0.0)
    margem         = Column(Float, default=0.0)
    estoque        = Column(Float, default=0.0)
    estoque_minimo = Column(Float, default=0.0)
    categoria_id   = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    fornecedor_id  = Column(Integer, ForeignKey("fornecedores.id"), nullable=True)
    ncm            = Column(String(10))
    observacao     = Column(Text)
    ativo          = Column(Boolean, default=True)
    criado_em      = Column(DateTime, default=datetime.now)
    atualizado_em  = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    categoria      = relationship("Categoria", back_populates="produtos")
    fornecedor     = relationship("Fornecedor", back_populates="produtos")
    itens_venda    = relationship("ItemVenda", back_populates="produto")


class Venda(Base):
    __tablename__ = "vendas"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    numero     = Column(Integer, unique=True, nullable=False)
    data       = Column(DateTime, default=datetime.now)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    subtotal   = Column(Float, default=0.0)
    desconto   = Column(Float, default=0.0)
    total      = Column(Float, default=0.0)
    forma_pgto = Column(String(30), default="DINHEIRO")
    valor_pago = Column(Float, default=0.0)
    troco      = Column(Float, default=0.0)
    status     = Column(String(20), default="CONCLUIDA")
    observacao = Column(Text)
    cliente    = relationship("Cliente", back_populates="vendas")
    usuario    = relationship("Usuario")
    itens      = relationship("ItemVenda", back_populates="venda", cascade="all, delete-orphan")
    conta      = relationship("ContaReceber", back_populates="venda", uselist=False)


class ItemVenda(Base):
    __tablename__ = "itens_venda"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    venda_id   = Column(Integer, ForeignKey("vendas.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    descricao  = Column(String(100))
    quantidade = Column(Float, default=1.0)
    preco_unit = Column(Float, default=0.0)
    desconto   = Column(Float, default=0.0)
    total      = Column(Float, default=0.0)
    venda      = relationship("Venda", back_populates="itens")
    produto    = relationship("Produto", back_populates="itens_venda")


class ContaReceber(Base):
    __tablename__ = "contas_receber"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id     = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    venda_id       = Column(Integer, ForeignKey("vendas.id"), nullable=True)
    data_emissao   = Column(DateTime, default=datetime.now)
    data_vencimento= Column(DateTime, nullable=True)
    valor_total    = Column(Float, default=0.0)
    valor_pago     = Column(Float, default=0.0)
    saldo_devedor  = Column(Float, default=0.0)
    status         = Column(String(20), default="PENDENTE")  # PENDENTE | PARCIAL | PAGO
    descricao      = Column(String(150))
    cliente        = relationship("Cliente", back_populates="contas")
    venda          = relationship("Venda", back_populates="conta")
    historico_pagamentos = relationship("HistoricoPagamentoConta", back_populates="conta", cascade="all, delete-orphan")


class HistoricoPagamentoConta(Base):
    __tablename__ = "historico_pagamentos_conta"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    conta_id       = Column(Integer, ForeignKey("contas_receber.id"), nullable=False)
    cliente_id     = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    data_hora      = Column(DateTime, default=datetime.now)
    valor_pago     = Column(Float, nullable=False)
    forma_pgto     = Column(String(30), default="DINHEIRO")
    saldo_anterior = Column(Float, default=0.0)
    saldo_restante = Column(Float, default=0.0)
    usuario_id     = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    pago_por       = Column(String(100), nullable=True)
    observacao     = Column(String(150), nullable=True)

    conta          = relationship("ContaReceber", back_populates="historico_pagamentos")
    cliente        = relationship("Cliente")
    usuario        = relationship("Usuario")


def criar_tabelas():
    Base.metadata.create_all(engine)

def get_session():
    return db_session
