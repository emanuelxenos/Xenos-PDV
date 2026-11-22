"""
GERADOR DE CHAVES DE ATIVAÇÃO — XENOS PDV
Execute este script na sua máquina de desenvolvedor para gerar chaves de mensalidade ou anuais para seus clientes.
"""
import hmac
import hashlib
import json
import base64
from datetime import datetime, date, timedelta

SECRET_KEY = b"XENOS-PDV-SISTEMA-COMERCIAL-2026-CHAVE-MESTRA-ASSINATURA"


def gerar_chave(cliente: str, dias_validade: int = 30) -> str:
    """
    Gera uma chave criptografada para o cliente com data de validade futura.
    """
    hoje = date.today()
    data_limite = hoje + timedelta(days=dias_validade)

    payload = {
        "cliente": cliente.strip(),
        "gerado_em": hoje.strftime("%Y-%m-%d"),
        "validade": data_limite.strftime("%Y-%m-%d"),
        "sistema": "Xenos_PDV"
    }

    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_bytes = payload_json.encode("utf-8")
    payload_b64 = base64.b64encode(payload_bytes).decode("utf-8")

    # Assinatura HMAC-SHA256
    assinatura = hmac.new(SECRET_KEY, payload_bytes, hashlib.sha256).hexdigest()

    chave_final = f"{payload_b64}.{assinatura}"
    return chave_final, data_limite.strftime("%d/%m/%Y")


def menu():
    print("=" * 60)
    print("      ⚡ GERADOR DE LICENÇAS — XENOS PDV (USO EXCLUSIVO) ⚡")
    print("=" * 60)

    cliente = input("Nome do Cliente / Loja: ").strip()
    if not cliente:
        cliente = "Cliente Padrao"

    print("\nEscolha o período da mensalidade:")
    print("  [1] Mensal (30 dias)")
    print("  [2] Bimestral (60 dias)")
    print("  [3] Semestral (180 dias)")
    print("  [4] Anual (365 dias - Pagamento à Vista)")
    print("  [5] Vitalício / Teste Longo (10 anos - 3650 dias)")
    print("  [6] Personalizado (definir quantidade de dias)")

    opcao = input("\nOpção (1-6): ").strip()
    dias = 30
    if opcao == "1": dias = 30
    elif opcao == "2": dias = 60
    elif opcao == "3": dias = 180
    elif opcao == "4": dias = 365
    elif opcao == "5": dias = 3650
    elif opcao == "6":
        try: dias = int(input("Quantidade de dias a liberar: "))
        except: dias = 30

    chave, data_fim = gerar_chave(cliente, dias)

    print("\n" + "=" * 60)
    print(f"✅ CHAVE GERADA COM SUCESSO PARA: {cliente}")
    print(f"📅 VÁLIDO ATÉ: {data_fim} ({dias} dias)")
    print("=" * 60)
    print("\nCopie o código abaixo e envie para o cliente colar no sistema:\n")
    print(chave)
    print("\n" + "=" * 60)


if __name__ == "__main__":
    menu()
