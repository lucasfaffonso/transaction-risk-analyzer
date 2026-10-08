# Transaction Risk Analyzer

Sistema web desenvolvido em **Python** para análise de risco de transações de e-commerce.

O projeto simula uma plataforma antifraude na qual lojistas podem enviar transações para análise, enquanto administradores podem acompanhar operações, gerenciar usuários, manter uma lista de risco e revisar transações manualmente.

> Projeto acadêmico desenvolvido durante o curso de Ciência da Computação.

---

## Funcionalidades

### Lojista

- Cadastro e autenticação de lojistas
- Consulta dos dados da própria conta
- Análise de transações
- Identificação de pedidos já analisados
- Prevenção de duplicação de pedidos
- Histórico de transações
- Filtros por risco, status, origem e busca
- Estatísticas das transações
- Visualização dos fatores que contribuíram para o risco

### Administrador

- Visualização de todos os lojistas
- Ativação e desativação de contas
- Visualização de todas as transações
- Revisão manual de transações
- Aprovação ou bloqueio de operações em análise
- Gerenciamento da lista de risco
- Estatísticas gerais da plataforma

### API REST

O sistema também disponibiliza uma API REST para simular a integração de um e-commerce externo com o serviço antifraude.

O arquivo `cliente.py` demonstra esse fluxo utilizando autenticação por token.

---

## Análise de risco

Cada transação recebe uma pontuação de acordo com regras predefinidas.

| Regra | Pontuação |
|---|---:|
| Comprador presente na lista de risco | +50 |
| Transação realizada entre 00:00 e 05:59 | +20 |
| Valor igual ou superior a R$ 3.000,00 | +30 |
| Terceira tentativa ou posterior em até 10 minutos | +40 |

A quantidade de tentativas é verificada pelo documento do comprador considerando as transações recentes registradas no sistema.

### Classificação

| Pontuação | Nível de risco | Status |
|---:|---|---|
| 0–29 | BAIXO | APROVADA |
| 30–59 | MÉDIO | APROVADA COM ALERTA |
| 60–89 | ALTO | EM ANÁLISE |
| 90+ | CRÍTICO | BLOQUEADA |

Transações classificadas como **EM ANÁLISE** podem ser revisadas posteriormente por um administrador.

---

## Identificação de pedidos

Cada lojista informa um `pedido_id` antes de enviar os dados completos da transação.

O sistema verifica se o pedido já foi analisado para aquela conta.

Se o pedido ainda não existir, o formulário completo da transação é liberado.

Se o pedido já tiver sido analisado, o sistema reutiliza o resultado anterior em vez de criar uma nova transação.

O banco de dados também possui uma restrição para impedir a duplicação do mesmo `pedido_id` dentro da mesma conta de lojista.

O mesmo identificador pode existir em lojistas diferentes.

---

## Estrutura do projeto

```text
transactionRiskAnalyzer/
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       ├── admin.js
│       ├── auth.js
│       ├── lojista.js
│       ├── main.js
│       ├── modal.js
│       ├── socket.js
│       ├── state.js
│       ├── utils.js
│       └── validators.js
│
├── templates/
│   ├── admin/
│   ├── auth/
│   ├── components/
│   ├── lojista/
│   ├── base.html
│   └── index.html
│
├── tests/
│   ├── test_database.py
│   ├── test_login_throttle.py
│   ├── test_order_id.py
│   ├── test_transactions.py
│   └── test_validations.py
│
├── cliente.py
├── database.py
├── login_throttle.py
├── server.py
├── .env.example
├── .gitignore
└── README.md
```

### `server.py`

Responsável pela aplicação Flask, eventos Socket.IO, API REST, autenticação e processamento das transações.

### `database.py`

Responsável pela persistência dos dados utilizando SQLite.

Gerencia usuários, lista de risco, transações, motivos de risco e migrações do banco de dados.

### `login_throttle.py`

Implementa proteção contra múltiplas tentativas consecutivas de login.

### `cliente.py`

Simula um sistema externo consumindo a API REST do Transaction Risk Analyzer.

### `static/js`

O JavaScript do frontend foi dividido em módulos responsáveis por autenticação, área do lojista, área administrativa, estado da aplicação, validações e componentes auxiliares.

### `templates`

Os templates Jinja foram separados por área da aplicação para facilitar organização e manutenção.

### `tests`

Contém os testes automatizados do sistema utilizando `pytest`.

---

## Tecnologias utilizadas

- Python
- Flask
- Flask-SocketIO
- SQLite
- Jinja
- JavaScript
- HTML
- CSS
- Werkzeug
- Requests
- python-dotenv
- pytest
- Git
- GitHub

---

## Segurança

O projeto implementa algumas medidas de segurança compatíveis com seu objetivo acadêmico:

