import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANCO = os.path.join(BASE_DIR, "transaction_risk.db")

FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")


# =========================================================
# CONEXÃO
# =========================================================


def conectar():
    conexao = sqlite3.connect(BANCO, timeout=10)

    conexao.row_factory = sqlite3.Row

    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


def _hash_senha_admin_inicial(senha):
    if not isinstance(senha, str) or len(senha) < 12:
        raise RuntimeError(
            "Configure ADMIN_INITIAL_PASSWORD "
            "com pelo menos 12 caracteres "
            "para criar ou proteger a conta administrativa."
        )

    return generate_password_hash(senha)


# =========================================================
# INICIALIZAÇÃO DO BANCO
# =========================================================


def inicializar_banco(senha_admin_inicial=None):
    with conectar() as conexao:

        conexao.execute("PRAGMA journal_mode = WAL")

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS app_migrations (
                migration_id TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                usuario_id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo_pessoa TEXT,
                documento TEXT UNIQUE,
                email TEXT NOT NULL UNIQUE,
                telefone TEXT,
                senha_hash TEXT NOT NULL,
                data_criacao TEXT NOT NULL,
                status TEXT NOT NULL,
                tipo_usuario TEXT NOT NULL
            )
            """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS lista_risco (
                risco_id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo_pessoa TEXT NOT NULL,
                documento TEXT NOT NULL UNIQUE,
                motivo TEXT NOT NULL,
                data_adicao TEXT NOT NULL
            )
            """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS transacoes (
                transacao_id INTEGER PRIMARY KEY AUTOINCREMENT,
                lojista_id INTEGER NOT NULL,
                pedido_id TEXT,
                origem TEXT NOT NULL,
                comprador_nome TEXT NOT NULL,
                comprador_tipo_pessoa TEXT NOT NULL,
                comprador_documento TEXT NOT NULL,
                comprador_email TEXT NOT NULL,
                valor REAL NOT NULL,
                forma_pagamento TEXT NOT NULL,
                pontuacao_risco INTEGER NOT NULL,
                nivel_risco TEXT NOT NULL,
                status_automatico TEXT NOT NULL,
                status TEXT NOT NULL,
                revisada INTEGER NOT NULL DEFAULT 0,
                decisao_revisao TEXT,
                data_revisao TEXT,
                data_hora TEXT NOT NULL,

                FOREIGN KEY (lojista_id)
                    REFERENCES usuarios(usuario_id)
            )
            """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS motivos_transacao (
                motivo_id INTEGER PRIMARY KEY AUTOINCREMENT,
                transacao_id INTEGER NOT NULL,
                motivo TEXT NOT NULL,
                pontos INTEGER NOT NULL,

                FOREIGN KEY (transacao_id)
                    REFERENCES transacoes(transacao_id)
                    ON DELETE CASCADE
            )
            """)

        # -------------------------------------------------
        # MIGRAÇÃO: pedido_id
        # -------------------------------------------------

        colunas_transacoes = {
            linha["name"]
            for linha in conexao.execute("PRAGMA table_info(transacoes)").fetchall()
        }

        if "pedido_id" not in colunas_transacoes:
            conexao.execute("""
                ALTER TABLE transacoes
                ADD COLUMN pedido_id TEXT
                """)

        # -------------------------------------------------
        # ÍNDICES
        # -------------------------------------------------

        conexao.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_transacao_pedido_lojista
            ON transacoes (
                lojista_id,
                pedido_id
            )
            WHERE pedido_id IS NOT NULL
            AND pedido_id <> ''
            """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_usuario_email
            ON usuarios(email)
            """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_usuario_documento
            ON usuarios(documento)
            """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_transacao_lojista
            ON transacoes(lojista_id)
            """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_transacao_documento
            ON transacoes(
                comprador_documento
            )
            """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_transacao_data
            ON transacoes(data_hora)
            """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_lista_risco_documento
            ON lista_risco(documento)
            """)

        # -------------------------------------------------
        # ADMINISTRADOR
        # -------------------------------------------------

        admin = conexao.execute(
            """
            SELECT usuario_id
            FROM usuarios
            WHERE email = ?
            """,
            ("admin@risk.com",),
        ).fetchone()

        migracao_admin_aplicada = conexao.execute(
            """
                SELECT 1
                FROM app_migrations
                WHERE migration_id = ?
                """,
            ("admin-initial-password-v1",),
        ).fetchone()

        if not admin or not migracao_admin_aplicada:
            senha_hash = _hash_senha_admin_inicial(senha_admin_inicial)

            if admin:
                conexao.execute(
                    """
                    UPDATE usuarios
                    SET senha_hash = ?
                    WHERE usuario_id = ?
                    """,
                    (
                        senha_hash,
                        admin["usuario_id"],
                    ),
                )

            else:
                conexao.execute(
                    """
                    INSERT INTO usuarios (
                        nome,
                        tipo_pessoa,
                        documento,
                        email,
                        telefone,
                        senha_hash,
                        data_criacao,
                        status,
                        tipo_usuario
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        "Administrador",
                        None,
                        None,
                        "admin@risk.com",
                        None,
                        senha_hash,
                        datetime.now(FUSO_HORARIO).strftime("%d/%m/%Y"),
                        "ATIVA",
                        "ADMIN",
                    ),
                )

            if not migracao_admin_aplicada:
                conexao.execute(
                    """
                    INSERT INTO app_migrations (
                        migration_id,
                        applied_at
                    )
                    VALUES (?, ?)
                    """,
                    (
                        "admin-initial-password-v1",
                        datetime.now(FUSO_HORARIO).isoformat(),
                    ),
                )


