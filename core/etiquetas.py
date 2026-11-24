"""
Módulo de Geração de Etiquetas em PDF para Impressão (Folha A4 e Bobinas Térmicas).
Gera código de barras visual e organiza etiquetas com Nome, Código/ID, Preço e Unidade.
"""
import os
import subprocess
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.barcode import code128

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_ETIQUETAS = os.path.join(BASE_DIR, "dados", "etiquetas")


def gerar_pdf_etiquetas(produtos_qtd: list, modelo="A4_3X10", parent_window=None) -> str:
    """
    Gera um arquivo PDF formatado com as etiquetas solicitadas e abre para impressão.
    produtos_qtd: lista de tuplas -> [(produto_obj, quantidade_etiquetas), ...]
    modelo: 'A4_3X10' (folha de 30 etiquetas A4 padrão tipo Pimaco)
    """
    os.makedirs(PASTA_ETIQUETAS, exist_ok=True)

    # Limpeza preventiva: remove PDFs de etiquetas gerados anteriormente para não acumular lixo
    try:
        for f in os.listdir(PASTA_ETIQUETAS):
            if f.lower().startswith("etiquetas_") and f.lower().endswith(".pdf"):
                caminho_antigo = os.path.join(PASTA_ETIQUETAS, f)
                try:
                    os.remove(caminho_antigo)
                except Exception:
                    pass  # Se estiver aberto em algum visualizador de PDF, ignora
    except Exception:
        pass

    caminho_pdf = os.path.join(PASTA_ETIQUETAS, f"etiquetas_{os.getpid()}.pdf")

    # Margens estreitas para caber na folha A4 (3 colunas x 10 linhas)
    doc = SimpleDocTemplate(
        caminho_pdf,
        pagesize=A4,
        leftMargin=15,
        rightMargin=15,
        topMargin=15,
        bottomMargin=15
    )

    styles = getSampleStyleSheet()
    style_nome = ParagraphStyle(
        'EtiquetaNome',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=9,
        alignment=1  # Centralizado
    )
    style_preco = ParagraphStyle(
        'EtiquetaPreco',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=13,
        alignment=1,
        textColor=colors.black
    )
    style_sub = ParagraphStyle(
        'EtiquetaSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=8,
        alignment=1,
        textColor=colors.dimgray
    )

    # Descompacta a lista com a quantidade de cada produto
    celulas_etiquetas = []
    for prod, qtd in produtos_qtd:
        valor_barras = str(prod.codigo_barras if prod.codigo_barras else f"{prod.id:06d}")
        
        # Gera o código de barras vetorial
        try:
            barcode = code128.Code128(valor_barras, barWidth=1.0, barHeight=18)
        except Exception:
            barcode = Paragraph(f"[{valor_barras}]", style_sub)

        # Monta o conteúdo interno de uma etiqueta
        conteudo_etiqueta = [
            Paragraph(f"<b>{prod.descricao[:28]}</b>", style_nome),
            Spacer(1, 2),
            Paragraph(f"R$ {prod.preco_venda:.2f} <font size=8>/{prod.unidade}</font>", style_preco),
            Spacer(1, 1),
            barcode,
            Paragraph(f"Cód: {valor_barras}", style_sub)
        ]
        
        for _ in range(int(qtd)):
            celulas_etiquetas.append(conteudo_etiqueta)

    if not celulas_etiquetas:
        return None

    # Organiza em 3 colunas por linha (Padrão 3x10 em folha A4)
    num_colunas = 3
    linhas_tabela = []
    linha_atual = []

    for etiq in celulas_etiquetas:
        linha_atual.append(etiq)
        if len(linha_atual) == num_colunas:
            linhas_tabela.append(linha_atual)
            linha_atual = []

    # Completa a última linha se sobrar célula vazia
    if linha_atual:
        while len(linha_atual) < num_colunas:
            linha_atual.append("")
        linhas_tabela.append(linha_atual)

    # Tabela com as dimensões aproximadas das etiquetas (largura ~185pt cada)
    tabela = Table(linhas_tabela, colWidths=[188, 188, 188], rowHeights=[78] * len(linhas_tabela))
    tabela.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))

    doc.build([tabela])

    # Abre o PDF para impressão imediata no leitor do Windows
    try:
        os.startfile(caminho_pdf)
    except Exception:
        pass

    return caminho_pdf
