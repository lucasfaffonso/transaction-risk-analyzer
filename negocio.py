from dados import (
    listar_clientes,
    listar_transacoes,
    buscar_cliente_por_id,
    buscar_cliente_por_documento,
    salvar_cliente,
    buscar_transacoes_por_cliente,
    buscar_destinatario_suspeito,
    salvar_destinatario_suspeito,
    excluir_destinatario_suspeito,
    salvar_transacao
)
from datetime import datetime


# Geração de IDs
def gerar_cliente_id():
    return len(listar_clientes()) + 1


def gerar_transacao_id():
    return len(listar_transacoes()) + 1


# Validações
def validar_email(email):

    email = email.strip().lower()

    if "@" not in email:
        return False, "Erro: E-mail inválido."

    partes = email.split("@")

    if len(partes) != 2:
        return False, "Erro: E-mail inválido."

    usuario = partes[0]
    dominio = partes[1]

    if usuario == "" or dominio == "":
        return False, "Erro: E-mail inválido."

    if "." not in dominio:
        return False, "Erro: E-mail inválido."

    if dominio.startswith(".") or dominio.endswith("."):
        return False, "Erro: E-mail inválido."

    return True, email


def validar_documento(documento, tipo_pessoa):

    documento = documento.strip()
    tipo_pessoa = tipo_pessoa.strip().upper()

    if tipo_pessoa not in ["PF", "PJ"]:
        return False, "Erro: Tipo de pessoa inválido."

    if not documento.isdigit():
        return False, "Erro: Documento deve conter apenas números."

    if tipo_pessoa == "PF":
        if len(documento) != 11:
            return False, "Erro: Documento para PF precisa ter 11 dígitos."

    elif tipo_pessoa == "PJ":
        if len(documento) != 14:
            return False, "Erro: Documento para PJ precisa ter 14 dígitos."

    return True, documento


def validar_documento_destinatario(documento):

    documento = documento.strip()

    if documento == "":
        return False, "Erro: Informe o documento do destinatário."

    if not documento.isdigit():
        return False, "Erro: Documento do destinatário deve conter apenas números."

    if len(documento) not in [11, 14]:
        return False, "Erro: Documento do destinatário deve ter 11 ou 14 dígitos."

    return True, documento


def validar_telefone(telefone):

    telefone = telefone.strip()

    if not telefone.isdigit():
        return False, "Erro: Telefone deve conter apenas números."

    if len(telefone) not in [10, 11]:
        return False, "Erro: Telefone deve ter 10 ou 11 dígitos."

    return True, telefone


def validar_dados_financeiros(saldo, limite_diario):

    if saldo < 0:
        return False, "Erro: Saldo inválido."

    if limite_diario <= 0:
        return False, "Erro: Limite diário inválido."

    return True, ""


# Clientes
def cadastrar_cliente(
    nome, tipo_pessoa, documento, email, telefone, saldo, limite_diario
):

    nome = nome.strip()

    if nome == "":
        return False, "Erro: Informe um nome."

    tipo_pessoa = tipo_pessoa.strip().upper()

    if tipo_pessoa not in ["PF", "PJ"]:
        return False, "Erro: Tipo de pessoa inválido."

    # Validação documento
    valido, resultado = validar_documento(documento, tipo_pessoa)

    if not valido:
        return False, resultado

    documento = resultado

    if buscar_cliente_por_documento(documento):
        return False, "Erro: Documento já cadastrado."

    # Validação email
    valido, resultado = validar_email(email)

    if not valido:
        return False, resultado

    email = resultado

    # Validação telefone
    valido, resultado = validar_telefone(telefone)

    if not valido:
        return False, resultado

    telefone = resultado

    # Validação Saldo e Limite Diário
    valido, mensagem = validar_dados_financeiros(saldo, limite_diario)

    if not valido:
        return False, mensagem

    cliente_id = gerar_cliente_id()

    data_criacao = datetime.now()
    data_formatada = data_criacao.strftime("%d/%m/%Y")

    novo_cliente = {
        "cliente_id": cliente_id,
        "nome": nome,
        "tipo_pessoa": tipo_pessoa,
        "documento": documento,
        "email": email,
        "telefone": telefone,
        "saldo": saldo,
        "limite_diario": limite_diario,
        "data_criacao": data_formatada,
        "status": "ATIVA",
    }

    salvar_cliente(novo_cliente)

    return True, "Cliente cadastrado com sucesso!"


def alterar_status_cliente(cliente_id, novo_status):

    cliente = buscar_cliente_por_id(cliente_id)

    if not cliente:
        return False, "Erro: Cliente não existe."

    novo_status = novo_status.strip().upper()

    if novo_status not in ["ATIVA", "INATIVA"]:
        return False, "Erro: Status inválido."

    cliente["status"] = novo_status

    return True, f"Status do cliente alterado para {novo_status}"


# Destinatarios suspeitos
def cadastrar_destinatario_suspeito(nome, documento, motivo):

    nome = nome.strip()
    documento = documento.strip()
    motivo = motivo.strip()

    if nome == "":
        return False, "Erro: Informe o nome do destinatário."

    valido, resultado = validar_documento_destinatario(documento)

    if not valido:
        return False, resultado

    documento = resultado

    if buscar_destinatario_suspeito(documento):
        return False, "Erro: Destinatário já está marcado como suspeito."

    if motivo == "":
        return False, "Erro: Informe o motivo."

    novo_destinatario_suspeito = {
        "nome": nome,
        "documento": documento,
        "motivo": motivo,
    }

    salvar_destinatario_suspeito(novo_destinatario_suspeito)

    return True, "Destinatário marcado como suspeito."