def testar_conexao():
    try:
        with conectar() as conexao:
            conexao.execute("SELECT 1")

        return True

    except sqlite3.Error:
        return False


def linha_para_dict(linha):
    if not linha:
        return None

    return dict(linha)


# =========================================================
# USUÁRIOS
# =========================================================


def buscar_usuario_por_id(usuario_id):
    with conectar() as conexao:
        linha = conexao.execute(
            """
            SELECT *
            FROM usuarios
            WHERE usuario_id = ?
            """,
            (usuario_id,),
        ).fetchone()

    return linha_para_dict(linha)


def buscar_usuario_por_email(email):
    with conectar() as conexao:
        linha = conexao.execute(
            """
            SELECT *
            FROM usuarios
            WHERE email = ?
            """,
            (email,),
        ).fetchone()

    return linha_para_dict(linha)


def buscar_usuario_por_documento(documento):
    with conectar() as conexao:
        linha = conexao.execute(
            """
            SELECT *
            FROM usuarios
            WHERE documento = ?
            """,
            (documento,),
        ).fetchone()

    return linha_para_dict(linha)


def listar_lojistas():
    with conectar() as conexao:
        linhas = conexao.execute("""
            SELECT *
            FROM usuarios
            WHERE tipo_usuario = 'LOJISTA'
            ORDER BY usuario_id
            """).fetchall()

    return [dict(linha) for linha in linhas]


def criar_usuario(
    nome,
    tipo_pessoa,
    documento,
    email,
    telefone,
    senha_hash,
    data_criacao,
    status="ATIVA",
    tipo_usuario="LOJISTA",
):
    with conectar() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO usuarios (
                nome,
                tipo_pessoa,
                documento,
                email,
                telefone,
                senha_hash,
                data_criacao,
                status,
                tipo_usuario
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                nome,
                tipo_pessoa,
                documento,
                email,
                telefone,
                senha_hash,
                data_criacao,
                status,
                tipo_usuario,
            ),
        )

        usuario_id = cursor.lastrowid

    return buscar_usuario_por_id(usuario_id)


def atualizar_status_usuario(usuario_id, status):
    with conectar() as conexao:
        cursor = conexao.execute(
            """
            UPDATE usuarios
            SET status = ?
            WHERE usuario_id = ?
            """,
            (
                status,
                usuario_id,
            ),
        )

    return cursor.rowcount > 0


# =========================================================
# LISTA DE RISCO
# =========================================================


def documento_na_lista_risco(documento):
    with conectar() as conexao:
        linha = conexao.execute(
            """
            SELECT risco_id
            FROM lista_risco
            WHERE documento = ?
            """,
            (documento,),
        ).fetchone()

    return linha is not None


def buscar_item_risco_por_id(risco_id):
    with conectar() as conexao:
        linha = conexao.execute(
            """
            SELECT *
            FROM lista_risco
            WHERE risco_id = ?
            """,
            (risco_id,),
        ).fetchone()

    return linha_para_dict(linha)


def listar_riscos():
    with conectar() as conexao:
        linhas = conexao.execute("""
            SELECT *
            FROM lista_risco
            ORDER BY risco_id
            """).fetchall()

    return [dict(linha) for linha in linhas]


