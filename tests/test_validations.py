import math

import pytest

import server

# =========================================================
# LOGIN
# =========================================================


def test_login_normaliza_email():
    resultado = server.extrair_credenciais_login(
        {
            "email": "  USUARIO@TESTE.COM  ",
            "senha": "senha123",
        }
    )

    assert resultado == (
        "usuario@teste.com",
        "senha123",
    )


def test_login_rejeita_payload_invalido():
    assert server.extrair_credenciais_login(None) is None

    assert server.extrair_credenciais_login([]) is None

    assert server.extrair_credenciais_login("texto") is None


def test_login_rejeita_email_nao_textual():
    resultado = server.extrair_credenciais_login(
        {
            "email": 123,
            "senha": "senha123",
        }
    )

    assert resultado is None


def test_login_rejeita_senha_nao_textual():
    resultado = server.extrair_credenciais_login(
        {
            "email": "usuario@teste.com",
            "senha": 123456,
        }
    )

    assert resultado is None


def test_login_rejeita_email_muito_longo():
    email = "a" * server.MAX_EMAIL_LOGIN + "x"

    resultado = server.extrair_credenciais_login(
        {
            "email": email,
            "senha": "senha123",
        }
    )

    assert resultado is None


# =========================================================
# E-MAIL
# =========================================================


@pytest.mark.parametrize(
    "email",
    [
        "usuario@teste.com",
        "usuario.nome@empresa.com.br",
        "TESTE@EXEMPLO.COM",
    ],
)
def test_email_valido(email):
    valido, resultado = server.validar_email(email)

    assert valido is True
    assert resultado == email.strip().lower()


@pytest.mark.parametrize(
    "email",
    [
        "usuario",
        "usuario@",
        "@teste.com",
        "usuario@teste",
        "usuario@.com",
        "usuario@teste.",
    ],
)
def test_email_invalido(email):
    valido, mensagem = server.validar_email(email)

    assert valido is False
    assert isinstance(
        mensagem,
        str,
    )


# =========================================================
# DOCUMENTO
# =========================================================


def test_cpf_valido():
    valido, documento = server.validar_documento(
        "12345678901",
        "PF",
    )

    assert valido is True
    assert documento == "12345678901"


def test_cnpj_valido():
    valido, documento = server.validar_documento(
        "12345678000199",
        "PJ",
    )

    assert valido is True
    assert documento == "12345678000199"


def test_cpf_com_tamanho_invalido():
    valido, mensagem = server.validar_documento(
        "1234567890",
        "PF",
    )

    assert valido is False
    assert "11" in mensagem


def test_cnpj_com_tamanho_invalido():
    valido, mensagem = server.validar_documento(
        "1234567800019",
        "PJ",
    )

    assert valido is False
    assert "14" in mensagem


def test_documento_rejeita_letras():
    valido, mensagem = server.validar_documento(
        "1234567890A",
        "PF",
    )

    assert valido is False
    assert "números" in mensagem.lower()


def test_tipo_de_pessoa_invalido():
    valido, mensagem = server.validar_documento(
        "12345678901",
        "XX",
    )

    assert valido is False
    assert "tipo" in mensagem.lower()


# =========================================================
# TELEFONE
# =========================================================


@pytest.mark.parametrize(
    "telefone",
    [
        "21999999999",
        "2133334444",
    ],
)
def test_telefone_valido(telefone):
    valido, resultado = server.validar_telefone(telefone)

    assert valido is True
    assert resultado == telefone


def test_telefone_com_tamanho_invalido():
    valido, mensagem = server.validar_telefone(
        "219999999",
    )

    assert valido is False
    assert "10 ou 11" in mensagem


def test_telefone_rejeita_letras():
    valido, mensagem = server.validar_telefone(
        "21999999ABC",
    )

    assert valido is False
    assert "números" in mensagem.lower()


# =========================================================
# PAYLOAD DE TRANSAÇÃO
# =========================================================


