# Transaction Risk Analyzer

Sistema web desenvolvido em **Python** para análise de risco e identificação de transações potencialmente fraudulentas.

O projeto simula uma plataforma antifraude na qual usuários podem enviar transações para análise, enquanto administradores podem acompanhar operações, gerenciar usuários, manter uma lista de risco e revisar transações manualmente.

> Projeto acadêmico desenvolvido durante o curso de Ciência da Computação.

---

## Funcionalidades

### Lojista

- Cadastro e autenticação de usuários
- Consulta dos dados da própria conta
- Análise de transações
- Identificação de transações já analisadas
- Prevenção de duplicação de transações
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

O sistema também disponibiliza uma API REST para simular a integração de sistemas externos com o serviço de análise de risco.

O arquivo `cliente.py` demonstra esse fluxo utilizando autenticação por token.

---

## Arquitetura MVC

O projeto foi organizado seguindo o padrão arquitetural **MVC — Model, View e Controller**.

### Model

Representado pelo arquivo:

```text
model.py
```

É responsável pelo acesso e persistência dos dados utilizando SQLite.

Entre suas responsabilidades estão:

- conexão com o banco de dados;
- criação das tabelas;
- gerenciamento de usuários;
- armazenamento das transações;
- gerenciamento da lista de risco;
- armazenamento dos motivos de risco;
- consultas e atualizações no banco;
- controle de duplicidade de transações.

### Controller

Representado pelo arquivo:

```text
controller.py
```

É responsável pela lógica da aplicação e pela comunicação entre a View e o Model.

Entre suas responsabilidades estão:

- autenticação;
- cadastro de usuários;
- validação de dados;
- processamento das transações;
- aplicação das regras de risco;
- geração de estatísticas;
- API REST;
- eventos Socket.IO;
- revisão manual de transações;
- controle das funcionalidades administrativas.

### View

Representada pelas pastas:

```text
templates/
static/
```

A camada View é responsável pela interface e pela interação do usuário com a aplicação.

Os arquivos HTML utilizam templates Jinja, enquanto CSS e JavaScript são responsáveis pela apresentação e comportamento da interface.

### Inicialização

O arquivo:

```text
server.py
```

funciona como ponto de entrada da aplicação.

Ele é responsável por:

- criar a aplicação Flask;
- configurar o Socket.IO;
- inicializar o Model;
- registrar o Controller;
- iniciar o servidor.

---

## Análise de risco

Cada transação recebe uma pontuação de acordo com regras predefinidas.

| Regra | Pontuação |
|---|---:|
| Documento presente na lista de risco | +50 |
| Transação realizada entre 00:00 e 05:59 | +20 |
| Valor igual ou superior a R$ 3.000,00 | +30 |
| Terceira tentativa ou posterior em até 10 minutos | +40 |

A quantidade de tentativas é verificada pelo documento associado à transação, considerando as operações recentes registradas no sistema.

### Classificação

| Pontuação | Nível de risco | Status |
|---:|---|---|
| 0–29 | BAIXO | APROVADA |
| 30–59 | MÉDIO | APROVADA COM ALERTA |
| 60–89 | ALTO | EM ANÁLISE |
| 90+ | CRÍTICO | BLOQUEADA |

Transações classificadas como **EM ANÁLISE** podem ser revisadas posteriormente por um administrador.

---

## Identificação das transações

Cada usuário informa um identificador antes de enviar os dados completos da transação.

Internamente, esse identificador é representado pelo campo:

```text
pedido_id
```

O sistema verifica se essa identificação já foi analisada para aquela conta.

Se ainda não existir uma análise, o usuário pode prosseguir com o preenchimento dos dados da transação.

Se a transação já tiver sido analisada, o sistema reutiliza o resultado anterior em vez de criar um novo registro.

O banco de dados também possui uma restrição que impede a duplicação do mesmo identificador dentro da mesma conta.

