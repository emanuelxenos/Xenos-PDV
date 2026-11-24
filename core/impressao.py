"""
Módulo de Impressão de Cupom / Comprovante Não Fiscal (Impressora Térmica 80mm / 58mm).
Gera arquivo de texto pronto para spooler/porta RAW ou visualização na tela/bloco de notas.
"""
import os
import subprocess
from datetime import datetime

try:
    import win32print
    import win32ui
    TEM_WIN32PRINT = True
except Exception:
    TEM_WIN32PRINT = False


from core.licenca import obter_nome_empresa_licenca


def formatar_cupom(venda, itens, nome_empresa=None, operador="Operador"):
    """
    Gera o layout formatado compacto para bobina térmica (40/48 colunas).
    Sem desperdício de linhas em branco no final.
    """
    if not nome_empresa:
        nome_empresa = obter_nome_empresa_licenca()
    largura = 40
    sep = "=" * largura
    sep_fina = "-" * largura

    linhas = []
    linhas.append(nome_empresa.center(largura))
    linhas.append("COMPROVANTE NAO FISCAL".center(largura))
    linhas.append(sep)
    linhas.append(f"Venda: #{venda.numero:06d}  Data: {venda.data.strftime('%d/%m/%Y %H:%M')}")
    linhas.append(f"Operador: {operador}")
    cli_nome = venda.cliente.nome if venda.cliente else "Consumidor Final"
    linhas.append(f"Cliente : {cli_nome[:30]}")
    linhas.append(sep_fina)
    linhas.append("ITEM DESC             QTD  VL.UN   TOTAL")
    linhas.append(sep_fina)

    for i, it in enumerate(itens, 1):
        desc = it.descricao[:20].ljust(20)
        linhas.append(f"{i:02d} {desc}")
        qtd_str = f"{it.quantidade:.2f}"
        un_str  = f"{it.preco_unit:.2f}"
        tot_str = f"R$ {it.total:.2f}"
        linhas.append(f"    {qtd_str} x R$ {un_str}".ljust(25) + tot_str.rjust(15))

    linhas.append(sep_fina)
    linhas.append("Subtotal:".ljust(25) + f"R$ {venda.subtotal:.2f}".rjust(15))
    if venda.desconto and venda.desconto > 0:
        linhas.append("Desconto:".ljust(25) + f"- R$ {venda.desconto:.2f}".rjust(15))
    linhas.append(sep)
    linhas.append("TOTAL A PAGAR:".ljust(22) + f"R$ {venda.total:.2f}".rjust(18))
    linhas.append(sep)
    linhas.append(f"Forma Pgto: {venda.forma_pgto}")
    linhas.append("Valor Pago:".ljust(25) + f"R$ {venda.valor_pago:.2f}".rjust(15))
    if venda.troco and venda.troco > 0:
        linhas.append("Troco:".ljust(25) + f"R$ {venda.troco:.2f}".rjust(15))
    linhas.append(sep_fina)
    linhas.append("Obrigado pela preferencia!".center(largura))
    # Espaçamento ideal para a serrilha da impressora térmica (permite rasgar com total folga)
    linhas.append("\n\n\n\n\n\n\n\n")

    return "\n".join(linhas)


def imprimir_direto_na_impressora(texto_para_imprimir, nome_impressora=None):
    """
    Envia o texto direto para a impressora térmica via spooler do Windows (RAW).
    Não abre Bloco de Notas nem Notepad!
    """
    if not TEM_WIN32PRINT:
        return False

    try:
        if not nome_impressora:
            nome_impressora = win32print.GetDefaultPrinter()

        hprinter = win32print.OpenPrinter(nome_impressora)
        try:
            hjob = win32print.StartDocPrinter(hprinter, 1, ("Comprovante PDV", None, "RAW"))
            try:
                win32print.StartPagePrinter(hprinter)
                # Envia em RAW codificado em latin1 ou cp850 para suportar acentos na térmica
                raw_data = texto_para_imprimir.encode("cp850", errors="replace")
                win32print.WritePrinter(hprinter, raw_data)
                win32print.EndPagePrinter(hprinter)
            finally:
                win32print.EndDocPrinter(hprinter)
        finally:
            win32print.ClosePrinter(hprinter)
        return True
    except Exception as ex:
        print(f"Erro ao imprimir direto no spooler: {ex}")
        return False


