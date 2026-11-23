"""
Script de Migração de Dados: SAC Antigo (DBF) -> Xenos PDV (SQLite)
Importa:
1. Clientes (clientes.DBF) -> 1.552 registros
2. Produtos (PRODUTO.DBF) -> 8.368 registros
3. Contas a Receber / Fiado Ativo (SALDO_DEV dos Clientes) -> 362 contas pendentes
"""
import os
import sys
from datetime import datetime
from dbfread import DBF

PASTA_XENOS = r"C:\Users\Emanuel\Desktop\Xenos_PDV"
sys.path.insert(0, PASTA_XENOS)

from core.database import db_session, Cliente, Produto, ContaReceber

PASTA_SAC = r"E:\SAC\dados"

def limpar_str(val):
    if not val:
        return ""
    if isinstance(val, str):
        # Tratar acentos latin1/cp850 comuns em dbf clipper/delphi
        return val.strip()
    return str(val).strip()

def para_float(val, padrao=0.0):
    if val is None:
        return padrao
    try:
        return float(val)
    except Exception:
        return padrao

def migrar_clientes():
    p = os.path.join(PASTA_SAC, "clientes.DBF")
    if not os.path.exists(p):
        print(f"[!] Arquivo nao encontrado: {p}")
        return {}

    table = DBF(p, encoding="latin1", ignore_missing_memofile=True)
    print(f"[*] Importando {len(table)} clientes de clientes.DBF...")

    mapa_clientes = {}  # codigo_antigo -> novo_obj_cliente
    contas_a_criar = []
    inseridos = 0

    for r in table:
        cod_antigo = limpar_str(r.get("CODIGO"))
        nome = limpar_str(r.get("NOME"))
        if not nome:
            continue

        cpf_cnpj = limpar_str(r.get("CPF"))
        tel = limpar_str(r.get("FONE"))
        cel = limpar_str(r.get("CELULAR"))
        ende = limpar_str(r.get("ENDE"))
        cid = limpar_str(r.get("CID"))
        est = limpar_str(r.get("EST"))
        cep = limpar_str(r.get("CEP"))
        bairro = limpar_str(r.get("BAIRRO"))
        limite = para_float(r.get("LIMITE"), 0.0)
        saldo_dev = para_float(r.get("SALDO_DEV"), 0.0)

        obs = []
        vulgo = limpar_str(r.get("VULGO"))
        if vulgo:
            obs.append(f"Apelido: {vulgo}")
        filiacao = limpar_str(r.get("FILIACAO1"))
        if filiacao:
            obs.append(f"Filiacao: {filiacao}")

        novo_cli = Cliente(
            nome=nome,
            cpf_cnpj=cpf_cnpj,
            telefone=tel,
            celular=cel,
            email="",
            endereco=ende,
            numero="",
            bairro=bairro,
            cidade=cid or "QUIXABA",
            estado=est or "PE",
            cep=cep,
            limite_credito=limite,
            observacao=" | ".join(obs),
            ativo=True,
            criado_em=datetime.now()
        )
        db_session.add(novo_cli)
        db_session.flush()  # Para obter o ID gerado

        mapa_clientes[cod_antigo] = novo_cli
        inseridos += 1

        # Se tinha saldo devedor (fiado do sistema antigo), registrar no Contas a Receber
        if saldo_dev > 0.0:
            contas_a_criar.append(ContaReceber(
                cliente_id=novo_cli.id,
                venda_id=None,
                data_emissao=datetime.now(),
                valor_total=saldo_dev,
                valor_pago=0.0,
                saldo_devedor=saldo_dev,
                status="PENDENTE",
                descricao=f"Saldo Devedor / Fiado Migrado do SAC Antigo (Cod. {cod_antigo})"
            ))

    if contas_a_criar:
        db_session.add_all(contas_a_criar)

    db_session.commit()
    print(f"[OK] {inseridos} clientes importados!")
    print(f"[OK] {len(contas_a_criar)} contas a receber (fiados pendentes) migradas!")
    return mapa_clientes

def migrar_produtos():
    p = os.path.join(PASTA_SAC, "PRODUTO.DBF")
    if not os.path.exists(p):
        print(f"[!] Arquivo nao encontrado: {p}")
        return

    table = DBF(p, encoding="latin1", ignore_missing_memofile=True)
    print(f"[*] Importando {len(table)} produtos de PRODUTO.DBF...")

    inseridos = 0
    batch = []

    for r in table:
        descr = limpar_str(r.get("DESCR"))
        if not descr:
            continue

        raw_cod = r.get("CODIGO")
        cod_barras = ""
        if raw_cod:
            cod_barras = str(raw_cod).strip()
            # Remover notacao cientifica se tiver
            if cod_barras.endswith(".0"):
                cod_barras = cod_barras[:-2]

        preco_venda = para_float(r.get("PRECO"), 0.0)
        preco_compra = para_float(r.get("PRCOMPRA"), 0.0)
        estoque = para_float(r.get("QFISICA"), 0.0)
        estmin = para_float(r.get("ESTMIN"), 0.0)
        unidade = limpar_str(r.get("UNIDADE")) or "UN"
        marca = limpar_str(r.get("MARCA"))

        obs = []
        if marca:
            obs.append(f"Marca: {marca}")
        ref = limpar_str(r.get("REFERENCIA"))
        if ref:
            obs.append(f"Ref: {ref}")

        prod = Produto(
            codigo_barras=cod_barras,
            descricao=descr,
            unidade=unidade[:10],
            preco_venda=preco_venda,
            preco_compra=preco_compra,
            margem=0.0,
            estoque=estoque,
            estoque_minimo=estmin,
            observacao=" | ".join(obs),
            ativo=True,
            criado_em=datetime.now()
        )
        batch.append(prod)
        inseridos += 1

        if len(batch) >= 500:
            db_session.add_all(batch)
            db_session.commit()
            batch = []

    if batch:
        db_session.add_all(batch)
        db_session.commit()

    print(f"[OK] {inseridos} produtos importados com sucesso!")

if __name__ == "__main__":
    print("=== INICIANDO MIGRACAO DE DADOS SAC -> XENOS PDV ===")
    migrar_clientes()
    migrar_produtos()
    print("=== MIGRACAO CONCLUIDA COM SUCESSO! ===")
