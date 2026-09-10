# Transaction Risk Analyzer

Sistema desenvolvido em **Python** para simular transações financeiras e realizar uma análise de risco com base em regras predefinidas.

O projeto permite cadastrar clientes, realizar transações, controlar destinatários suspeitos e atribuir automaticamente uma pontuação de risco para cada operação.

> Projeto acadêmico desenvolvido durante o curso de Ciência da Computação.

## Funcionalidades

O sistema atualmente permite:

- Cadastrar clientes Pessoa Física (PF) e Pessoa Jurídica (PJ)
- Listar clientes cadastrados
- Ativar e inativar clientes
- Controlar saldo e limite diário
- Realizar transações via PIX ou transferência
- Realizar transações entre clientes cadastrados
- Realizar transações para destinatários externos
- Cadastrar e remover destinatários suspeitos
- Analisar automaticamente o risco de cada transação
- Consultar o histórico de transações

## Análise de risco

Cada transação é analisada utilizando um sistema de pontuação.

| Regra | Pontuação |
|---|---:|
| Limite diário excedido | +40 |
| Transação realizada entre 00:00 e 05:59 | +20 |
| Destinatário identificado como suspeito | +50 |
| Valor igual ou superior a 80% do saldo disponível | +30 |

A pontuação acumulada determina o nível de risco e o status da transação:

| Pontuação | Nível de risco | Status |
|---:|---|---|
| 0–29 | BAIXO | APROVADA |
| 30–59 | MÉDIO | APROVADA COM ALERTA |
| 60–89 | ALTO | EM ANÁLISE |
| 90+ | CRÍTICO | BLOQUEADA |

Somente transações com status **APROVADA** ou **APROVADA COM ALERTA** realizam a movimentação do saldo.

## Estrutura do projeto

```text
transaction-risk-analyzer/
│
├── main.py
├── negocio.py
├── dados.py
├── README.md
└── .gitignore
```

### `main.py`

Responsável pela interação com o usuário através do terminal, incluindo menus, entrada de dados e exibição dos resultados.

### `negocio.py`

Contém as regras de negócio do sistema, incluindo:

- Validações
- Cadastro e alteração de clientes
- Processamento de transações
- Gerenciamento de destinatários suspeitos
- Cálculo da pontuação de risco
- Classificação das transações

### `dados.py`

Responsável pelo armazenamento e acesso aos dados utilizados durante a execução do programa.

Nesta versão, os dados são armazenados em memória utilizando listas e dicionários.

## Tecnologias utilizadas

- Python
- Git
- GitHub

## Como executar

### 1. Clone o repositório

```bash
git clone https://github.com/lucasfaffonso/transaction-risk-analyzer.git
```

### 2. Acesse a pasta

```bash
cd transaction-risk-analyzer
```

### 3. Execute o programa

```bash
python main.py
```

No Windows, dependendo da instalação do Python:

```bash
py main.py
```

Não é necessária a instalação de bibliotecas externas para executar a versão atual.

## Armazenamento dos dados

Atualmente, clientes, transações e destinatários suspeitos são armazenados apenas em memória.

Isso significa que os dados são perdidos quando o programa é encerrado.

A persistência dos dados poderá ser implementada em versões futuras do projeto.

## Status do projeto

🚧 **Em desenvolvimento**

A versão atual contém as funcionalidades principais de cadastro, processamento de transações e análise de risco.

Possíveis evoluções do projeto incluem:

- Estatísticas e indicadores das transações
- Persistência dos dados
- Análise de dados
- Integração com banco de dados
- Visualização dos resultados

## Autor

**Lucas Fernandes Affonso**

Estudante de Ciência da Computação.