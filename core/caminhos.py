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
