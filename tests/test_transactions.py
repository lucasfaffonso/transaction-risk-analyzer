from datetime import datetime

import pytest

import server

# =========================================================
# AUXILIARES
# =========================================================


def data_hora(hora=12):
    return datetime(
        2026,
        10,
        7,
        hora,
        0,
        0,
        tzinfo=server.FUSO_HORARIO,
    )


def configurar_risco(
    monkeypatch,
    *,
    na_lista=False,
    transacoes_recentes=0,
):
    monkeypatch.setattr(
        server.db,
        "documento_na_lista_risco",
        lambda documento: na_lista,
    )

    monkeypatch.setattr(
        server.db,
        "contar_transacoes_recentes",
        lambda *args: transacoes_recentes,
    )


def motivos_por_pontos(motivos):
    return {motivo["pontos"] for motivo in motivos}


# =========================================================
# BAIXO RISCO
# =========================================================


def test_transacao_sem_fatores_de_risco_e_aprovada(
    monkeypatch,
):
    configurar_risco(
        monkeypatch,
        na_lista=False,
        transacoes_recentes=0,
    )

    pontuacao, nivel, status, motivos = server.analisar_risco(
        "12345678901",
        100.00,
        data_hora(12),
    )

    assert pontuacao == 0
    assert nivel == "BAIXO"
    assert status == "APROVADA"
    assert motivos == []


# =========================================================
# VALOR ELEVADO
# =========================================================


def test_valor_abaixo_de_3000_nao_pontua(
    monkeypatch,
):
    configurar_risco(monkeypatch)

    pontuacao, nivel, status, motivos = server.analisar_risco(
        "12345678901",
        2999.99,
        data_hora(12),
    )

    assert pontuacao == 0
    assert nivel == "BAIXO"
    assert status == "APROVADA"

    assert 30 not in motivos_por_pontos(motivos)


def test_valor_igual_a_3000_adiciona_30_pontos(
    monkeypatch,
):
    configurar_risco(monkeypatch)

    pontuacao, nivel, status, motivos = server.analisar_risco(
        "12345678901",
        3000.00,
        data_hora(12),
    )

    assert pontuacao == 30
    assert nivel == "MÉDIO"

    assert status == "APROVADA COM ALERTA"

    assert 30 in motivos_por_pontos(motivos)


def test_valor_acima_de_3000_adiciona_30_pontos(
    monkeypatch,
):
    configurar_risco(monkeypatch)

    pontuacao, nivel, status, motivos = server.analisar_risco(
        "12345678901",
        5000.00,
        data_hora(12),
    )

    assert pontuacao == 30
    assert nivel == "MÉDIO"

    assert status == "APROVADA COM ALERTA"

    assert 30 in motivos_por_pontos(motivos)


# =========================================================
# LISTA DE RISCO
# =========================================================


def test_documento_na_lista_de_risco_adiciona_50_pontos(
    monkeypatch,
):
    configurar_risco(
        monkeypatch,
        na_lista=True,
    )

    pontuacao, nivel, status, motivos = server.analisar_risco(
        "12345678901",
        100.00,
        data_hora(12),
    )

    assert pontuacao == 50
    assert nivel == "MÉDIO"

    assert status == "APROVADA COM ALERTA"

    assert 50 in motivos_por_pontos(motivos)


# =========================================================
# HORÁRIO INCOMUM
# =========================================================


@pytest.mark.parametrize(
    "hora",
    [
        0,
        1,
        2,
        3,
        4,
        5,
    ],
)
def test_horario_entre_meia_noite_e_5_59_adiciona_20_pontos(
    monkeypatch,
    hora,
):
    configurar_risco(monkeypatch)

    pontuacao, nivel, status, motivos = server.analisar_risco(
        "12345678901",
        100.00,
        data_hora(hora),
    )

    assert pontuacao == 20
    assert nivel == "BAIXO"
    assert status == "APROVADA"

    assert 20 in motivos_por_pontos(motivos)


