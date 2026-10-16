import pytest

from flask import Flask
from flask_socketio import SocketIO

import controller as server


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
        "valor": 100.00,
        "forma_pagamento": "PIX",
        "pontuacao_risco": 0,
        "nivel_risco": "BAIXO",
        "status_automatico": "APROVADA",
        "status": "APROVADA",
        "motivos_risco": [],
        "revisada": False,
        "decisao_revisao": None,
        "data_revisao": None,
        "data_hora": "2026-10-08T12:00:00-03:00",
    }


@pytest.fixture
def aplicacao_socket():
    app = Flask(__name__)

    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "segredo-de-teste"

    socketio = SocketIO(
        app,
        async_mode="threading",
    )

    server.registrar_controller(
        app,
        socketio,
    )

    return app, socketio


def obter_evento(cliente, nome):
    eventos = cliente.get_received()

    for evento in eventos:
        if evento["name"] == nome:
            argumentos = evento.get("args", [])

            if argumentos:
                return argumentos[0]

            return None

    return None


def criar_cliente_socket(
    monkeypatch,
    lojista,
    aplicacao_socket,
):
    app, socketio = aplicacao_socket

    monkeypatch.setattr(
        server,
        "buscar_usuario_logado",
        lambda: lojista,
    )

    return socketio.test_client(app)


def test_pedido_novo_libera_analise(
    monkeypatch,
    lojista,
    aplicacao_socket,
):
    monkeypatch.setattr(
        server.model,
        "buscar_transacao_por_pedido",
        lambda lojista_id, pedido_id: None,
    )

    cliente = criar_cliente_socket(
        monkeypatch,
        lojista,
        aplicacao_socket,
    )

    cliente.emit(
        "verificar_pedido_id",
        {"pedido_id": "PEDIDO-NOVO"},
    )

    resposta = obter_evento(
        cliente,
        "resultado_verificacao_pedido",
    )

    assert resposta is not None
    assert resposta["sucesso"] is True
    assert resposta["existe"] is False
    assert resposta["pedido_id"] == "PEDIDO-NOVO"

    cliente.disconnect()


def test_pedido_existente_retorna_resultado_anterior(
    monkeypatch,
    lojista,
    transacao_existente,
    aplicacao_socket,
):
    monkeypatch.setattr(
        server.model,
        "buscar_transacao_por_pedido",
        lambda lojista_id, pedido_id: transacao_existente,
    )

    cliente = criar_cliente_socket(
        monkeypatch,
        lojista,
        aplicacao_socket,
    )

    cliente.emit(
        "verificar_pedido_id",
        {"pedido_id": "PEDIDO-001"},
    )

    resposta = obter_evento(
        cliente,
        "resultado_verificacao_pedido",
    )

    assert resposta["sucesso"] is True
    assert resposta["existe"] is True

    assert "já foi analisada" in resposta["mensagem"]

    cliente.disconnect()


def test_pedido_vazio_e_rejeitado(
    lojista,
):
    payload = {
        "pedido_id": "",
        "comprador_nome": "Cliente Teste",
        "comprador_tipo_pessoa": "PF",
        "comprador_documento": "12345678901",
        "comprador_email": "cliente@teste.com",
        "valor": 100,
        "forma_pagamento": "PIX",
    }

    dados, erro = server.validar_payload_transacao(payload)

    assert dados is None
    assert erro["sucesso"] is False
    assert erro["campo"] == "pedido_id"


def test_pedido_muito_longo_e_rejeitado(
    lojista,
):
    payload = {
        "pedido_id": "A" * (server.MAX_PEDIDO_ID + 1),
        "comprador_nome": "Cliente Teste",
        "comprador_tipo_pessoa": "PF",
        "comprador_documento": "12345678901",
        "comprador_email": "cliente@teste.com",
        "valor": 100,
        "forma_pagamento": "PIX",
    }

    dados, erro = server.validar_payload_transacao(payload)

    assert dados is None
    assert erro["sucesso"] is False
    assert erro["campo"] == "pedido_id"


def test_verificacao_usa_id_do_lojista(
    monkeypatch,
    lojista,
    aplicacao_socket,
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
        server.model,
        "buscar_transacao_por_pedido",
        buscar_transacao,
    )

    cliente = criar_cliente_socket(
        monkeypatch,
        lojista,
        aplicacao_socket,
    )

    cliente.emit(
        "verificar_pedido_id",
        {"pedido_id": "PEDIDO-XYZ"},
    )

    resposta = obter_evento(
        cliente,
        "resultado_verificacao_pedido",
    )

    assert resposta["sucesso"] is True

    assert chamada["lojista_id"] == lojista["usuario_id"]

    assert chamada["pedido_id"] == "PEDIDO-XYZ"

    cliente.disconnect()


def test_pedido_existente_nao_cria_nova_transacao(
    monkeypatch,
    lojista,
    transacao_existente,
):
    monkeypatch.setattr(
        server.model,
        "buscar_transacao_por_pedido",
        lambda lojista_id, pedido_id: transacao_existente,
    )

    def nao_deve_criar(dados):
        pytest.fail("Uma transação duplicada " "não deveria ser criada.")

    monkeypatch.setattr(
        server.model,
        "criar_transacao",
        nao_deve_criar,
    )

    resultado = server.processar_transacao(
        lojista,
        {
            "pedido_id": "PEDIDO-001",
            "comprador_nome": "Cliente Teste",
            "comprador_tipo_pessoa": "PF",
            "comprador_documento": "12345678901",
            "comprador_email": "cliente@teste.com",
            "valor": 100,
            "forma_pagamento": "PIX",
        },
        origem="WEB",
    )

    assert resultado["sucesso"] is True
    assert resultado["duplicada"] is True

    assert resultado["transacao"]["transacao_id"] == 1
