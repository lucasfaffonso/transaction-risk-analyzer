from negocio import (
    cadastrar_cliente,
    cadastrar_transacao,
    alterar_status_cliente,
    cadastrar_destinatario_suspeito,
    remover_destinatario_suspeito,
    validar_documento,
    validar_documento_destinatario,
    validar_email,
    validar_telefone,
    validar_dados_financeiros,
)

from dados import (
    listar_clientes,
    listar_transacoes,
    buscar_cliente_por_id,
    buscar_cliente_por_documento,
    buscar_destinatario_suspeito,
    listar_destinatarios_suspeitos,
)


# Utilitários
def aguardar_retorno():
    input("\nPressione ENTER para voltar ao menu...")


def formatar_documento(documento):
    if len(documento) == 11:
        return f"{documento[:3]}.{documento[3:6]}.{documento[6:9]}-{documento[9:]}"

    return f"{documento[:2]}.{documento[2:5]}.{documento[5:8]}/{documento[8:12]}-{documento[12:]}"


def formatar_telefone(telefone):
    if len(telefone) == 11:
        return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"

    return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"


# Menus Cliente
def menu_cadastrar_cliente():

    while True:
        nome = input("Nome do cliente (0 para cancelar): ").strip()

        if nome == "0":
            return

        if nome == "":
            print("Erro: Informe um nome.\n")
            continue

        break

    while True:
        opcao_tipo = input(
            "1 - PF\n" "2 - PJ\n" "0 - Cancelar\n" "Escolha o tipo de pessoa: "
        )

        if opcao_tipo == "0":
            return

        if opcao_tipo == "1":
            tipo_pessoa = "PF"
            break

        elif opcao_tipo == "2":
            tipo_pessoa = "PJ"
            break

        print("\nOpção inválida.")

    while True:

        if tipo_pessoa == "PF":
            documento = input("CPF (0 para cancelar): ")
        else:
            documento = input("CNPJ (0 para cancelar): ")

        if documento == "0":
            return

        documento = documento.strip().replace(".", "").replace("-", "").replace("/", "")

        valido, resultado = validar_documento(documento, tipo_pessoa)

        if not valido:
            print(resultado, "\n")
            continue

        documento = resultado

        if buscar_cliente_por_documento(documento):
            print("Erro: Documento já cadastrado.\n")
            continue

        break

    while True:
        email = input("E-mail (0 para cancelar): ")

        if email == "0":
            return

        valido, resultado = validar_email(email)

        if valido:
            email = resultado
            break

        print(resultado, "\n")

    while True:
        telefone = input("Telefone (0 para cancelar): ")

        if telefone == "0":
            return

        telefone = (
            telefone.strip()
            .replace("(", "")
            .replace(")", "")
            .replace("-", "")
            .replace(" ", "")
        )

        valido, resultado = validar_telefone(telefone)

        if valido:
            telefone = resultado
            break

        print(resultado, "\n")

    while True:
        entrada_saldo = input("Saldo (C para cancelar): R$ ").strip()

        if entrada_saldo.upper() == "C":
            return

        try:
            saldo = float(entrada_saldo)
        except ValueError:
            print("Erro: Saldo deve ser um número.\n")
            continue

        if saldo < 0:
            print("Erro: Saldo inválido.\n")
            continue

        break

    while True:
        entrada_limite = input("Limite diário (C para cancelar): R$ ").strip()

        if entrada_limite.upper() == "C":
            return

        try:
            limite_diario = float(entrada_limite)
        except ValueError:
            print("Erro: Limite diário deve ser um número.\n")
            continue

        if limite_diario <= 0:
            print("Erro: Limite diário inválido.\n")
            continue

        break

    valido, mensagem = validar_dados_financeiros(saldo, limite_diario)

    if not valido:
        print(mensagem)
        aguardar_retorno()
        return

    sucesso, mensagem = cadastrar_cliente(
        nome, tipo_pessoa, documento, email, telefone, saldo, limite_diario
    )

    print("\n", mensagem)
    aguardar_retorno()