O mesmo identificador pode existir em contas diferentes.

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
│   │   ├── conta.html
│   │   ├── estatisticas.html
│   │   ├── inicio.html
│   │   ├── painel.html
│   │   ├── risco.html
│   │   ├── transacoes.html
│   │   └── usuarios.html
│   │
│   ├── auth/
│   │   ├── cadastro.html
│   │   └── login.html
│   │
│   ├── components/
│   │   └── modal_detalhes.html
│   │
│   ├── lojista/
│   │   ├── analisar.html
│   │   ├── conta.html
│   │   ├── estatisticas.html
│   │   ├── inicio.html
│   │   ├── painel.html
│   │   └── transacoes.html
│   │
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
├── controller.py
├── login_throttle.py
├── model.py
├── server.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Principais arquivos

### `model.py`

Representa a camada **Model** do padrão MVC.

É responsável pela persistência dos dados utilizando SQLite.

Gerencia:

- usuários;
- transações;
- lista de risco;
- motivos associados ao risco;
- revisão de transações;
- migrações;
- índices e restrições do banco.

### `controller.py`

Representa a camada **Controller**.

Contém a lógica principal da aplicação, incluindo:

- autenticação;
- cadastro;
- validações;
- regras de negócio;
- motor de risco;
- API REST;
- eventos Socket.IO;
- estatísticas;
- funcionalidades administrativas.

### `server.py`

É o ponto de entrada da aplicação.

Inicializa Flask e Flask-SocketIO, prepara o Model e registra as funcionalidades existentes no Controller.

### `login_throttle.py`

Implementa proteção contra múltiplas tentativas consecutivas de login.

### `cliente.py`

Simula um sistema externo consumindo a API REST do Transaction Risk Analyzer.

### `static/js`

O JavaScript do frontend foi dividido em módulos responsáveis por autenticação, área do lojista, área administrativa, estado da aplicação, validações e componentes auxiliares.

### `templates`

Os templates Jinja foram separados por área da aplicação para facilitar a organização e manutenção.

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
- pytest
- Git
- GitHub

---

## Segurança

O projeto implementa medidas de segurança compatíveis com seu objetivo acadêmico:

- senhas armazenadas utilizando hash do Werkzeug;
- chave secreta configurável por variável de ambiente;
- credenciais administrativas configuráveis por variável de ambiente;
- proteção contra excesso de tentativas de login;
- tokens temporários para acesso à API;
- validação dos dados recebidos pelo frontend e pela API;
- restrição de funcionalidades de acordo com o tipo de usuário;
- prevenção de duplicação de transações no banco de dados;
- revisão manual realizada de maneira atômica;
- `.env` e banco SQLite excluídos do versionamento.

Os tokens da API e as sessões Socket.IO são mantidos em memória durante a execução do servidor.

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

```bash
py -m pip install -r requirements.txt
```

Caso esteja utilizando o comando `python`:

```bash
python -m pip install -r requirements.txt
```

---

## Variáveis de ambiente

O projeto utiliza variáveis de ambiente para informações que não devem ser armazenadas diretamente no código.

Utilize o arquivo:

```text
.env.example
```

como referência.

As principais variáveis são:

```env
SECRET_KEY=sua-chave-secreta
ADMIN_INITIAL_PASSWORD=sua-senha-administrativa
PORT=5000
```

A senha administrativa inicial deve possuir pelo menos 12 caracteres.

O arquivo `.env` não deve ser enviado ao GitHub.

> As variáveis precisam estar disponíveis no ambiente em que o servidor for executado.

---

## Iniciando o servidor

No Windows:

```bash
py server.py
```

Ou:

```bash
python server.py
```

Por padrão, a aplicação utiliza a porta:

```text
5000
```

Depois, acesse no navegador:

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

é criado localmente durante a execução da aplicação e não faz parte do repositório.

Na inicialização, o sistema cria as tabelas necessárias e garante a existência da conta administrativa.

O e-mail administrativo utilizado pelo projeto é:

```text
admin@risk.com
```

A senha administrativa inicial é definida através da variável:

