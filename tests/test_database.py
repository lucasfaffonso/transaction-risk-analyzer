import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import database as db

# =========================================================
# BANCO TEMPORÁRIO
# =========================================================


@pytest.fixture
def banco_temporario(
    tmp_path,
    monkeypatch,
):
    caminho_banco = tmp_path / "transaction_risk_test.db"

    monkeypatch.setattr(
        db,
        "BANCO",
        str(caminho_banco),
    )

    db.inicializar_banco("SenhaAdminTeste123!")

    return caminho_banco


# =========================================================
# AUXILIARES
# =========================================================


def criar_lojista(
    *,
    nome="Loja Teste",
    documento="12345678901",
    email="loja@teste.com",
):
    return db.criar_usuario(
        nome=nome,
        tipo_pessoa="PF",
        documento=documento,
        email=email,
        telefone="21999999999",
        senha_hash=generate_password_hash("senha123"),
        data_criacao="07/10/2026",
    )


def dados_transacao(
    lojista_id,
    pedido_id="PEDIDO-001",
):
    return {
        "lojista_id": lojista_id,
        "pedido_id": pedido_id,
        "origem": "WEB",
        "comprador_nome": "Cliente Teste",
        "comprador_tipo_pessoa": "PF",
        "comprador_documento": "98765432100",
        "comprador_email": "cliente@teste.com",
        "valor": 3500.00,
        "forma_pagamento": "PIX",
        "pontuacao_risco": 30,
        "nivel_risco": "MÉDIO",
        "status_automatico": "APROVADA COM ALERTA",
        "status": "APROVADA COM ALERTA",
        "motivos_risco": [
            {
                "motivo": "Valor elevado da transação",
                "pontos": 30,
            }
        ],
        "revisada": False,
        "decisao_revisao": None,
        "data_revisao": None,
        "data_hora": "2026-10-07T15:00:00-03:00",
    }


# =========================================================
# INICIALIZAÇÃO
# =========================================================


def test_banco_e_criado(
    banco_temporario,
):
    assert banco_temporario.exists()

    assert db.testar_conexao() is True


def test_admin_e_criado_automaticamente(
    banco_temporario,
):
    admin = db.buscar_usuario_por_email("admin@risk.com")

    assert admin is not None

    assert admin["tipo_usuario"] == "ADMIN"

    assert admin["status"] == "ATIVA"


# =========================================================
# USUÁRIOS
# =========================================================


def test_criar_e_buscar_lojista(
    banco_temporario,
):
    lojista = criar_lojista()

    assert lojista is not None
    assert lojista["usuario_id"] > 0

    assert lojista["nome"] == "Loja Teste"

    assert lojista["tipo_usuario"] == "LOJISTA"

    assert lojista["status"] == "ATIVA"


def test_buscar_usuario_por_email(
    banco_temporario,
):
    criar_lojista()

    usuario = db.buscar_usuario_por_email("loja@teste.com")

    assert usuario is not None

    assert usuario["documento"] == "12345678901"


def test_buscar_usuario_por_documento(
    banco_temporario,
):
    criar_lojista()

    usuario = db.buscar_usuario_por_documento("12345678901")

    assert usuario is not None

    assert usuario["email"] == "loja@teste.com"


def test_alterar_status_do_lojista(
    banco_temporario,
):
    lojista = criar_lojista()

    db.atualizar_status_usuario(
        lojista["usuario_id"],
        "INATIVA",
    )

    atualizado = db.buscar_usuario_por_id(lojista["usuario_id"])

    assert atualizado["status"] == "INATIVA"


# =========================================================
# LISTA DE RISCO
# =========================================================


def test_adicionar_documento_na_lista_de_risco(
    banco_temporario,
):
    item = db.adicionar_risco(
        nome="Cliente de Risco",
        tipo_pessoa="PF",
        documento="11122233344",
        motivo="Teste automatizado",
        data_adicao="07/10/2026",
    )

    assert item is not None

    assert item["documento"] == "11122233344"

    assert db.documento_na_lista_risco("11122233344") is True


def test_remover_documento_da_lista_de_risco(
    banco_temporario,
):
    item = db.adicionar_risco(
        nome="Cliente de Risco",
        tipo_pessoa="PF",
        documento="11122233344",
        motivo="Teste automatizado",
        data_adicao="07/10/2026",
    )

    db.remover_risco(item["risco_id"])

    assert db.documento_na_lista_risco("11122233344") is False


# =========================================================
# TRANSAÇÕES
# =========================================================


def test_criar_transacao(
    banco_temporario,
):
    lojista = criar_lojista()

    transacao = db.criar_transacao(dados_transacao(lojista["usuario_id"]))

    assert transacao is not None

    assert transacao["pedido_id"] == "PEDIDO-001"

    assert transacao["lojista_id"] == lojista["usuario_id"]

    assert transacao["valor"] == 3500.00

    assert transacao["nivel_risco"] == "MÉDIO"


