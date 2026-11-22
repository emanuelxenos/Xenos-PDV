<p align="center">
  <img src="assets/icone.png" width="130" height="130" alt="Xenos PDV Logo" />
</p>

<h1 align="center">⚡ Xenos PDV — Sistema de Gestão Comercial e Frente de Caixa</h1>

<p align="center">
  <b>Sistema desktop moderno, ágil e robusto para gestão comercial e vendas no varejo.</b><br>
  Desenvolvido em <b>Python</b> com interface moderna em <b>CustomTkinter</b> e banco de dados <b>SQLite</b> via <b>SQLAlchemy</b>.
</p>

<p align="center">
  <i>Ideal para lojas de roupas, pet shops / agropecuárias, mercados, eletrônicos e comércios em geral.</i>
</p>

---

## 🚀 Principais Recursos e Módulos

### 🛒 Frente de Caixa (PDV Ágil)
- **Foco automático no leitor de código de barras:** Pronto para bipar produtos assim que a tela abre ou a venda é concluída.
- **Múltiplas Formas de Pagamento:** Dinheiro, PIX, Cartão de Débito, Cartão de Crédito e **A Prazo (Fiado)**.
- **Cálculo em Tempo Real:** Totalizador, desconto em reais e cálculo instantâneo de troco.
- **Comprovante Térmico Não Fiscal:** Emissão formatada de recibo para bobinas térmicas de 80mm e 58mm, com salvamento e visualização direta.
- **Baixa Automática:** Deduz o estoque automaticamente na confirmação da venda.

### 📖 Contas a Receber (Controle de Fiado)
- Vendas a prazo integradas diretamente ao cadastro de clientes.
- Consulta rápida de débitos por cliente, com status visual (*Pendente*, *Parcial*, *Quitado*).
- Modal de quitação parcial ou total, registrando automaticamente a entrada do valor no fluxo de caixa do dia.

### 💵 Fluxo de Caixa Diário
- Gestão completa de caixa por operador: **Abertura**, **Sangria**, **Suprimento** e **Fechamento**.
- Histórico de movimentações em tempo real com saldo em gaveta consolidado.

### 🏷️ Emissão de Etiquetas em PDF com Código de Barras
- Fila de impressão personalizada: selecione os produtos e a quantidade de etiquetas desejada.
- Geração de folhas de etiquetas no formato padrão A4 (grelha 3x10 / 30 etiquetas por folha, padrão Pimaco 6180/6280 ou compatíveis).
- Impressão com nome do produto, preço de venda, unidade e código de barras legível Code128.

### ⚠️ Alerta de Reposição de Estoque
- Identificação visual imediata de produtos zerados ou abaixo do estoque mínimo.
- Cálculo de déficit e botão de **Ajuste Rápido em 1 Clique** para reabastecimento.

### 💾 Central de Backup Automático & Restauração
- **Backup Periódico em Segundo Plano:** Realiza cópias de segurança em `.zip` compactado a cada *X* horas definidas pelo usuário.
- **Rotação Inteligente:** Mantém as últimas 15 cópias locais automaticamente para não consumir espaço em disco.
- **Importação/Restauração Direta:** Interface centralizada para restaurar backups com 1 clique.

### 🔒 Licenciamento Offline à Prova de Manipulação
- Chaves de ativação baseadas em tokens criptografados (HMAC-SHA256) com data de validade (30, 60, 180, 365 ou 3650 dias).
- Verificação anti-adulteração de relógio do sistema operacional.
- Botão de suporte rápido direcionado para WhatsApp.
- Gerador de licenças CLI independente (`gerador_licenca.py`) para o desenvolvedor emitir as chaves.

---

## 🏗️ Arquitetura do Projeto

O sistema foi concebido de forma modular e desacoplada, evitando códigos monolíticos e garantindo facilidade de manutenção:

```
Xenos_PDV/
├── assets/                  # Ícones oficiais (.ico e .png com transparência)
├── core/
│   ├── auth.py              # Autenticação e hash de senhas (SHA-256)
│   ├── backup.py            # Serviço de backup periódico em thread e restauração
│   ├── database.py          # Modelos SQLAlchemy e scoped_session SQLite
│   ├── etiquetas.py         # Gerador de folhas de etiquetas em PDF (ReportLab)
│   ├── impressao.py         # Formatador de comprovantes térmicos não fiscais
│   └── licenca.py           # Validador de licenças offline e anti-tamper
├── dados/                   # Banco SQLite (xenos.db), backups e cupons
├── telas/
│   ├── alterar_senha.py     # Modal de alteração de senha do operador
│   ├── ativacao.py          # Modal de ativação e renovação de licença
│   ├── backup.py            # Central unificada de backup e restauração
│   ├── caixa.py             # Movimentações e fluxo de caixa diário
│   ├── clientes.py          # Listagem e modal de cadastro de clientes
│   ├── contas_receber.py    # Gestão de crediário / fiado e baixas
│   ├── estoque_alerta.py    # Monitoramento de estoque baixo e reposição
│   ├── etiquetas.py         # Fila de impressão e gerador de PDF
│   ├── fornecedores.py      # Gestão de fornecedores
│   ├── login.py             # Tela de login integrada
│   ├── pdv.py               # Frente de caixa principal
│   ├── produtos.py          # Cadastro de produtos com código de barras
│   ├── relatorios.py        # Relatórios de vendas e reimpressão de cupons
│   └── widgets.py           # Estilos e componentes reutilizáveis CustomTkinter
├── main.py                  # Janela principal, sidebar e roteamento em cache
├── gerador_licenca.py       # Utilitário CLI para geração de licenças
├── iniciar_sistema.bat      # Inicializador fácil para Windows
└── enviar_para_github.bat   # Script facilitador de commits para o Git
```

---

## 🛠️ Instalação e Execução

### Pré-requisitos
- **Python 3.10** ou superior instalado no Windows.

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
*Ou dar dois cliques no arquivo `iniciar_sistema.bat`.*

---

### 🔑 Credenciais Padrão
- **Usuário:** `admin`
- **Senha:** `1234`
*(A senha pode ser alterada diretamente no menu lateral após o login)*
