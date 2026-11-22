# ⚡ Xenos PDV — Sistema de Gestão Comercial e Frente de Caixa

Sistema desktop moderno para gestão comercial e vendas, desenvolvido em **Python** com **CustomTkinter** e banco de dados **SQLite** via **SQLAlchemy**.

Projetado de forma genérica para atender lojas de roupas, agropecuárias/rações, mercados, eletrônicos e comércios em geral.

---

## 🚀 Funcionalidades

- **Autenticação:** Controle de acesso com usuário e senha criptografada (SHA-256).
- **Frente de Caixa (PDV):**
  - Leitura rápida por código de barras ou busca por nome/ID.
  - Formas de pagamento: Dinheiro, PIX, Cartão de Débito, Cartão de Crédito e A Prazo.
  - Cálculo instantâneo de descontos e troco.
  - Baixa automática no estoque ao concluir a venda.
  - **Comprovante Térmico Não Fiscal:** Emissão formatada para bobinas térmicas (80mm e 58mm).
- **Gestão de Produtos e Estoque:**
  - Suporte a diversas unidades de medida (`UN`, `KG`, `M`, `L`, `CX`, `PCT`, `PAR`, etc.).
  - Controle de estoque mínimo e preços de compra/venda com margem.
- **Cadastros em Popups Modais:**
  - Clientes (com controle de limite de crédito).
  - Fornecedores completos.
  - Chaves primárias sequenciais automáticas (sem necessidade de código manual).
- **Painel Geral (Dashboard):** Visão geral em tempo real de vendas e contadores.
- **Performance:** Conexão única com escopo global em memória (`scoped_session`) e cache de telas com transição instantânea.

---

## 🛠️ Instalação e Execução

### Pré-requisitos
- Python 3.10 ou superior instalado.

### 1. Clonar o repositório
```bash
git clone https://github.com/emanuelxenos/Xenos-PDV.git
cd Xenos-PDV
```

### 2. Instalar dependências
```bash
pip install customtkinter sqlalchemy reportlab pillow
```

### 3. Iniciar o sistema
Basta executar:
```bash
python main.py
```
*Ou dar dois cliques em `iniciar_sistema.bat` no Windows.*

---

### 🔑 Acesso Padrão
- **Usuário:** `admin`
- **Senha:** `1234`