- Senhas armazenadas utilizando hash do Werkzeug
- Chave secreta configurável por variável de ambiente
- Credenciais administrativas configuráveis por variável de ambiente
- Proteção contra excesso de tentativas de login
- Tokens temporários para acesso à API
- Validação de dados recebidos pelo frontend e pela API
- Restrição de funcionalidades de acordo com o tipo de usuário
- Prevenção de duplicação de pedidos no banco de dados
- `.env` e banco SQLite excluídos do versionamento

Os tokens da API e sessões Socket.IO são mantidos em memória durante a execução do servidor.

---

## Como executar

### 1. Clone o repositório

```bash
git clone https://github.com/lucasfaffonso/transaction-risk-analyzer.git
```

### 2. Acesse a pasta

```bash
cd transaction-risk-analyzer
```

### 3. Instale as dependências

No Windows:

```bash
py -m pip install flask flask-socketio werkzeug requests python-dotenv tzdata pytest
```

Ou:

```bash
python -m pip install flask flask-socketio werkzeug requests python-dotenv tzdata pytest
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto utilizando `.env.example` como referência.

Exemplo:

```env
SECRET_KEY=sua-chave-secreta
ADMIN_INITIAL_PASSWORD=sua-senha-administrativa
PORT=5000
```

O arquivo `.env` não deve ser enviado para o GitHub.

### 5. Inicie o servidor

```bash
py server.py
```

ou:

```bash
python server.py
```

Depois acesse:

```text
http://127.0.0.1:5000
```

---

## Banco de dados

O projeto utiliza **SQLite** para persistência dos dados.

O arquivo:

```text
transaction_risk.db
```

é criado localmente e não faz parte do repositório.

Na inicialização do banco, o sistema também garante a existência da conta administrativa.

O e-mail administrativo utilizado pelo projeto é:

```text
admin@risk.com
```

A senha inicial deve ser definida através da variável:

```text
ADMIN_INITIAL_PASSWORD
```

---

## API REST

### Verificar serviço

```http
GET /api/v1/health
```

### Autenticação

```http
POST /api/v1/login
```

Após autenticação, a API retorna um token que deve ser enviado nas rotas protegidas.

```http
Authorization: Bearer TOKEN
```

### Analisar uma transação

```http
POST /api/v1/transacoes/analisar
```

Exemplo de corpo:

```json
{
  "pedido_id": "PEDIDO-001",
  "comprador_nome": "Cliente Teste",
  "comprador_tipo_pessoa": "PF",
  "comprador_documento": "12345678901",
  "comprador_email": "cliente@teste.com",
  "valor": 3500,
  "forma_pagamento": "PIX"
}
```

### Listar transações

```http
GET /api/v1/transacoes
```

### Encerrar acesso à API

```http
POST /api/v1/logout
```

A API externa é destinada às contas do tipo **LOJISTA**.

---

## Testes automatizados

O projeto possui testes automatizados para as principais partes do sistema.

Entre os cenários testados estão:

- Inicialização e operações do banco SQLite
- Criação e consulta de usuários
- Lista de risco
- Criação de transações
- Restrição de pedidos duplicados
- Revisão manual de transações
- Proteção contra tentativas excessivas de login
- Validações de entrada
- Identificação de pedidos
- Regras do motor de risco
- Valores inválidos como `NaN` e `Infinity`

Para executar todos os testes:

```bash
py -m pytest -v
```

Resultado atual:

```text
95 passed
```

---

## Exemplo do motor de risco

Uma compra realizada às 03:00 com:

```text
Comprador na lista de risco       +50
Valor igual ou superior a R$3000  +30
Horário incomum                   +20
Múltiplas tentativas              +40
                                  ----
Pontuação total                   140
```

Resultado:

```text
Risco: CRÍTICO
Status: BLOQUEADA
```

---

## Objetivo do projeto

O objetivo do Transaction Risk Analyzer é aplicar conceitos de desenvolvimento de software em um cenário próximo de um sistema antifraude real.

O projeto envolve:

- Desenvolvimento backend
- Desenvolvimento frontend
- APIs REST
- Comunicação em tempo real com Socket.IO
- Banco de dados relacional
- Autenticação e autorização
- Regras de negócio
- Validação de dados
- Testes automatizados
- Organização modular de código

---

## Status do projeto

**Versão funcional.**

Atualmente o sistema possui interface web, persistência em banco de dados, autenticação, perfis de lojista e administrador, API REST, análise automática de risco, revisão manual e testes automatizados.

O projeto pode continuar evoluindo com novas regras antifraude, dashboards mais avançados, análise exploratória dos dados e modelos estatísticos ou de machine learning.

---

## Autor

**Lucas Fernandes Affonso**

Estudante de Ciência da Computação.