def menu_listar_clientes():

    lista = listar_clientes()

    print("\n===== CLIENTES CADASTRADOS =====")

    if not lista:
        print("\nNenhum cliente cadastrado.")
        aguardar_retorno()
        return

    for cliente in lista:

        documento_formatado = formatar_documento(cliente["documento"])
        telefone_formatado = formatar_telefone(cliente["telefone"])

        if cliente["tipo_pessoa"] == "PF":
            tipo_documento = "CPF"
        else:
            tipo_documento = "CNPJ"

        print(
            "\n"
            f"ID: {cliente['cliente_id']} | "
            f"Nome: {cliente['nome']} | "
            f"Tipo: {cliente['tipo_pessoa']} | "
            f"{tipo_documento}: {documento_formatado} | "
            f"E-mail: {cliente['email']} | "
            f"Telefone: {telefone_formatado} | "
            f"Saldo: R$ {cliente['saldo']:.2f} | "
            f"Limite Diário: R$ {cliente['limite_diario']:.2f} | "
            f"Data de Criação: {cliente['data_criacao']} | "
            f"Status: {cliente['status']}"
        )

    aguardar_retorno()


def menu_alterar_status_cliente():

    lista = listar_clientes()

    if not lista:
        print("\nNenhum cliente cadastrado.")
        aguardar_retorno()
        return

    print("\n===== CLIENTES CADASTRADOS =====")

    for cliente in lista:
        print(
            f"ID: {cliente['cliente_id']} | "
            f"Nome: {cliente['nome']} | "
            f"Status: {cliente['status']}"
        )

    while True:

        entrada_id = input("\nID do cliente (0 para cancelar): ")

        if entrada_id == "0":
            return

        try:
            cliente_id = int(entrada_id)
        except ValueError:
            print("Erro: ID deve ser um número.\n")
            continue

        cliente = buscar_cliente_por_id(cliente_id)

        if not cliente:
            print("Erro: Cliente não encontrado.\n")
            continue

        break

    while True:
        opcao_status = input(
            "1 - Ativar\n" "2 - Inativar\n" "0 - Cancelar\n" "Escolha a opção: "
        )

        if opcao_status == "0":
            return

        if opcao_status == "1":
            novo_status = "ATIVA"
            break

        elif opcao_status == "2":
            novo_status = "INATIVA"
            break

        print("Opção inválida.\n")

    sucesso, mensagem = alterar_status_cliente(cliente_id, novo_status)

    print("\n", mensagem)
    aguardar_retorno()


# Menus Transações
def selecionar_cliente_origem():

    while True:
        entrada_id = input(
            "ID do cliente que está realizando a transação " "(0 para cancelar): "
        )

        if entrada_id == "0":
            return None

        try:
            cliente_id = int(entrada_id)
        except ValueError:
            print("Erro: ID deve ser um número.\n")
            continue

        cliente_origem = buscar_cliente_por_id(cliente_id)

        if not cliente_origem:
            print("Erro: Cliente não encontrado.\n")
            continue

        if cliente_origem["status"] != "ATIVA":
            print("Erro: Cliente está inativo.\n")
            continue

        return cliente_origem


def selecionar_destinatario(cliente_origem):

    cliente_id = cliente_origem["cliente_id"]

    while True:
        opcao = input(
            "Destinatário:\n"
            "1 - Cliente cadastrado\n"
            "2 - Destinatário externo\n"
            "0 - Cancelar\n"
            "Escolha a opção: "
        )

        if opcao == "0":
            return None

        if opcao in ["1", "2"]:
            break

        print("Opção inválida.\n")

    if opcao == "1":

        destinatarios_disponiveis = []

        for cliente in listar_clientes():
            if cliente["status"] == "ATIVA" and cliente["cliente_id"] != cliente_id:
                destinatarios_disponiveis.append(cliente)

        if not destinatarios_disponiveis:
            print("Nenhum destinatário disponível.")
            aguardar_retorno()
            return None

        print("\n===== DESTINATÁRIOS DISPONÍVEIS =====")

        for cliente in destinatarios_disponiveis:
            print(f"ID: {cliente['cliente_id']} | " f"Nome: {cliente['nome']}")

        while True:
            entrada_id = input("ID do destinatário (0 para cancelar): ")

            if entrada_id == "0":
                return None

            try:
                destinatario_id = int(entrada_id)
            except ValueError:
                print("Erro: ID deve ser um número.\n")
                continue

            cliente_destino = buscar_cliente_por_id(destinatario_id)

            if not cliente_destino:
                print("Erro: Destinatário não encontrado.\n")
                continue

            if cliente_destino["status"] != "ATIVA":
                print("Erro: Destinatário está inativo.\n")
                continue

            if destinatario_id == cliente_id:
                print("Erro: O cliente não pode transferir para si mesmo.\n")
                continue

            return (
                cliente_destino["nome"],
                cliente_destino["documento"],
                destinatario_id,
            )

    destinatario_id = None

    while True:
        destinatario = input("Nome do destinatário (0 para cancelar): ").strip()

        if destinatario == "0":
            return None

        if destinatario == "":
            print("Erro: Informe o destinatário.\n")
            continue

        break

    while True:
        documento = input("CPF/CNPJ do destinatário (0 para cancelar): ")

        if documento == "0":
            return None

        documento = documento.strip().replace(".", "").replace("-", "").replace("/", "")

        valido, resultado = validar_documento_destinatario(documento)

        if not valido:
            print(resultado, "\n")
            continue

        documento = resultado

        if documento == cliente_origem["documento"]:
            print("Erro: O cliente não pode transferir para si mesmo.\n")
            continue

        return destinatario, documento, destinatario_id


