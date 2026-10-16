import sqlite3

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

import model

ADMIN_PASSWORD = "SenhaAdminTeste123!"


@pytest.fixture
def banco_teste(tmp_path, monkeypatch):
    caminho = tmp_path / "transaction_risk_test.db"

    monkeypatch.setattr(
        model,
        "BANCO",
        str(caminho),
    )

    model.inicializar_banco(ADMIN_PASSWORD)

    return caminho


def criar_lojista(
    nome="Loja Teste",
    documento="12345678901",
    email="loja@teste.com",
):
    return model.criar_usuario(
        nome=nome,
        tipo_pessoa="PF",
        documento=documento,
        email=email,
        telefone="21999999999",
        senha_hash=generate_password_hash("senha123"),
        data_criacao="08/10/2026",
        status="ATIVA",
        tipo_usuario="LOJISTA",
    )


def dados_transacao(
    lojista_id,
    pedido_id="PEDIDO-001",
    documento="98765432100",
):
    return {
        "lojista_id": lojista_id,
        "pedido_id": pedido_id,
        "origem": "WEB",
        "comprador_nome": "Cliente Teste",
        "comprador_tipo_pessoa": "PF",
        "comprador_documento": documento,
        "comprador_email": "cliente@teste.com",
        "valor": 1000.00,
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


def test_banco_e_criado(
    banco_teste,
):
    assert banco_teste.exists()

    with model.conectar() as conexao:
        tabelas = {linha["name"] for linha in conexao.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """).fetchall()}

    assert "usuarios" in tabelas
    assert "transacoes" in tabelas
    assert "lista_risco" in tabelas
    assert "motivos_transacao" in tabelas


def test_admin_e_criado_automaticamente(
    banco_teste,
):
    admin = model.buscar_usuario_por_email("admin@risk.com")

    assert admin is not None
    assert admin["tipo_usuario"] == "ADMIN"
    assert admin["status"] == "ATIVA"

    assert check_password_hash(
        admin["senha_hash"],
        ADMIN_PASSWORD,
    )


def test_criar_e_buscar_lojista(
    banco_teste,
):
    criado = criar_lojista()

    encontrado = model.buscar_usuario_por_id(criado["usuario_id"])

    assert encontrado is not None
    assert encontrado["nome"] == "Loja Teste"
    assert encontrado["tipo_usuario"] == "LOJISTA"


def test_buscar_usuario_por_email(
    banco_teste,
):
    criar_lojista()

    usuario = model.buscar_usuario_por_email("loja@teste.com")

    assert usuario is not None
    assert usuario["email"] == "loja@teste.com"


def test_buscar_usuario_por_documento(
    banco_teste,
):
    criar_lojista()

    usuario = model.buscar_usuario_por_documento("12345678901")

    assert usuario is not None
    assert usuario["documento"] == "12345678901"


def test_alterar_status_do_lojista(
    banco_teste,
):
    lojista = criar_lojista()

    resultado = model.atualizar_status_usuario(
        lojista["usuario_id"],
        "INATIVA",
    )

    atualizado = model.buscar_usuario_por_id(lojista["usuario_id"])

    assert resultado is True
    assert atualizado["status"] == "INATIVA"


def test_adicionar_documento_na_lista_de_risco(
    banco_teste,
):
    item = model.adicionar_risco(
        nome="Cliente Suspeito",
        tipo_pessoa="PF",
        documento="11122233344",
        motivo="Teste",
        data_adicao="08/10/2026 12:00:00",
    )

    assert item is not None

    assert model.documento_na_lista_risco("11122233344")

    lista = model.listar_riscos()

    assert len(lista) == 1
    assert lista[0]["documento"] == "11122233344"


def test_remover_documento_da_lista_de_risco(
    banco_teste,
):
    item = model.adicionar_risco(
        nome="Cliente Suspeito",
        tipo_pessoa="PF",
        documento="11122233344",
        motivo="Teste",
        data_adicao="08/10/2026 12:00:00",
    )

    resultado = model.remover_risco(item["risco_id"])

    assert resultado is True

    assert not model.documento_na_lista_risco("11122233344")


def test_criar_transacao(
    banco_teste,
):
    lojista = criar_lojista()

    transacao = model.criar_transacao(dados_transacao(lojista["usuario_id"]))

    assert transacao is not None
    assert transacao["pedido_id"] == "PEDIDO-001"
    assert transacao["valor"] == 1000.00
    assert transacao["status"] == "APROVADA"


def test_motivos_da_transacao_sao_salvos(
    banco_teste,
):
    lojista = criar_lojista()

    dados = dados_transacao(lojista["usuario_id"])

    dados["pontuacao_risco"] = 50
    dados["nivel_risco"] = "MÉDIO"
    dados["status"] = "APROVADA COM ALERTA"
    dados["status_automatico"] = "APROVADA COM ALERTA"

    dados["motivos_risco"] = [
        {
            "motivo": "Comprador presente na lista de risco",
            "pontos": 50,
        }
    ]

    transacao = model.criar_transacao(dados)

    assert len(transacao["motivos_risco"]) == 1

    assert transacao["motivos_risco"][0]["pontos"] == 50


def test_buscar_transacao_por_pedido(
    banco_teste,
):
    lojista = criar_lojista()

    model.criar_transacao(
        dados_transacao(
            lojista["usuario_id"],
            pedido_id="PEDIDO-ABC",
        )
    )

    transacao = model.buscar_transacao_por_pedido(
        lojista["usuario_id"],
        "PEDIDO-ABC",
    )

    assert transacao is not None
    assert transacao["pedido_id"] == "PEDIDO-ABC"


def test_mesmo_pedido_nao_pode_ser_duplicado_no_mesmo_lojista(
    banco_teste,
):
    lojista = criar_lojista()

    dados = dados_transacao(
        lojista["usuario_id"],
        pedido_id="PEDIDO-DUPLICADO",
    )

    model.criar_transacao(dados)

    with pytest.raises(sqlite3.IntegrityError):
        model.criar_transacao(dados)


def test_mesmo_pedido_pode_existir_em_lojistas_diferentes(
    banco_teste,
):
    lojista_1 = criar_lojista(
        nome="Loja 1",
        documento="11111111111",
        email="loja1@teste.com",
    )

    lojista_2 = criar_lojista(
        nome="Loja 2",
        documento="22222222222",
        email="loja2@teste.com",
    )

    transacao_1 = model.criar_transacao(
        dados_transacao(
            lojista_1["usuario_id"],
            pedido_id="PEDIDO-001",
        )
    )

    transacao_2 = model.criar_transacao(
        dados_transacao(
            lojista_2["usuario_id"],
            pedido_id="PEDIDO-001",
        )
    )

    assert transacao_1["lojista_id"] != transacao_2["lojista_id"]


def test_listar_transacoes_do_lojista(
    banco_teste,
):
    lojista = criar_lojista()

    model.criar_transacao(
        dados_transacao(
            lojista["usuario_id"],
            pedido_id="PEDIDO-001",
        )
    )

    model.criar_transacao(
        dados_transacao(
            lojista["usuario_id"],
            pedido_id="PEDIDO-002",
        )
    )

    transacoes = model.buscar_transacoes_por_lojista(lojista["usuario_id"])

    assert len(transacoes) == 2


def test_revisao_manual_atualiza_transacao(
    banco_teste,
):
    lojista = criar_lojista()

    dados = dados_transacao(lojista["usuario_id"])

    dados["pontuacao_risco"] = 80
    dados["nivel_risco"] = "ALTO"
    dados["status_automatico"] = "EM ANÁLISE"
    dados["status"] = "EM ANÁLISE"

    transacao = model.criar_transacao(dados)

    resultado = model.atualizar_revisao_transacao(
        transacao["transacao_id"],
        "APROVADA",
        "APROVADA",
        "08/10/2026 13:00:00",
    )

    atualizada = model.buscar_transacao_por_id(transacao["transacao_id"])

    assert resultado is True
    assert atualizada["revisada"] is True
    assert atualizada["status"] == "APROVADA"
    assert atualizada["decisao_revisao"] == "APROVADA"


def test_transacao_nao_pode_ser_revisada_duas_vezes(
    banco_teste,
):
    lojista = criar_lojista()

    dados = dados_transacao(lojista["usuario_id"])

    dados["pontuacao_risco"] = 80
    dados["nivel_risco"] = "ALTO"
    dados["status_automatico"] = "EM ANÁLISE"
    dados["status"] = "EM ANÁLISE"

    transacao = model.criar_transacao(dados)

    primeira = model.atualizar_revisao_transacao(
        transacao["transacao_id"],
        "APROVADA",
        "APROVADA",
        "08/10/2026 13:00:00",
    )

    segunda = model.atualizar_revisao_transacao(
        transacao["transacao_id"],
        "BLOQUEADA",
        "BLOQUEADA",
        "08/10/2026 13:01:00",
    )

    assert primeira is True
    assert segunda is False

    atualizada = model.buscar_transacao_por_id(transacao["transacao_id"])

    assert atualizada["status"] == "APROVADA"