def payload_transacao_valido():
    return {
        "pedido_id": "PEDIDO-001",
        "comprador_nome": "Cliente Teste",
        "comprador_tipo_pessoa": "PF",
        "comprador_documento": "12345678901",
        "comprador_email": "cliente@teste.com",
        "valor": 150.50,
        "forma_pagamento": "PIX",
    }


def test_payload_transacao_valido():
    dados, erro = server.validar_payload_transacao(payload_transacao_valido())

    assert erro is None
    assert dados is not None

    assert dados["pedido_id"] == "PEDIDO-001"

    assert dados["comprador_nome"] == "Cliente Teste"

    assert dados["comprador_tipo_pessoa"] == "PF"

    assert dados["forma_pagamento"] == "PIX"

    assert dados["valor"] == 150.50


def test_payload_transacao_rejeita_body_nao_objeto():
    dados, erro = server.validar_payload_transacao([])

    assert dados is None
    assert erro["sucesso"] is False
    assert erro["campo"] == "body"


def test_payload_rejeita_pedido_vazio():
    payload = payload_transacao_valido()

    payload["pedido_id"] = ""

    dados, erro = server.validar_payload_transacao(payload)

    assert dados is None
    assert erro["sucesso"] is False
    assert erro["campo"] == "pedido_id"


def test_payload_rejeita_pedido_muito_longo():
    payload = payload_transacao_valido()

    payload["pedido_id"] = "A" * (server.MAX_PEDIDO_ID + 1)

    dados, erro = server.validar_payload_transacao(payload)

    assert dados is None
    assert erro["campo"] == "pedido_id"


def test_payload_rejeita_nome_nao_textual():
    payload = payload_transacao_valido()

    payload["comprador_nome"] = 123

    dados, erro = server.validar_payload_transacao(payload)

    assert dados is None
    assert erro["campo"] == "comprador_nome"


def test_payload_rejeita_valor_zero():
    payload = payload_transacao_valido()

    payload["valor"] = 0

    dados, erro = server.validar_payload_transacao(payload)

    assert dados is None
    assert erro["campo"] == "transacao_valor"


def test_payload_rejeita_valor_negativo():
    payload = payload_transacao_valido()

    payload["valor"] = -100

    dados, erro = server.validar_payload_transacao(payload)

    assert dados is None
    assert erro["campo"] == "transacao_valor"


@pytest.mark.parametrize(
    "valor",
    [
        math.nan,
        math.inf,
        -math.inf,
    ],
)
def test_payload_rejeita_valores_nao_finitos(
    valor,
):
    payload = payload_transacao_valido()

    payload["valor"] = valor

    dados, erro = server.validar_payload_transacao(payload)

    assert dados is None
    assert erro["sucesso"] is False
    assert erro["campo"] == "transacao_valor"


@pytest.mark.parametrize(
    "valor",
    [
        None,
        [],
        {},
        True,
    ],
)
def test_payload_rejeita_tipo_de_valor_invalido(
    valor,
):
    payload = payload_transacao_valido()

    payload["valor"] = valor

    dados, erro = server.validar_payload_transacao(payload)

    assert dados is None
    assert erro["campo"] == "transacao_valor"


# =========================================================
# IDENTIFICADORES
# =========================================================


@pytest.mark.parametrize(
    "valor, esperado",
    [
        (1, 1),
        (10, 10),
        ("1", 1),
        ("999", 999),
    ],
)
def test_extrair_id_positivo(
    valor,
    esperado,
):
    resultado = server.extrair_id_positivo_payload(
        {
            "usuario_id": valor,
        },
        "usuario_id",
    )

    assert resultado == esperado


@pytest.mark.parametrize(
    "valor",
    [
        0,
        -1,
        "",
        "abc",
        1.5,
        True,
        None,
    ],
)
def test_extrair_id_rejeita_valor_invalido(
    valor,
):
    resultado = server.extrair_id_positivo_payload(
        {
            "usuario_id": valor,
        },
        "usuario_id",
    )

    assert resultado is None
