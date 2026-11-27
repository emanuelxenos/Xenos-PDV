"""
Centralizador de Caminhos e Pastas do Sistema.
Garante compatibilidade tanto rodando via script Python quanto como .EXE compilado pelo PyInstaller.
"""
import sys
import os

def obter_pasta_raiz() -> str:
    """
    Retorna o diretorio raiz da aplicacao:
    - Se executando como .exe (PyInstaller no-onefile ou onefile): pasta onde o executavel reside.
    - Se executando como script .py: pasta onde main.py reside.
    """
    if getattr(sys, 'frozen', False):
        # Executavel compilado
        return os.path.dirname(sys.executable)
    else:
        # Script normal: C:\Users\...\Xenos_PDV
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def obter_caminho_dados(subcaminho: str = "") -> str:
    """
    Retorna o caminho absoluto para a pasta de dados persistentes do sistema.
    """
    pasta = os.path.join(obter_pasta_raiz(), "dados")
    if subcaminho:
        return os.path.join(pasta, subcaminho)
    return pasta


def obter_caminho_asset(nome_arquivo: str) -> str:
    """
    Retorna o caminho absoluto de um asset (ícone, logo),
    buscando tanto no executável compilado quanto em desenvolvimento.
    """
    # 1. Se estiver rodando como .exe (dist/XenosPDV)
    pasta_raiz = obter_pasta_raiz()
    p_raiz = os.path.join(pasta_raiz, "assets", nome_arquivo)
    if os.path.exists(p_raiz):
        return p_raiz

    # 2. Se estiver empacotado no _internal
    p_internal = os.path.join(pasta_raiz, "_internal", "assets", nome_arquivo)
    if os.path.exists(p_internal):
        return p_internal

    # 3. Se estiver no sys._MEIPASS
    if hasattr(sys, "_MEIPASS"):
        p_meipass = os.path.join(sys._MEIPASS, "assets", nome_arquivo)
        if os.path.exists(p_meipass):
            return p_meipass

    # 4. Fallback relativo ao script
    p_fallback = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", nome_arquivo)
    return p_fallback if os.path.exists(p_fallback) else ""