def emitir_comprovante(venda, itens, operador="Operador", abrir_visualizacao=False):
    """
    Salva o comprovante em TXT e tenta imprimir direto na impressora térmica sem abrir Notepad.
    Se não houver impressora configurada e abrir_visualizacao for True, abre o visualizador.
    """
    cupom_txt = formatar_cupom(venda, itens, operador=operador)

    from core.caminhos import obter_caminho_dados
    pasta_cupons = obter_caminho_dados("cupons")
    os.makedirs(pasta_cupons, exist_ok=True)

    caminho_arquivo = os.path.join(pasta_cupons, f"cupom_venda_{venda.numero:06d}.txt")

    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(cupom_txt)

    # 1. Tentar imprimir direto no spooler da impressora padrão do Windows
    sucesso_direto = imprimir_direto_na_impressora(cupom_txt)

    # 2. Se a impressão direta falhar (ex: sem impressora física ou erro de driver) e foi solicitado abrir
    if not sucesso_direto and abrir_visualizacao:
        try:
            os.startfile(caminho_arquivo)
        except Exception:
            pass

    return sucesso_direto


def formatar_recibo_pagamento(conta, valor_pago, forma_pgto="DINHEIRO", operador="Operador", nome_empresa=None):
    """
    Formata recibo não fiscal compacto para bobina térmica.
    """
    if not nome_empresa:
        nome_empresa = obter_nome_empresa_licenca()
    largura = 40
    sep = "=" * largura
    sep_fina = "-" * largura

    linhas = []
    linhas.append(nome_empresa.center(largura))
    linhas.append("RECIBO DE PAGAMENTO / ABATIMENTO".center(largura))
    linhas.append(sep)
    linhas.append(f"Recibo: #{conta.id:06d}  Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    linhas.append(f"Operador: {operador}")
    cli_nome = conta.cliente.nome if conta.cliente else "Consumidor"
    linhas.append(f"Cliente : {cli_nome[:30]}")
    if conta.cliente and conta.cliente.cpf_cnpj:
        linhas.append(f"CPF/CNPJ: {conta.cliente.cpf_cnpj}")
    linhas.append(sep_fina)

    linhas.append("Total Divida:".ljust(22) + f"R$ {conta.valor_total:.2f}".rjust(18))
    linhas.append("VALOR PAGO:".ljust(22) + f"R$ {valor_pago:.2f}".rjust(18))
    linhas.append(f"Forma Pgto: {forma_pgto}")
    linhas.append(sep_fina)

    saldo_atual = max(0.0, conta.saldo_devedor)
    linhas.append("SALDO RESTANTE:".ljust(22) + f"R$ {saldo_atual:.2f}".rjust(18))
    st = "QUITADO" if saldo_atual <= 0.001 else "PAGAMENTO PARCIAL"
    linhas.append(f"Situacao: {st}".center(largura))
    linhas.append(sep)
    linhas.append("\n")
    linhas.append("______________________________________".center(largura))
    linhas.append("Assinatura do Recebedor".center(largura))
    linhas.append("Obrigado pela pontualidade!".center(largura))
    # Espaçamento ideal para a serrilha da impressora térmica
    linhas.append("\n\n\n\n\n\n\n\n")

    return "\n".join(linhas)


def emitir_recibo_pagamento(conta, valor_pago, forma_pgto="DINHEIRO", operador="Operador", abrir_visualizacao=False):
    """
    Salva o recibo e imprime direto no spooler da impressora térmica sem abrir Notepad.
    """
    recibo_txt = formatar_recibo_pagamento(conta, valor_pago, forma_pgto=forma_pgto, operador=operador)
    from core.caminhos import obter_caminho_dados
    pasta_cupons = obter_caminho_dados("cupons")
    os.makedirs(pasta_cupons, exist_ok=True)

    agora_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_arquivo = os.path.join(pasta_cupons, f"recibo_abate_conta_{conta.id:04d}_{agora_str}.txt")

    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(recibo_txt)

    sucesso_direto = imprimir_direto_na_impressora(recibo_txt)
    if not sucesso_direto and abrir_visualizacao:
        try:
            os.startfile(caminho_arquivo)
        except Exception:
            pass

    return sucesso_direto


def formatar_extrato_cliente(cliente, movimentacoes, resumo, nome_empresa=None, operador="Operador"):
    """
    Formata o extrato completo de dívidas e abatimentos do cliente para impressora térmica de 40 colunas.
    movimentacoes: lista de dicts com {'data', 'tipo', 'ref', 'valor', 'saldo_apos'}
    resumo: {'total_compras', 'total_abates', 'saldo_atual'}
    """
    if not nome_empresa:
        nome_empresa = obter_nome_empresa_licenca()
    largura = 40
    sep = "=" * largura
    sep_fina = "-" * largura

    linhas = []
    linhas.append(nome_empresa.center(largura))
    linhas.append("EXTRATO DE CONTA / HISTORICO".center(largura))
    linhas.append("CONTROLE DE DIVIDAS E ABATIMENTOS".center(largura))
    linhas.append(sep)
    linhas.append(f"Emissao : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    linhas.append(f"Operador: {operador}")
    linhas.append(f"Cliente : {cliente.nome[:30]}")
    if cliente.cpf_cnpj:
        linhas.append(f"CPF/CNPJ: {cliente.cpf_cnpj}")
    if cliente.telefone or cliente.celular:
        tel = cliente.celular or cliente.telefone
        linhas.append(f"Telefone: {tel}")
    linhas.append(sep)
    linhas.append("DATA       TIPO         VALOR(R$)  SALDO")
    linhas.append(sep_fina)

    for m in movimentacoes:
        dt_str = m['data'].strftime('%d/%m/%y') if hasattr(m['data'], 'strftime') else str(m['data'])[:8]
        tipo_str = m['tipo'][:11].ljust(11) # ex: COMPRA #123 ou ABATIMENTO
        val_str = f"{m['valor']:.2f}".rjust(8)
        saldo_str = f"{m['saldo_apos']:.2f}".rjust(8)
        # Formato: DD/MM/YY  TIPO-LJUST  VALOR  SALDO
        # 8 + 1 + 11 + 1 + 8 + 1 + 8 = 38 chars
        linhas.append(f"{dt_str} {tipo_str} {val_str} {saldo_str}")
        if m.get('detalhe'):
            linhas.append(f"  {m['detalhe'][:36]}")

    linhas.append(sep_fina)
    linhas.append("RESUMO FINANCEIRO:".center(largura))
    linhas.append("Total Compras a Prazo:".ljust(22) + f"R$ {resumo['total_compras']:.2f}".rjust(18))
    linhas.append("Total Pago/Abatido   :".ljust(22) + f"R$ {resumo['total_abates']:.2f}".rjust(18))
    linhas.append(sep)
    linhas.append("SALDO DEVEDOR ATUAL  :".ljust(22) + f"R$ {resumo['saldo_atual']:.2f}".rjust(18))
    if resumo['saldo_atual'] <= 0.001:
        linhas.append(">>> CONTA 100% QUITADA <<<".center(largura))
    else:
        linhas.append(">>> CONTA PENDENTE <<<".center(largura))
    linhas.append(sep)
    linhas.append("")
    linhas.append("Assinatura do Cliente:".center(largura))
    linhas.append("")
    linhas.append("________________________________________")
    linhas.append(f"{cliente.nome[:38]}".center(largura))
    linhas.append("")
    linhas.append("Controle Interno - Xenos PDV".center(largura))
    # Espaçamento para guilhotina/rasgo do papel
    linhas.append("\n" * 8)

    return "\n".join(linhas)


def emitir_extrato_cliente(cliente, movimentacoes, resumo, operador="Operador", abrir_visualizacao=False):
    """
    Gera e envia para a impressora o extrato do cliente.
    """
    texto = formatar_extrato_cliente(cliente, movimentacoes, resumo, operador=operador)
    imprimir_direto_na_impressora(texto)

    if abrir_visualizacao:
        try:
            import tempfile
            import os
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="latin-1", errors="replace")
            tf.write(texto)
            tf.close()
            os.startfile(tf.name)
        except Exception as e:
            print("Erro ao abrir visualização do extrato:", e)