def remover_destinatario_suspeito(documento):

    valido, resultado = validar_documento_destinatario(documento)

    if not valido:
        return False, resultado

    documento = resultado

    destinatario_suspeito = buscar_destinatario_suspeito(documento)

    if not destinatario_suspeito:
        return False, "Erro: Destinatário não está na lista de suspeitos."

    excluir_destinatario_suspeito(destinatario_suspeito)

    return True, "Destinatário removido da lista de suspeitos."


# Análise de risco
def calcular_total_transacoes_hoje(cliente_id):

    transacoes_cliente = buscar_transacoes_por_cliente(cliente_id)

    hoje = datetime.now().strftime("%d/%m/%Y")

    total = 0

    for transacao in transacoes_cliente:

        if transacao["status"] in ["APROVADA", "APROVADA COM ALERTA"]:

            if transacao["data_hora"].startswith(hoje):
                total += transacao["valor"]

    return total


def classificar_risco(pontos):

    if pontos <= 29:
        nivel_risco = "BAIXO"

    elif pontos <= 59:
        nivel_risco = "MEDIO"

    elif pontos <= 89:
        nivel_risco = "ALTO"

    else:
        nivel_risco = "CRITICO"

    if nivel_risco == "BAIXO":
        status = "APROVADA"

    elif nivel_risco == "MEDIO":
        status = "APROVADA COM ALERTA"

    elif nivel_risco == "ALTO":
        status = "EM ANALISE"

    else:
        status = "BLOQUEADA"

    return nivel_risco, status


def analisar_risco(cliente, valor, documento_destinatario):

    pontos = 0
    motivos = []

    # Total movimentado hoje
    total_hoje = calcular_total_transacoes_hoje(cliente["cliente_id"])

    total_com_nova_transacao = total_hoje + valor

    # Limite diário
    if total_com_nova_transacao > cliente["limite_diario"]:
        pontos += 40
        motivos.append("Limite diário excedido.")

    # Horário incomum
    hora_atual = datetime.now().hour

    if hora_atual < 6:
        pontos += 20
        motivos.append("Transação realizada em horário incomum.")

    # Destinatário suspeito
    destinatario_suspeito = buscar_destinatario_suspeito(documento_destinatario)

    if destinatario_suspeito:
        pontos += 50
        motivos.append("Destinatário identificado como suspeito.")

    # Valor muito alto em relação ao saldo
    if valor >= cliente["saldo"] * 0.8:
        pontos += 30
        motivos.append("Valor da transação representa 80% ou mais do saldo.")

    nivel_risco, status = classificar_risco(pontos)

    return pontos, motivos, status, nivel_risco


# Transações
def cadastrar_transacao(
    cliente_id, valor, tipo, destinatario, documento_destinatario, destinatario_id=None
):

    cliente_existente = buscar_cliente_por_id(cliente_id)

    if not cliente_existente:
        return False, "Erro: Cliente não existe."

    if cliente_existente["status"] != "ATIVA":
        return False, "Erro: Cliente não ativo."

    if valor <= 0:
        return False, "Erro: Valor inválido."

    if cliente_existente["saldo"] < valor:
        return False, "Erro: Saldo insuficiente."

    tipo = tipo.strip().upper()

    if tipo == "TRANSFERÊNCIA":
        tipo = "TRANSFERENCIA"

    if tipo not in ["PIX", "TRANSFERENCIA"]:
        return False, "Erro: Tipo de transação inválida."

    if destinatario_id is not None:

        cliente_destino = buscar_cliente_por_id(destinatario_id)

        if not cliente_destino:
            return False, "Erro: Destinatário não existe."

        if destinatario_id == cliente_id:
            return False, "Erro: O cliente não pode transferir para si mesmo."

        if cliente_destino["status"] != "ATIVA":
            return False, "Erro: Destinatário está inativo."

        destinatario = cliente_destino["nome"]
        documento_destinatario = cliente_destino["documento"]

    else:

        destinatario = destinatario.strip()

        if destinatario == "":
            return False, "Erro: Informe o destinatário."

        valido, resultado = validar_documento_destinatario(documento_destinatario)

        if not valido:
            return False, resultado

        documento_destinatario = resultado

        if documento_destinatario == cliente_existente["documento"]:
            return False, "Erro: O cliente não pode transferir para si mesmo."

    transacao_id = gerar_transacao_id()

    data_hora = datetime.now()
    data_formatada = data_hora.strftime("%d/%m/%Y %H:%M:%S")

    pontos, motivos, status, nivel_risco = analisar_risco(
        cliente_existente, valor, documento_destinatario
    )

    if status in ["APROVADA", "APROVADA COM ALERTA"]:

        cliente_existente["saldo"] -= valor

        if destinatario_id is not None:
            cliente_destino["saldo"] += valor

    nova_transacao = {
        "transacao_id": transacao_id,
        "valor": valor,
        "tipo": tipo,
        "destinatario": destinatario,
        "documento_destinatario": documento_destinatario,
        "destinatario_id": destinatario_id,
        "data_hora": data_formatada,
        "cliente_id": cliente_id,
        "pontuacao_risco": pontos,
        "motivos_risco": motivos,
        "status": status,
        "nivel_risco": nivel_risco,
    }

    salvar_transacao(nova_transacao)
    return True, f"Transação registrada. Status: {status}"