def adicionar_risco(nome, tipo_pessoa, documento, motivo, data_adicao):
    with conectar() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO lista_risco (
                nome,
                tipo_pessoa,
                documento,
                motivo,
                data_adicao
            )
            VALUES (
                ?, ?, ?, ?, ?
            )
            """,
            (
                nome,
                tipo_pessoa,
                documento,
                motivo,
                data_adicao,
            ),
        )

        risco_id = cursor.lastrowid

    return buscar_item_risco_por_id(risco_id)


def remover_risco(risco_id):
    with conectar() as conexao:
        cursor = conexao.execute(
            """
            DELETE FROM lista_risco
            WHERE risco_id = ?
            """,
            (risco_id,),
        )

    return cursor.rowcount > 0


# =========================================================
# TRANSAÇÕES
# =========================================================


def buscar_motivos_transacao(transacao_id):
    with conectar() as conexao:
        linhas = conexao.execute(
            """
            SELECT
                motivo,
                pontos
            FROM motivos_transacao
            WHERE transacao_id = ?
            ORDER BY motivo_id
            """,
            (transacao_id,),
        ).fetchall()

    return [dict(linha) for linha in linhas]


def preparar_transacao(linha):
    if not linha:
        return None

    transacao = dict(linha)

    transacao["revisada"] = bool(transacao["revisada"])

    transacao["motivos_risco"] = buscar_motivos_transacao(transacao["transacao_id"])

    return transacao


def buscar_transacao_por_id(transacao_id):
    with conectar() as conexao:
        linha = conexao.execute(
            """
            SELECT *
            FROM transacoes
            WHERE transacao_id = ?
            """,
            (transacao_id,),
        ).fetchone()

    return preparar_transacao(linha)


def buscar_transacao_por_pedido(lojista_id, pedido_id):
    with conectar() as conexao:
        linha = conexao.execute(
            """
            SELECT *
            FROM transacoes
            WHERE lojista_id = ?
            AND pedido_id = ?
            """,
            (
                lojista_id,
                pedido_id,
            ),
        ).fetchone()

    return preparar_transacao(linha)


def listar_transacoes():
    with conectar() as conexao:
        linhas = conexao.execute("""
            SELECT *
            FROM transacoes
            ORDER BY transacao_id
            """).fetchall()

    return [preparar_transacao(linha) for linha in linhas]


def buscar_transacoes_por_lojista(lojista_id):
    with conectar() as conexao:
        linhas = conexao.execute(
            """
            SELECT *
            FROM transacoes
            WHERE lojista_id = ?
            ORDER BY transacao_id
            """,
            (lojista_id,),
        ).fetchall()

    return [preparar_transacao(linha) for linha in linhas]


def contar_transacoes_recentes(documento, inicio, fim):
    with conectar() as conexao:
        linha = conexao.execute(
            """
            SELECT COUNT(*) AS quantidade
            FROM transacoes
            WHERE comprador_documento = ?
            AND data_hora >= ?
            AND data_hora <= ?
            """,
            (
                documento,
                inicio.isoformat(),
                fim.isoformat(),
            ),
        ).fetchone()

    return linha["quantidade"]


def criar_transacao(dados):
    with conectar() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO transacoes (
                lojista_id,
                pedido_id,
                origem,
                comprador_nome,
                comprador_tipo_pessoa,
                comprador_documento,
                comprador_email,
                valor,
                forma_pagamento,
                pontuacao_risco,
                nivel_risco,
                status_automatico,
                status,
                revisada,
                decisao_revisao,
                data_revisao,
                data_hora
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                dados["lojista_id"],
                dados.get("pedido_id"),
                dados["origem"],
                dados["comprador_nome"],
                dados["comprador_tipo_pessoa"],
                dados["comprador_documento"],
                dados["comprador_email"],
                dados["valor"],
                dados["forma_pagamento"],
                dados["pontuacao_risco"],
                dados["nivel_risco"],
                dados["status_automatico"],
                dados["status"],
                (1 if dados.get("revisada", False) else 0),
                dados.get("decisao_revisao"),
                dados.get("data_revisao"),
                dados["data_hora"],
            ),
        )

        transacao_id = cursor.lastrowid

        for motivo in dados.get("motivos_risco", []):
            conexao.execute(
                """
                INSERT INTO motivos_transacao (
                    transacao_id,
                    motivo,
                    pontos
                )
                VALUES (?, ?, ?)
                """,
                (
                    transacao_id,
                    motivo["motivo"],
                    motivo["pontos"],
                ),
            )

    return buscar_transacao_por_id(transacao_id)


def atualizar_revisao_transacao(transacao_id, status, decisao_revisao, data_revisao):
    """
    Faz a revisão de forma atômica.

    Apenas uma revisão pode alterar a transação.
    """

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            UPDATE transacoes
            SET
                status = ?,
                revisada = 1,
                decisao_revisao = ?,
                data_revisao = ?
            WHERE transacao_id = ?
            AND revisada = 0
            AND status_automatico = 'EM ANÁLISE'
            """,
            (
                status,
                decisao_revisao,
                data_revisao,
                transacao_id,
            ),
        )

    return cursor.rowcount == 1