def test_motivos_da_transacao_sao_salvos(
    banco_temporario,
):
    lojista = criar_lojista()

    transacao = db.criar_transacao(dados_transacao(lojista["usuario_id"]))

    motivos = transacao["motivos_risco"]

    assert len(motivos) == 1

    assert motivos[0]["motivo"] == "Valor elevado da transação"

    assert motivos[0]["pontos"] == 30


def test_buscar_transacao_por_pedido(
    banco_temporario,
):
    lojista = criar_lojista()

    criada = db.criar_transacao(
        dados_transacao(
            lojista["usuario_id"],
            "PEDIDO-ABC",
        )
    )

    encontrada = db.buscar_transacao_por_pedido(
        lojista["usuario_id"],
        "PEDIDO-ABC",
    )

    assert encontrada is not None

    assert encontrada["transacao_id"] == criada["transacao_id"]


# =========================================================
# PEDIDO ÚNICO POR LOJISTA
# =========================================================


def test_mesmo_pedido_nao_pode_ser_duplicado_no_mesmo_lojista(
    banco_temporario,
):
    lojista = criar_lojista()

    dados = dados_transacao(
        lojista["usuario_id"],
        "PEDIDO-DUPLICADO",
    )

    db.criar_transacao(dados)

    with pytest.raises(sqlite3.IntegrityError):
        db.criar_transacao(dados)


def test_mesmo_pedido_pode_existir_em_lojistas_diferentes(
    banco_temporario,
):
    lojista_1 = criar_lojista(
        nome="Loja 1",
        documento="12345678901",
        email="loja1@teste.com",
    )

    lojista_2 = criar_lojista(
        nome="Loja 2",
        documento="12345678902",
        email="loja2@teste.com",
    )

    primeira = db.criar_transacao(
        dados_transacao(
            lojista_1["usuario_id"],
            "PEDIDO-001",
        )
    )

    segunda = db.criar_transacao(
        dados_transacao(
            lojista_2["usuario_id"],
            "PEDIDO-001",
        )
    )

    assert primeira is not None
    assert segunda is not None

    assert primeira["lojista_id"] != segunda["lojista_id"]


# =========================================================
# LISTAGEM
# =========================================================


def test_listar_transacoes_do_lojista(
    banco_temporario,
):
    lojista = criar_lojista()

    db.criar_transacao(
        dados_transacao(
            lojista["usuario_id"],
            "PEDIDO-001",
        )
    )

    db.criar_transacao(
        dados_transacao(
            lojista["usuario_id"],
            "PEDIDO-002",
        )
    )

    transacoes = db.buscar_transacoes_por_lojista(lojista["usuario_id"])

    assert len(transacoes) == 2


# =========================================================
# REVISÃO MANUAL
# =========================================================


def test_revisao_manual_atualiza_transacao(
    banco_temporario,
):
    lojista = criar_lojista()

    dados = dados_transacao(lojista["usuario_id"])

    dados["pontuacao_risco"] = 80
    dados["nivel_risco"] = "ALTO"
    dados["status_automatico"] = "EM ANÁLISE"
    dados["status"] = "EM ANÁLISE"

    transacao = db.criar_transacao(dados)

    atualizada = db.atualizar_revisao_transacao(
        transacao["transacao_id"],
        "APROVADA",
        "APROVADA",
        "2026-10-07T16:00:00-03:00",
    )

    assert atualizada is True

    transacao_atualizada = db.buscar_transacao_por_id(transacao["transacao_id"])

    assert transacao_atualizada["status"] == "APROVADA"

    assert transacao_atualizada["revisada"] is True

    assert transacao_atualizada["decisao_revisao"] == "APROVADA"


def test_transacao_nao_pode_ser_revisada_duas_vezes(
    banco_temporario,
):
    lojista = criar_lojista()

    dados = dados_transacao(lojista["usuario_id"])

    dados["pontuacao_risco"] = 80
    dados["nivel_risco"] = "ALTO"
    dados["status_automatico"] = "EM ANÁLISE"
    dados["status"] = "EM ANÁLISE"

    transacao = db.criar_transacao(dados)

    primeira = db.atualizar_revisao_transacao(
        transacao["transacao_id"],
        "APROVADA",
        "APROVADA",
        "2026-10-07T16:00:00-03:00",
    )

    segunda = db.atualizar_revisao_transacao(
        transacao["transacao_id"],
        "BLOQUEADA",
        "BLOQUEADA",
        "2026-10-07T17:00:00-03:00",
    )

    assert primeira is True
    assert segunda is False

    resultado = db.buscar_transacao_por_id(transacao["transacao_id"])

    assert resultado["status"] == "APROVADA"
