"""
Módulo de Verificação de Licença e Validade (Xenos PDV).
Gerencia a expiração mensal/anual e previne adulteração de relógio do Windows.
"""
import hmac
import hashlib
import json
import base64
import os
from datetime import datetime, date
from core.caminhos import obter_caminho_dados

# Chave secreta de assinatura digital (conhecida apenas pelo Xenos PDV e pelo gerador)
SECRET_KEY = b"XENOS-PDV-SISTEMA-COMERCIAL-2026-CHAVE-MESTRA-ASSINATURA"

ARQUIVO_LICENCA = obter_caminho_dados("licenca.key")
ARQUIVO_TRAVA_TEMPO = obter_caminho_dados(".sync_time")


def assinar_dados(payload_bytes: bytes) -> str:
    """Gera assinatura HMAC-SHA256 para o payload."""
    return hmac.new(SECRET_KEY, payload_bytes, hashlib.sha256).hexdigest()


def decodificar_chave(chave_str: str):
    """
    Decodifica e valida a chave no formato: BASE64(PAYLOAD).ASSINATURA
    Retorna o dict do payload se válido, ou None se inválido/adulterado.
    """
    try:
        chave_str = chave_str.strip().replace(" ", "").replace("\n", "")
        partes = chave_str.split(".")
        if len(partes) != 2:
            return None

        payload_b64, assinatura_fornecida = partes
        payload_bytes = base64.b64decode(payload_b64.encode("utf-8"))

        # Validação da assinatura digital
        assinatura_esperada = assinar_dados(payload_bytes)
        if not hmac.compare_digest(assinatura_fornecida, assinatura_esperada):
            return None

        dados = json.loads(payload_bytes.decode("utf-8"))
        return dados
    except Exception:
        return None


def salvar_chave_ativacao(chave_str: str) -> bool:
    """Valida a chave e salva no arquivo local se for válida."""
    dados = decodificar_chave(chave_str)
    if not dados or "validade" not in dados:
        return False

    os.makedirs(os.path.dirname(ARQUIVO_LICENCA), exist_ok=True)
    with open(ARQUIVO_LICENCA, "w", encoding="utf-8") as f:
        f.write(chave_str.strip())
    # Limpa a trava de tempo ao ativar com sucesso
    if os.path.exists(ARQUIVO_TRAVA_TEMPO):
        try:
            os.remove(ARQUIVO_TRAVA_TEMPO)
        except Exception:
            pass
    return True


def registrar_ultimo_acesso():
    """Grava timestamp para evitar atraso proposital de relógio do Windows."""
    try:
        agora = datetime.now().timestamp()
        os.makedirs(os.path.dirname(ARQUIVO_TRAVA_TEMPO), exist_ok=True)
        with open(ARQUIVO_TRAVA_TEMPO, "w") as f:
            f.write(str(agora))
    except Exception:
        pass


def checar_relogio_adulterado() -> bool:
    """Verifica se o relógio do Windows foi atrasado para tentar burlar a validade."""
    if not os.path.exists(ARQUIVO_TRAVA_TEMPO):
        registrar_ultimo_acesso()
        return False

    try:
        with open(ARQUIVO_TRAVA_TEMPO, "r") as f:
            conteudo = f.read().strip()
            if not conteudo:
                registrar_ultimo_acesso()
                return False
            ultimo_timestamp = float(conteudo)
        agora_timestamp = datetime.now().timestamp()

        # Tolerancia ampla de 24 horas para fuso/mudancas de horario
        if agora_timestamp < (ultimo_timestamp - 86400):
            return True

        registrar_ultimo_acesso()
        return False
    except Exception:
        return False


def verificar_licenca():
    """
    Verifica o estado da licença.
    Retorna: (status: str, dias_restantes: int, mensagem: str, data_validade: str)
    Status possíveis: 'VALIDO', 'EXPIRANDO', 'EXPIRADO', 'SEM_LICENCA', 'RELOGIO_ADULTERADO'
    """
    if checar_relogio_adulterado():
        return "RELOGIO_ADULTERADO", 0, "O relógio do computador foi atrasado! Ajuste a data e hora corretas.", ""

    if not os.path.exists(ARQUIVO_LICENCA):
        return "SEM_LICENCA", 0, "Sistema não ativado. Insira uma chave de liberação.", ""

    try:
        with open(ARQUIVO_LICENCA, "r", encoding="utf-8") as f:
            conteudo = f.read().strip()
    except Exception:
        return "SEM_LICENCA", 0, "Arquivo de licença ilegível.", ""

    dados = decodificar_chave(conteudo)
    if not dados or "validade" not in dados:
        return "SEM_LICENCA", 0, "Chave de licença inválida ou corrompida.", ""

    try:
        data_val = datetime.strptime(dados["validade"], "%Y-%m-%d").date()
    except Exception:
        return "SEM_LICENCA", 0, "Formato de data de validade inválido na chave.", ""

    hoje = date.today()
    dias_restantes = (data_val - hoje).days
    data_formatada = data_val.strftime("%d/%m/%Y")

    if dias_restantes < 0:
        return "EXPIRADO", dias_restantes, f"Sua mensalidade venceu em {data_formatada}. Renove para continuar usando.", data_formatada
    elif dias_restantes <= 5:
        return "EXPIRANDO", dias_restantes, f"Atenção: Sua mensalidade vence em {dias_restantes} dia(s) ({data_formatada}).", data_formatada
    else:
        return "VALIDO", dias_restantes, f"Licença ativa até {data_formatada}.", data_formatada


def obter_nome_empresa_licenca() -> str:
    """
    Retorna o nome do estabelecimento registrado na licença ativa.
    Se não houver licença ou nome registrado, retorna 'XENOS COMERCIO E VAREJO'.
    """
    if not os.path.exists(ARQUIVO_LICENCA):
        return "XENOS COMERCIO E VAREJO"
    try:
        with open(ARQUIVO_LICENCA, "r", encoding="utf-8") as f:
            conteudo = f.read().strip()
        dados = decodificar_chave(conteudo)
        if dados and dados.get("cliente"):
            return dados["cliente"].strip().upper()
    except Exception:
        pass
    return "XENOS COMERCIO E VAREJO"

