import math
import os

import requests

SERVER_URL = os.getenv("SERVER_URL", "http://127.0.0.1:5000").rstrip("/")

FORMAS_PAGAMENTO = {"CARTAO", "PIX", "BOLETO"}
TIPOS_PESSOA = {"PF", "PJ"}


def requisicao_json(metodo, rota, **kwargs):
    """Faz uma requisição e tenta retornar a resposta em JSON."""
    try:
        resposta = requests.request(
            metodo,
            f"{SERVER_URL}{rota}",
            timeout=kwargs.pop("timeout", 10),
            **kwargs,
        )

        try:
            dados = resposta.json()
        except ValueError:
            print("O servidor retornou uma resposta inválida.")
            return None, None

        return resposta, dados

    except requests.RequestException as erro:
        print(f"Erro de conexão: {erro}")
        return None, None


def cabecalhos(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def verificar_servidor():
    resposta, dados = requisicao_json(
        "GET",
        "/api/v1/health",
        timeout=5,
    )

    if resposta is None:
        return False

    if resposta.ok and dados.get("sucesso"):
        print("Servidor online.")
        return True

    print("O servidor respondeu, mas não está saudável.")
    return False


def login():
    print("\n=== LOGIN DO LOJISTA ===")

    email = input("E-mail: ").strip()
    senha = input("Senha: ")

    resposta, dados = requisicao_json(
        "POST",
        "/api/v1/login",
        json={
            "email": email,
            "senha": senha,
        },
    )

    if resposta is None:
        return None

    if resposta.status_code == 429:
        espera = resposta.headers.get("Retry-After")

        if espera:
            print(
                f"Muitas tentativas de login. "
                f"Tente novamente em aproximadamente {espera} segundos."
            )
        else:
            print("Muitas tentativas de login. Tente novamente mais tarde.")

        return None

    if not resposta.ok or not dados.get("sucesso"):
        print(
            dados.get(
                "mensagem",
                "Não foi possível realizar o login.",
            )
        )
        return None

    usuario = dados["usuario"]

    print(f"Login realizado como {usuario['nome']}.")

    return dados["token"]


def ler_tipo_pessoa():
    while True:
        tipo = input("Tipo de pessoa (PF/PJ): ").strip().upper()

        if tipo in TIPOS_PESSOA:
            return tipo

        print("Digite PF ou PJ.")


def ler_valor():
    entrada = input("Valor da compra: R$ ").strip().replace(",", ".")

    try:
        valor = float(entrada)
    except ValueError:
        print("Valor inválido.")
        return None

    if not math.isfinite(valor) or valor <= 0:
        print("O valor deve ser um número maior que zero.")
        return None

    return round(valor, 2)


def ler_forma_pagamento():
    while True:
        pagamento = input("Forma de pagamento (CARTAO/PIX/BOLETO): ").strip().upper()

        if pagamento in FORMAS_PAGAMENTO:
            return pagamento

        print("Forma de pagamento inválida.")


def mostrar_resultado_transacao(transacao):
    print(f"Pedido: {transacao.get('pedido_id') or '-'}")
    print(f"Transação: #{transacao['transacao_id']}")
    print(f"Data: {transacao['data_hora']}")
    print(f"Score: {transacao['pontuacao_risco']}")
    print(f"Risco: {transacao['nivel_risco']}")
    print(f"Status: {transacao['status']}")
    print(f"Origem: {transacao.get('origem', 'API')}")

    motivos = transacao.get("motivos_risco", [])

    if not motivos:
        print("Motivos: nenhum fator de risco identificado.")
        return

    print("Motivos:")

    for motivo in motivos:
        print(f"  +{motivo['pontos']} - {motivo['motivo']}")


def analisar_transacao(token):
    print("\n=== ANALISAR TRANSAÇÃO ===")

    pedido_id = input("ID da transação: ").strip()

    if not pedido_id:
        print("O ID da transação é obrigatório.")
        return True

    if len(pedido_id) > 80:
        print("O ID da transação deve ter no máximo 80 caracteres.")
        return True

    nome = input("Nome do comprador: ").strip()
    tipo_pessoa = ler_tipo_pessoa()
    documento = input("CPF/CNPJ: ").strip()
    email = input("E-mail do comprador: ").strip()

    valor = ler_valor()

    if valor is None:
        return True

    forma_pagamento = ler_forma_pagamento()

    dados_transacao = {
        "pedido_id": pedido_id,
        "comprador_nome": nome,
        "comprador_tipo_pessoa": tipo_pessoa,
        "comprador_documento": documento,
        "comprador_email": email,
        "valor": valor,
        "forma_pagamento": forma_pagamento,
    }

    resposta, dados = requisicao_json(
        "POST",
        "/api/v1/transacoes/analisar",
        json=dados_transacao,
        headers=cabecalhos(token),
    )

    if resposta is None:
        return True

    if resposta.status_code == 401:
        print("Sua sessão não é mais válida. Faça login novamente.")
        return False

    if not resposta.ok or not dados.get("sucesso"):
        print(
            dados.get(
                "mensagem",
                "Não foi possível analisar a transação.",
            )
        )
        return True

    transacao = dados["transacao"]

    if dados.get("duplicada"):
        print(
            "\nEsta transação já foi analisada. " "O resultado anterior foi reutilizado."
        )
    else:
        print("\nTransação analisada com sucesso.")

    mostrar_resultado_transacao(transacao)

    return True


def mostrar_transacao_resumida(transacao):
    print("\n------------------------------")
    print(f"Transação: #{transacao['transacao_id']}")
    print(f"Pedido: {transacao.get('pedido_id') or '-'}")
    print(f"Data: {transacao['data_hora']}")
    print(f"Comprador: {transacao['comprador_nome']}")
    print(f"Documento: {transacao['comprador_documento']}")
    print(f"Valor: R$ {transacao['valor']:.2f}")
    print(f"Pagamento: {transacao['forma_pagamento']}")
    print(f"Origem: {transacao.get('origem', 'API')}")
    print(f"Score: {transacao['pontuacao_risco']}")
    print(f"Risco: {transacao['nivel_risco']}")
    print(f"Status: {transacao['status']}")


def listar_transacoes(token):
    print("\n=== MINHAS TRANSAÇÕES ===")

    resposta, dados = requisicao_json(
        "GET",
        "/api/v1/transacoes",
        headers=cabecalhos(token),
    )

    if resposta is None:
        return True

    if resposta.status_code == 401:
        print("Sua sessão não é mais válida. Faça login novamente.")
        return False

    if not resposta.ok or not dados.get("sucesso"):
        print(
            dados.get(
                "mensagem",
                "Não foi possível listar as transações.",
            )
        )
        return True

    transacoes = dados.get("transacoes", [])

    if not transacoes:
        print("Nenhuma transação encontrada.")
        return True

    print(f"\nTotal encontrado: {len(transacoes)}")

    for transacao in transacoes:
        mostrar_transacao_resumida(transacao)

    return True


def logout(token):
    requisicao_json(
        "POST",
        "/api/v1/logout",
        headers=cabecalhos(token),
        timeout=5,
    )


def menu(token):
    while True:
        print("\n===== E-COMMERCE CLIENTE =====")
        print("1 - Analisar transação")
        print("2 - Minhas transações")
        print("3 - Sair")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            sessao_valida = analisar_transacao(token)

            if not sessao_valida:
                break

        elif opcao == "2":
            sessao_valida = listar_transacoes(token)

            if not sessao_valida:
                break

        elif opcao == "3":
            logout(token)
            print("Sessão encerrada.")
            break

        else:
            print("Opção inválida.")


def main():
    print("===== TRANSACTION RISK ANALYZER - CLIENTE EXTERNO =====")

    if not verificar_servidor():
        return

    token = login()

    if not token:
        return

    menu(token)


if __name__ == "__main__":
    main()