def test_horario_6_da_manha_nao_adiciona_pontos(
    monkeypatch,
):
    configurar_risco(monkeypatch)

    pontuacao, nivel, status, motivos = server.analisar_risco(
        "12345678901",
        100.00,
        data_hora(6),
    )

    assert pontuacao == 0
    assert nivel == "BAIXO"
    assert status == "APROVADA"

    assert 20 not in motivos_por_pontos(motivos)


# =========================================================
# MÚLTIPLAS TENTATIVAS
# =========================================================


def test_duas_transacoes_anteriores_adicionam_40_pontos(
    monkeypatch,
):
    configurar_risco(
        monkeypatch,
        transacoes_recentes=2,
    )

    pontuacao, nivel, status, motivos = server.analisar_risco(
        "12345678901",
        100.00,
        data_hora(12),
    )

    assert pontuacao == 40
    assert nivel == "MÉDIO"

    assert status == "APROVADA COM ALERTA"

    assert 40 in motivos_por_pontos(motivos)


def test_uma_transacao_anterior_nao_adiciona_40_pontos(
    monkeypatch,
):
    configurar_risco(
        monkeypatch,
        transacoes_recentes=1,
    )

    pontuacao, nivel, status, motivos = server.analisar_risco(
        "12345678901",
        100.00,
        data_hora(12),
    )

    assert pontuacao == 0
    assert nivel == "BAIXO"
    assert status == "APROVADA"

    assert 40 not in motivos_por_pontos(motivos)


# =========================================================
# RISCO ALTO
# =========================================================


def test_lista_de_risco_mais_valor_alto_resulta_em_risco_alto(
    monkeypatch,
):
    configurar_risco(
        monkeypatch,
        na_lista=True,
        transacoes_recentes=0,
    )

    pontuacao, nivel, status, motivos = server.analisar_risco(
        "12345678901",
        3000.00,
        data_hora(12),
    )

    assert pontuacao == 80
    assert nivel == "ALTO"
    assert status == "EM ANÁLISE"

    pontos = motivos_por_pontos(motivos)

    assert 50 in pontos
    assert 30 in pontos


# =========================================================
# RISCO CRÍTICO
# =========================================================


def test_multiplos_fatores_resultam_em_risco_critico(
    monkeypatch,
):
    configurar_risco(
        monkeypatch,
        na_lista=True,
        transacoes_recentes=2,
    )

    pontuacao, nivel, status, motivos = server.analisar_risco(
        "12345678901",
        3000.00,
        data_hora(12),
    )

    assert pontuacao == 120
    assert nivel == "CRÍTICO"
    assert status == "BLOQUEADA"

    pontos = motivos_por_pontos(motivos)

    assert 50 in pontos
    assert 30 in pontos
    assert 40 in pontos


def test_todos_os_fatores_resultam_em_140_pontos(
    monkeypatch,
):
    configurar_risco(
        monkeypatch,
        na_lista=True,
        transacoes_recentes=2,
    )

    pontuacao, nivel, status, motivos = server.analisar_risco(
        "12345678901",
        3000.00,
        data_hora(3),
    )

    assert pontuacao == 140
    assert nivel == "CRÍTICO"
    assert status == "BLOQUEADA"

    assert motivos_por_pontos(motivos) == {
        20,
        30,
        40,
        50,
    }


# =========================================================
# MOTIVOS
# =========================================================


def test_motivos_possuem_texto_e_pontuacao(
    monkeypatch,
):
    configurar_risco(
        monkeypatch,
        na_lista=True,
        transacoes_recentes=2,
    )

    _, _, _, motivos = server.analisar_risco(
        "12345678901",
        3000.00,
        data_hora(3),
    )

    assert len(motivos) == 4

    for motivo in motivos:
        assert "motivo" in motivo
        assert "pontos" in motivo

        assert isinstance(
            motivo["motivo"],
            str,
        )

        assert isinstance(
            motivo["pontos"],
            int,
        )
