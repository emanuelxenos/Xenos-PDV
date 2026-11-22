"""
Módulo de Impressão de Cupom / Comprovante Não Fiscal (Impressora Térmica 80mm / 58mm).
Gera arquivo de texto pronto para spooler/porta RAW ou visualização na tela/bloco de notas.
"""
import os
import subprocess
from datetime import datetime

def formatar_cupom(venda, itens, nome_empresa="XENOS COMERCIO E VAREJO", operador="Operador"):
    """
    Gera o layout formatado padrão de bobina térmica (48 colunas - 80mm / 58mm).
    """
    largura = 48
    sep = "=" * largura
    sep_fina = "-" * largura

    linhas = []
    linhas.append(nome_empresa.center(largura))
    linhas.append("COMPROVANTE NAO FISCAL".center(largura))
    linhas.append(sep)
    linhas.append(f"Venda No: {venda.numero:06d}".ljust(24) + f"Data: {venda.data.strftime('%d/%m/%Y %H:%M')}".rjust(24))
    linhas.append(f"Operador: {operador}".ljust(largura))
    if venda.cliente:
        linhas.append(f"Cliente : {venda.cliente.nome}".ljust(largura))
    else:
        linhas.append("Cliente : Consumidor Final".ljust(largura))
    linhas.append(sep_fina)
    linhas.append("ITEM COD  DESCRICAO           QTD   VL.UN   TOTAL")
    linhas.append(sep_fina)

    for i, it in enumerate(itens, 1):
        # Linha 1: Item + Descrição
        desc = it.descricao[:28].ljust(28)
        linhas.append(f"{i:02d}  {desc}")
        # Linha 2: Qtd x Preço Unit = Total
        qtd_str = f"{it.quantidade:.2f}".rjust(6)
        un_str  = f"R$ {it.preco_unit:.2f}".rjust(9)
        tot_str = f"R$ {it.total:.2f}".rjust(10)
        linhas.append(f"      {qtd_str} x {un_str}        {tot_str}".rjust(largura))

    linhas.append(sep_fina)
    linhas.append(f"Subtotal:".ljust(34) + f"R$ {venda.subtotal:.2f}".rjust(14))
    if venda.desconto and venda.desconto > 0:
        linhas.append(f"Desconto:".ljust(34) + f"- R$ {venda.desconto:.2f}".rjust(14))
    linhas.append(sep)
    linhas.append(f"TOTAL A PAGAR:".ljust(30) + f"R$ {venda.total:.2f}".rjust(18))
    linhas.append(sep)
    linhas.append(f"Forma Pgto: {venda.forma_pgto}".ljust(largura))
    linhas.append(f"Valor Pago:".ljust(34) + f"R$ {venda.valor_pago:.2f}".rjust(14))
    if venda.troco and venda.troco > 0:
        linhas.append(f"Troco:".ljust(34) + f"R$ {venda.troco:.2f}".rjust(14))
    linhas.append(sep_fina)
    linhas.append("Obrigado pela preferencia!".center(largura))
    linhas.append("Volte sempre!".center(largura))
    linhas.append("\n\n\n\n\n")  # Avanço de papel para guilhotina/corte

    return "\n".join(linhas)


def emitir_comprovante(venda, itens, operador="Operador", abrir_visualizacao=True):
    """
    Salva o comprovante em pasta local e abre para visualização/impressão imediata.
    """
    cupom_txt = formatar_cupom(venda, itens, operador=operador)
    
    pasta_cupons = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dados", "cupons")
    os.makedirs(pasta_cupons, exist_ok=True)
    
    caminho_arquivo = os.path.join(pasta_cupons, f"cupom_venda_{venda.numero:06d}.txt")
    
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(cupom_txt)
        
    if abrir_visualizacao:
        try:
            # Abre o arquivo no visualizador do Windows (permite clicar Ctrl+P e imprimir direto na térmica instalada)
            os.startfile(caminho_arquivo)
        except Exception:
            pass
            
    return caminho_arquivo