```text
ADMIN_INITIAL_PASSWORD
```

---

## API REST

A API permite que sistemas externos utilizem o mecanismo de análise de risco.

### Verificar serviço

```http
GET /api/v1/health
```

### Autenticação

```http
POST /api/v1/login
```

Após a autenticação, a API retorna um token temporário.

O token deve ser enviado nas rotas protegidas através do cabeçalho:

```http
Authorization: Bearer TOKEN
```

O token possui duração de duas horas.

### Analisar uma transação

```http
POST /api/v1/transacoes/analisar
```

Exemplo:

```json
{
  "pedido_id": "TRX-001",
  "comprador_nome": "Cliente Teste",
  "comprador_tipo_pessoa": "PF",
  "comprador_documento": "12345678901",
  "comprador_email": "cliente@teste.com",
  "valor": 3500,
  "forma_pagamento": "PIX"
}
```

Embora alguns nomes internos ainda utilizem termos como `pedido_id` e `comprador`, eles representam os dados associados à transação e não restringem o mecanismo de risco exclusivamente ao comércio eletrônico.

### Listar transações

```http
GET /api/v1/transacoes
```

### Encerrar acesso à API

```http
POST /api/v1/logout
```

A API externa é destinada atualmente às contas do tipo **LOJISTA**.

---

## Testes automatizados

O projeto possui testes automatizados para suas principais funcionalidades.

Entre os cenários testados estão:

- inicialização e operações do banco SQLite;
- criação e consulta de usuários;
- lista de risco;
- criação de transações;
- restrição de transações duplicadas;
- revisão manual de transações;
- proteção contra tentativas excessivas de login;
- validações de entrada;
- identificação de transações;
- regras do motor de risco;
- valores inválidos como `NaN` e `Infinity`;
- diferentes combinações de fatores de risco.

Para executar todos os testes:

```bash
py -m pytest -v
```

ou:

```bash
python -m pytest -v
```

Resultado atual:

```text
95 passed
```

---

## Exemplo do motor de risco

Considere uma transação realizada às 03:00 que apresenta os seguintes fatores:

```text
Documento na lista de risco          +50
Valor igual ou superior a R$ 3.000   +30
Horário incomum                      +20
Múltiplas tentativas                 +40
                                     ----
Pontuação total                      140
```

Resultado:

```text
Nível de risco: CRÍTICO
Status: BLOQUEADA
```

---

## Fluxo simplificado

```text
USUÁRIO
   │
   ▼
VIEW
templates/ + static/
   │
   ▼
CONTROLLER
controller.py
   │
   ├── validações
   ├── autenticação
   ├── regras de negócio
   └── análise de risco
   │
   ▼
MODEL
model.py
   │
   ▼
SQLite
transaction_risk.db
```

---

## Objetivo do projeto

O objetivo do Transaction Risk Analyzer é aplicar conceitos de Engenharia de Software no desenvolvimento de um sistema capaz de analisar transações e identificar situações potencialmente fraudulentas.

O projeto envolve:

- arquitetura MVC;
- desenvolvimento backend;
- desenvolvimento frontend;
- APIs REST;
- comunicação em tempo real com Socket.IO;
- banco de dados relacional;
- autenticação e autorização;
- regras de negócio;
- análise de risco;
- validação de dados;
- testes automatizados;
- organização modular de código.

---

## Status do projeto

**Versão funcional.**

Atualmente, o sistema possui:

- interface web;
- persistência de dados;
- autenticação;
- perfis de lojista e administrador;
- API REST;
- comunicação em tempo real;
- análise automática de risco;
- histórico de transações;
- lista de risco;
- revisão manual;
- estatísticas;
- testes automatizados.

O projeto pode continuar evoluindo com novos fatores de risco, bancos de dados mais robustos, dashboards avançados, análise de dados e modelos estatísticos ou de machine learning.

---

## Autor

**Lucas Fernandes Affonso**

Estudante de Ciência da Computação.