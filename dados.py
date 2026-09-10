# Dados
clientes = []
transacoes = []
destinatarios_suspeitos = []


# Clientes
def salvar_cliente(cliente):
    clientes.append(cliente)


def listar_clientes():
    return clientes


def buscar_cliente_por_id(cliente_id):
    for cliente in clientes:
        if cliente["cliente_id"] == cliente_id:
            return cliente
    return None


def buscar_cliente_por_documento(documento):
    for cliente in clientes:
        if cliente["documento"] == documento:
            return cliente
    return None


# Transações
def salvar_transacao(transacao):
    transacoes.append(transacao)


def listar_transacoes():
    return transacoes


def buscar_transacao_por_id(transacao_id):
    for transacao in transacoes:
        if transacao["transacao_id"] == transacao_id:
            return transacao
    return None


def buscar_transacoes_por_cliente(cliente_id):
    lista = []

    for transacao in transacoes:
        if transacao["cliente_id"] == cliente_id:
            lista.append(transacao)

    return lista


# Destinatários suspeitos
def salvar_destinatario_suspeito(destinatario_suspeito):
    destinatarios_suspeitos.append(destinatario_suspeito)


def listar_destinatarios_suspeitos():
    return destinatarios_suspeitos


def buscar_destinatario_suspeito(documento):
    for destinatario_suspeito in destinatarios_suspeitos:
        if destinatario_suspeito["documento"] == documento:
            return destinatario_suspeito
    return None


def excluir_destinatario_suspeito(destinatario_suspeito):
    destinatarios_suspeitos.remove(destinatario_suspeito)
