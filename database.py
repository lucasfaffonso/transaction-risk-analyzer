import os
import secrets
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANCO = os.path.join(BASE_DIR, "transaction_risk.db")
FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

ADMIN_EMAIL = "admin@risk.com"
MIGRACAO_SENHA_ADMIN = "admin-initial-password-v1"


def conectar():
    conexao = sqlite3.connect(BANCO, timeout=10)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def _linha_para_dict(linha):
    return dict(linha) if linha else None


def _senha_admin_inicial(senha):
    if isinstance(senha, str) and len(senha) >= 12:
        return senha

    senha_gerada = secrets.token_urlsafe(18)

    print("\n[ADMIN] ADMIN_INITIAL_PASSWORD não foi configurada.")
    print(f"[ADMIN] Senha temporária de {ADMIN_EMAIL}: {senha_gerada}\n")

    return senha_gerada


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

        colunas = {
            linha["name"]
            for linha in conexao.execute("PRAGMA table_info(transacoes)").fetchall()
        }

        if "pedido_id" not in colunas:
            conexao.execute("ALTER TABLE transacoes ADD COLUMN pedido_id TEXT")

        conexao.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_transacao_pedido_lojista
            ON transacoes(lojista_id, pedido_id)
            WHERE pedido_id IS NOT NULL AND pedido_id <> ''
        """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS idx_transacao_lojista
            ON transacoes(lojista_id)
        """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS idx_transacao_documento_data
            ON transacoes(comprador_documento, data_hora)
        """)

        _garantir_admin(conexao, senha_admin_inicial)


def _garantir_admin(conexao, senha_admin_inicial):
    admin = conexao.execute(
        """
        SELECT usuario_id
        FROM usuarios
        WHERE email = ?
        """,
        (ADMIN_EMAIL,),
    ).fetchone()

    migracao_aplicada = conexao.execute(
        """
        SELECT 1
        FROM app_migrations
        WHERE migration_id = ?
        """,
        (MIGRACAO_SENHA_ADMIN,),
    ).fetchone()

    if admin and migracao_aplicada:
        return

    senha = _senha_admin_inicial(senha_admin_inicial)

    senha_hash = generate_password_hash(senha)

    if admin:
        conexao.execute(
            """
            UPDATE usuarios
            SET senha_hash = ?
            WHERE usuario_id = ?
            """,
            (senha_hash, admin["usuario_id"]),
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Administrador",
                None,
                None,
                ADMIN_EMAIL,
                None,
                senha_hash,
                datetime.now(FUSO_HORARIO).strftime("%d/%m/%Y"),
                "ATIVA",
                "ADMIN",
            ),
        )

    if not migracao_aplicada:
        conexao.execute(
            """
            INSERT INTO app_migrations (
                migration_id,
                applied_at
            )
            VALUES (?, ?)
            """,
            (
                MIGRACAO_SENHA_ADMIN,
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

    return _linha_para_dict(linha)


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

    return _linha_para_dict(linha)


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

    return _linha_para_dict(linha)


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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        conexao.execute(
            """
            UPDATE usuarios
            SET status = ?
            WHERE usuario_id = ?
            """,
            (status, usuario_id),
        )


# =========================================================
# LISTA DE RISCO
# =========================================================


def documento_na_lista_risco(documento):
    with conectar() as conexao:
        linha = conexao.execute(
            """
            SELECT 1
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

    return _linha_para_dict(linha)


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
            VALUES (?, ?, ?, ?, ?)
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
        conexao.execute(
            """
            DELETE FROM lista_risco
            WHERE risco_id = ?
            """,
            (risco_id,),
        )


# =========================================================
# TRANSAÇÕES
# =========================================================


def _preparar_transacoes(linhas):
    transacoes = [dict(linha) for linha in linhas if linha]

    if not transacoes:
        return []

    ids = [transacao["transacao_id"] for transacao in transacoes]

    placeholders = ",".join("?" for _ in ids)

    with conectar() as conexao:
        linhas_motivos = conexao.execute(
            f"""
            SELECT
                transacao_id,
                motivo,
                pontos
            FROM motivos_transacao
            WHERE transacao_id IN ({placeholders})
            ORDER BY motivo_id
            """,
            ids,
        ).fetchall()

    motivos_por_transacao = {transacao_id: [] for transacao_id in ids}

    for linha in linhas_motivos:
        motivos_por_transacao[linha["transacao_id"]].append(
            {
                "motivo": linha["motivo"],
                "pontos": linha["pontos"],
            }
        )

    for transacao in transacoes:
        transacao["revisada"] = bool(transacao["revisada"])

        transacao["motivos_risco"] = motivos_por_transacao[transacao["transacao_id"]]

    return transacoes


def preparar_transacao(linha):
    transacoes = _preparar_transacoes([linha] if linha else [])

    return transacoes[0] if transacoes else None


def buscar_motivos_transacao(transacao_id):
    transacao = buscar_transacao_por_id(transacao_id)

    if not transacao:
        return []

    return transacao["motivos_risco"]


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
            (lojista_id, pedido_id),
        ).fetchone()

    return preparar_transacao(linha)


def listar_transacoes():
    with conectar() as conexao:
        linhas = conexao.execute("""
            SELECT *
            FROM transacoes
            ORDER BY transacao_id
        """).fetchall()

    return _preparar_transacoes(linhas)


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

    return _preparar_transacoes(linhas)


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
                1 if dados["revisada"] else 0,
                dados["decisao_revisao"],
                dados["data_revisao"],
                dados["data_hora"],
            ),
        )

        transacao_id = cursor.lastrowid

        conexao.executemany(
            """
            INSERT INTO motivos_transacao (
                transacao_id,
                motivo,
                pontos
            )
            VALUES (?, ?, ?)
            """,
            [
                (
                    transacao_id,
                    motivo["motivo"],
                    motivo["pontos"],
                )
                for motivo in dados["motivos_risco"]
            ],
        )

    return buscar_transacao_por_id(transacao_id)


def atualizar_revisao_transacao(
    transacao_id,
    status,
    decisao_revisao,
    data_revisao,
):
    with conectar() as conexao:
        cursor = conexao.execute(
            """
            UPDATE transacoes
            SET status = ?,
                revisada = 1,
                decisao_revisao = ?,
                data_revisao = ?
            WHERE transacao_id = ?
              AND revisada = 0
            """,
            (
                status,
                decisao_revisao,
                data_revisao,
                transacao_id,
            ),
        )

    return cursor.rowcount == 1
