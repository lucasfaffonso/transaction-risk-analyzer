import pytest

import server

# =========================================================
# DADOS DE TESTE
# =========================================================


@pytest.fixture
def lojista():
    return {
        "usuario_id": 10,
        "nome": "Loja Teste",
        "tipo_usuario": "LOJISTA",
        "status": "ATIVA",
    }


@pytest.fixture
def transacao_existente():
    return {
        "transacao_id": 1,
        "lojista_id": 10,
        "pedido_id": "PEDIDO-001",
        "origem": "WEB",
        "comprador_nome": "Cliente Teste",
        "comprador_tipo_pessoa": "PF",
        "comprador_documento": "12345678901",
        "comprador_email": "cliente@teste.com",
        "valor": 150.00,
        "forma_pagamento": "PIX",
        "pontuacao_risco": 0,
        "nivel_risco": "BAIXO",
        "status_automatico": "APROVADA",
        "status": "APROVADA",
        "motivos_risco": [],
        "revisada": False,
        "decisao_revisao": None,
        "data_revisao": None,
        "data_hora": "2026-10-07T15:00:00-03:00",
    }


# =========================================================
# AUXILIARES
# =========================================================


def buscar_resposta(cliente, nome_evento):
    eventos = cliente.get_received()

    for evento in eventos:
        if evento["name"] == nome_evento:
            return evento["args"][0]

    pytest.fail(f"Evento '{nome_evento}' não foi recebido.")


def criar_cliente_socket(
    monkeypatch,
    lojista,
):
    monkeypatch.setattr(
        server,
        "buscar_usuario_logado",
        lambda: lojista,
    )

    return server.socketio.test_client(server.app)


# =========================================================
# PEDIDO NOVO
# =========================================================


def test_pedido_novo_libera_analise(
    monkeypatch,
    lojista,
):
    monkeypatch.setattr(
        server.db,
        "buscar_transacao_por_pedido",
        lambda lojista_id, pedido_id: None,
    )

    cliente = criar_cliente_socket(
        monkeypatch,
        lojista,
    )

    cliente.emit(
        "verificar_pedido_id",
        {
            "pedido_id": "PEDIDO-NOVO",
        },
    )

    resposta = buscar_resposta(
        cliente,
        "resultado_verificacao_pedido",
    )

    assert resposta["sucesso"] is True
    assert resposta["existe"] is False
    assert resposta["pedido_id"] == "PEDIDO-NOVO"

    cliente.disconnect()


# =========================================================
# PEDIDO EXISTENTE
# =========================================================


def test_pedido_existente_retorna_resultado_anterior(
    monkeypatch,
    lojista,
    transacao_existente,
):
    monkeypatch.setattr(
        server.db,
        "buscar_transacao_por_pedido",
        lambda lojista_id, pedido_id: transacao_existente,
    )

    cliente = criar_cliente_socket(
        monkeypatch,
        lojista,
    )

    cliente.emit(
        "verificar_pedido_id",
        {
            "pedido_id": "PEDIDO-001",
        },
    )

    resposta = buscar_resposta(
        cliente,
        "resultado_verificacao_pedido",
    )

    assert resposta["sucesso"] is True
    assert resposta["existe"] is True
    assert resposta["pedido_id"] == "PEDIDO-001"

    transacao = resposta["transacao"]

    assert transacao["transacao_id"] == 1

    assert transacao["pedido_id"] == "PEDIDO-001"

    assert transacao["nivel_risco"] == "BAIXO"

    assert transacao["status"] == "APROVADA"

    cliente.disconnect()


# =========================================================
# PEDIDO VAZIO
# =========================================================


def test_pedido_vazio_e_rejeitado(
    monkeypatch,
    lojista,
):
    cliente = criar_cliente_socket(
        monkeypatch,
        lojista,
    )

    cliente.emit(
        "verificar_pedido_id",
        {
            "pedido_id": "",
        },
    )

    resposta = buscar_resposta(
        cliente,
        "resultado_verificacao_pedido",
    )

    assert resposta["sucesso"] is False
    assert "pedido" in resposta["mensagem"].lower()

    cliente.disconnect()


# =========================================================
# PEDIDO MAIOR QUE O LIMITE
# =========================================================


def test_pedido_muito_longo_e_rejeitado(
    monkeypatch,
    lojista,
):
    cliente = criar_cliente_socket(
        monkeypatch,
        lojista,
    )

    cliente.emit(
        "verificar_pedido_id",
        {
            "pedido_id": "A" * 81,
        },
    )

    resposta = buscar_resposta(
        cliente,
        "resultado_verificacao_pedido",
    )

    assert resposta["sucesso"] is False
    assert "80" in resposta["mensagem"]

    cliente.disconnect()


# =========================================================
# PEDIDO É ESPECÍFICO DO LOJISTA
# =========================================================


def test_verificacao_usa_id_do_lojista(
    monkeypatch,
    lojista,
):
    chamada = {}

    def buscar_transacao(
        lojista_id,
        pedido_id,
    ):
        chamada["lojista_id"] = lojista_id

        chamada["pedido_id"] = pedido_id

        return None

    monkeypatch.setattr(
        server.db,
        "buscar_transacao_por_pedido",
        buscar_transacao,
    )

    cliente = criar_cliente_socket(
        monkeypatch,
        lojista,
    )

    cliente.emit(
        "verificar_pedido_id",
        {
            "pedido_id": "PEDIDO-999",
        },
    )

    buscar_resposta(
        cliente,
        "resultado_verificacao_pedido",
    )

    assert chamada["lojista_id"] == 10

    assert chamada["pedido_id"] == "PEDIDO-999"

    cliente.disconnect()


# =========================================================
# NÃO DUPLICAR TRANSAÇÃO
# =========================================================


def test_pedido_existente_nao_cria_nova_transacao(
    monkeypatch,
    lojista,
    transacao_existente,
):
    monkeypatch.setattr(
        server.db,
        "buscar_transacao_por_pedido",
        lambda lojista_id, pedido_id: transacao_existente,
    )

    def criar_transacao_nao_deveria_ser_chamada(
        dados,
    ):
        pytest.fail("Uma nova transação foi criada " "para um pedido já existente.")

    monkeypatch.setattr(
        server.db,
        "criar_transacao",
        criar_transacao_nao_deveria_ser_chamada,
    )

    resultado = server.processar_transacao(
        lojista,
        {
            "pedido_id": "PEDIDO-001",
            "comprador_nome": "Cliente Teste",
            "comprador_tipo_pessoa": "PF",
            "comprador_documento": "12345678901",
            "comprador_email": "cliente@teste.com",
            "valor": 150.00,
            "forma_pagamento": "PIX",
        },
    )

    assert resultado["sucesso"] is True

    assert resultado["duplicada"] is True

    assert resultado["transacao"]["pedido_id"] == "PEDIDO-001"