def selecionar_tipo_transacao():

    while True:
        opcao = input(
            "\n===== TIPO DE TRANSAÇÃO =====\n"
            "1 - PIX\n"
            "2 - TRANSFERÊNCIA\n"
            "0 - Cancelar\n"
            "Escolha a opção: "
        )

        if opcao == "0":
            return None

        if opcao == "1":
            return "PIX"

        if opcao == "2":
            return "TRANSFERENCIA"

        print("Opção inválida.\n")


def informar_valor_transacao(cliente_origem):

    while True:
        entrada_valor = input("Valor (C para cancelar): ").strip()

        if entrada_valor.upper() == "C":
            return None

        try:
            valor = float(entrada_valor)
        except ValueError:
            print("Erro: Valor deve ser um número.\n")
            continue

        if valor <= 0:
            print("Erro: Valor deve ser maior que zero.\n")
            continue

        if valor > cliente_origem["saldo"]:
            print("Erro: Saldo insuficiente.\n")
            continue

        return valor


def menu_registrar_transacao():

    cliente_origem = selecionar_cliente_origem()

    if not cliente_origem:
        return

    dados_destinatario = selecionar_destinatario(cliente_origem)

    if not dados_destinatario:
        return

    destinatario, documento_destinatario, destinatario_id = dados_destinatario

    tipo = selecionar_tipo_transacao()

    if not tipo:
        return

    valor = informar_valor_transacao(cliente_origem)

    if valor is None:
        return

    sucesso, mensagem = cadastrar_transacao(
        cliente_origem["cliente_id"],
        valor,
        tipo,
        destinatario,
        documento_destinatario,
        destinatario_id,
    )

    print("\n", mensagem)
    aguardar_retorno()


def menu_listar_transacoes():

    lista = listar_transacoes()

    print("\n===== TRANSAÇÕES REALIZADAS =====")

    if not lista:
        print("\nNenhuma transação realizada.")
        aguardar_retorno()
        return

    for transacao in lista:

        if transacao["motivos_risco"]:
            motivos_formatados = ", ".join(transacao["motivos_risco"])
        else:
            motivos_formatados = "Nenhum"

        print(
            "\n"
            f"ID da transação: {transacao['transacao_id']} | "
            f"Cliente ID: {transacao['cliente_id']} | "
            f"Tipo: {transacao['tipo']} | "
            f"Valor: R$ {transacao['valor']:.2f} | "
            f"Destinatário: {transacao['destinatario']} | "
            f"Data: {transacao['data_hora']} | "
            f"Risco: {transacao['nivel_risco']} | "
            f"Pontuação: {transacao['pontuacao_risco']} | "
            f"Status: {transacao['status']} | "
            f"Motivos: {motivos_formatados}"
        )

    aguardar_retorno()


# Menu Destinatários Suspeitos
def menu_adicionar_destinatario_suspeito():

    while True:
        nome = input("Nome do destinatário (0 para cancelar): ").strip()

        if nome == "0":
            return

        if nome == "":
            print("Erro: Informe o nome do destinatário.\n")
            continue

        break

    while True:
        documento = input("CPF/CNPJ do destinatário (0 para cancelar): ")

        if documento == "0":
            return

        documento = documento.strip().replace(".", "").replace("-", "").replace("/", "")

        valido, resultado = validar_documento_destinatario(documento)

        if not valido:
            print(resultado, "\n")
            continue

        documento = resultado

        if buscar_destinatario_suspeito(documento):
            print("Erro: Destinatário já marcado como suspeito.\n")
            continue

        break

    while True:
        motivo = input("Motivo (0 para cancelar): ").strip()

        if motivo == "0":
            return

        if motivo == "":
            print("Erro: Informe o motivo.\n")
            continue

        break

    sucesso, mensagem = cadastrar_destinatario_suspeito(nome, documento, motivo)

    print("\n", mensagem)
    aguardar_retorno()


def menu_listar_destinatarios_suspeitos():

    lista = listar_destinatarios_suspeitos()

    print("\n===== DESTINATÁRIOS SUSPEITOS =====")

    if not lista:
        print("\nNenhum destinatário suspeito cadastrado.")
        aguardar_retorno()
        return

    for destinatario_suspeito in lista:

        documento_formatado = formatar_documento(destinatario_suspeito["documento"])

        print(
            "\n"
            f"Nome: {destinatario_suspeito['nome']} | "
            f"CPF/CNPJ: {documento_formatado} | "
            f"Motivo: {destinatario_suspeito['motivo']}"
        )

    aguardar_retorno()


def menu_remover_destinatario_suspeito():

    lista = listar_destinatarios_suspeitos()

    if not lista:
        print("\nNenhum destinatário suspeito cadastrado.")
        aguardar_retorno()
        return

    print("\n===== DESTINATÁRIOS SUSPEITOS =====")

    for destinatario_suspeito in lista:

        documento_formatado = formatar_documento(destinatario_suspeito["documento"])

        print(
            f"Nome: {destinatario_suspeito['nome']} | "
            f"CPF/CNPJ: {documento_formatado}"
        )

    while True:

        documento = input(
            "\nCPF/CNPJ do destinatário que deseja remover " "(0 para cancelar): "
        )

        if documento == "0":
            return

        documento = documento.strip().replace(".", "").replace("-", "").replace("/", "")

        valido, resultado = validar_documento_destinatario(documento)

        if not valido:
            print(resultado, "\n")
            continue

        documento = resultado

        if not buscar_destinatario_suspeito(documento):
            print("Erro: Destinatário não está na lista de suspeitos.\n")
            continue

        sucesso, mensagem = remover_destinatario_suspeito(documento)

        print(f"\n{mensagem}")
        aguardar_retorno()
        return


def menu_destinatarios_suspeitos():

    while True:

        print("\n===== DESTINATÁRIOS SUSPEITOS =====\n")
        print("1 - Adicionar destinatário suspeito")
        print("2 - Listar destinatários suspeitos")
        print("3 - Remover destinatário suspeito")
        print("0 - Voltar")

        opcao = input("\nEscolha uma opção: ")

        if opcao == "1":
            menu_adicionar_destinatario_suspeito()

        elif opcao == "2":
            menu_listar_destinatarios_suspeitos()

        elif opcao == "3":
            menu_remover_destinatario_suspeito()

        elif opcao == "0":
            return

        else:
            print("\nOpção inválida.")
            aguardar_retorno()


def menu():
    while True:
        print("\n===== TRANSACTION RISK ANALYZER =====")
        print("\n1 - Cadastrar cliente")
        print("2 - Listar cliente")
        print("3 - Alterar status do cliente")
        print("4 - Registrar transação")
        print("5 - Listar transações")
        print("6 - Gerenciar destinatários suspeitos")
        print("0 - Sair")
        opcao = input("\nEscolha uma opção: ")

        if opcao == "1":
            menu_cadastrar_cliente()

        elif opcao == "2":
            menu_listar_clientes()

        elif opcao == "3":
            menu_alterar_status_cliente()

        elif opcao == "4":
            menu_registrar_transacao()

        elif opcao == "5":
            menu_listar_transacoes()

        elif opcao == "6":

            menu_destinatarios_suspeitos()

        elif opcao == "0":
            print("\nFechando sistema...")
            break

        else:
            print("\nOpção inválida!")
            aguardar_retorno()


# Inicia o menu
menu()
