import math
import os
import secrets
import sqlite3
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit
from werkzeug.security import check_password_hash, generate_password_hash

import database as db
from login_throttle import LimitadorTentativasLogin

load_dotenv()

# =========================================================
# CONFIGURAÇÃO
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)

app.json.ensure_ascii = False

socketio = SocketIO(app)

FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

VALOR_ALTO = 3000.00

JANELA_TENTATIVAS_MINUTOS = 10
LIMITE_TENTATIVAS = 3

TOKEN_API_HORAS = 2

MAX_EMAIL_LOGIN = 254
MAX_SENHA_LOGIN = 1024

MIN_SENHA_CADASTRO = 8

MAX_PEDIDO_ID = 80
MAX_NOME_COMPRADOR = 120
MAX_DOCUMENTO_COMPRADOR = 18
MAX_EMAIL_COMPRADOR = 254

MAX_ID_BANCO = (2**63) - 1


usuarios_conectados = {}
tokens_api = {}

limitador_login = LimitadorTentativasLogin()


db.inicializar_banco(os.environ.get("ADMIN_INITIAL_PASSWORD"))


# =========================================================
# VALIDAÇÕES GERAIS
# =========================================================


def extrair_credenciais_login(dados):
    if not isinstance(dados, dict):
        return None

    email = dados.get("email")
    senha = dados.get("senha")

    if not isinstance(email, str) or not isinstance(senha, str):
        return None

    if len(email) > MAX_EMAIL_LOGIN or len(senha) > MAX_SENHA_LOGIN:
        return None

    return (
        email.strip().lower(),
        senha,
    )


def validar_email(email):
    email = email.strip().lower()

    partes = email.split("@")

    if len(partes) != 2:
        return False, "E-mail inválido."

    usuario, dominio = partes

    if not usuario or not dominio:
        return False, "E-mail inválido."

    if "." not in dominio or dominio.startswith(".") or dominio.endswith("."):
        return False, "E-mail inválido."

    return True, email


def validar_documento(documento, tipo_pessoa):
    documento = documento.strip()

    tipo_pessoa = tipo_pessoa.strip().upper()

    if tipo_pessoa not in {
        "PF",
        "PJ",
    }:
        return (False, "Tipo de pessoa inválido.")

    if not documento.isdigit():
        return (False, "Documento deve conter apenas números.")

    if tipo_pessoa == "PF" and len(documento) != 11:
        return (False, "CPF precisa ter 11 dígitos.")

    if tipo_pessoa == "PJ" and len(documento) != 14:
        return (False, "CNPJ precisa ter 14 dígitos.")

    return True, documento


def validar_telefone(telefone):
    telefone = telefone.strip()

    if not telefone.isdigit():
        return (False, "Telefone deve conter apenas números.")

    if len(telefone) not in {
        10,
        11,
    }:
        return (False, "Telefone deve ter 10 ou 11 dígitos.")

    return True, telefone


def validar_campos_texto_payload(dados, limites):
    if not isinstance(dados, dict):
        return False, None

    for campo, limite in limites.items():
        valor = dados.get(campo)

        if valor is None:
            continue

        if not isinstance(valor, str) or len(valor) > limite:
            return False, campo

    return True, None


def extrair_id_positivo_payload(dados, campo):
    if not isinstance(dados, dict):
        return None

    valor = dados.get(campo)

    if isinstance(valor, bool):
        return None

    if isinstance(valor, int):
        identificador = valor

    elif (
        isinstance(valor, str)
        and valor
        and len(valor) <= 19
        and valor.isascii()
        and valor.isdecimal()
    ):
        identificador = int(valor)

    else:
        return None

    if 0 < identificador <= MAX_ID_BANCO:
        return identificador

    return None


def emitir_erro_socket(evento, mensagem, campo=None):
    resposta = {
        "sucesso": False,
        "mensagem": mensagem,
    }

    if campo:
        resposta["campo"] = campo

    emit(
        evento,
        resposta,
    )


# =========================================================
# VALIDAÇÃO DAS TRANSAÇÕES
# =========================================================


def validar_payload_transacao(dados):
    if not isinstance(dados, dict):
        return None, {
            "sucesso": False,
            "campo": "body",
            "mensagem": ("O corpo da requisição " "deve ser um objeto JSON."),
        }

    pedido_id = dados.get(
        "pedido_id",
        "",
    )

    if pedido_id is None:
        pedido_id = ""

    if isinstance(pedido_id, bool) or not isinstance(
        pedido_id,
        (str, int),
    ):
        return None, {
            "sucesso": False,
            "campo": "pedido_id",
            "mensagem": ("O ID do pedido deve ser texto."),
        }

    pedido_id = str(pedido_id).strip()

    if not pedido_id:
        return None, {
            "sucesso": False,
            "campo": "pedido_id",
            "mensagem": ("Informe o ID do pedido."),
        }

    if len(pedido_id) > MAX_PEDIDO_ID:
        return None, {
            "sucesso": False,
            "campo": "pedido_id",
            "mensagem": (
                f"O ID do pedido deve ter " f"no máximo {MAX_PEDIDO_ID} " f"caracteres."
            ),
        }

    limites_texto = {
        "comprador_nome": MAX_NOME_COMPRADOR,
        "comprador_tipo_pessoa": 2,
        "comprador_documento": MAX_DOCUMENTO_COMPRADOR,
        "comprador_email": MAX_EMAIL_COMPRADOR,
        "forma_pagamento": 10,
    }

    payload = {
        "pedido_id": pedido_id,
    }

    for campo, limite in limites_texto.items():
        valor = dados.get(
            campo,
            "",
        )

        if valor is None:
            valor = ""

        if not isinstance(
            valor,
            str,
        ):
            return None, {
                "sucesso": False,
                "campo": campo,
                "mensagem": ("Este campo deve ser texto."),
            }

        if len(valor) > limite:
            return None, {
                "sucesso": False,
                "campo": campo,
                "mensagem": (
                    f"Este campo deve ter " f"no máximo {limite} " f"caracteres."
                ),
            }

        payload[campo] = valor.strip()

    payload["comprador_tipo_pessoa"] = payload["comprador_tipo_pessoa"].upper()

    payload["comprador_documento"] = (
        payload["comprador_documento"]
        .replace(".", "")
        .replace("-", "")
        .replace("/", "")
    )

    payload["comprador_email"] = payload["comprador_email"].lower()

    payload["forma_pagamento"] = payload["forma_pagamento"].upper()

    valor_bruto = dados.get("valor")

    if isinstance(valor_bruto, bool) or not isinstance(
        valor_bruto,
        (int, float, str),
    ):
        return None, {
            "sucesso": False,
            "campo": "transacao_valor",
            "mensagem": ("Informe um valor numérico válido."),
        }

    try:
        valor = float(valor_bruto)

    except (
        TypeError,
        ValueError,
        OverflowError,
    ):
        return None, {
            "sucesso": False,
            "campo": "transacao_valor",
            "mensagem": ("Informe um valor numérico válido."),
        }

    if not math.isfinite(valor):
        return None, {
            "sucesso": False,
            "campo": "transacao_valor",
            "mensagem": ("O valor deve ser um número finito."),
        }

    valor = round(
        valor,
        2,
    )

    if valor <= 0:
        return None, {
            "sucesso": False,
            "campo": "transacao_valor",
            "mensagem": ("O valor deve ser maior que zero."),
        }

    payload["valor"] = valor

    return payload, None


# =========================================================
# AUTENTICAÇÃO
# =========================================================


def autenticar_com_limite(email, senha):
    chave, retry_after = limitador_login.iniciar(
        request.remote_addr,
        email,
    )

    if retry_after:
        return None, retry_after

    try:
        usuario = db.buscar_usuario_por_email(email)

        senha_correta = bool(
            usuario
            and check_password_hash(
                usuario["senha_hash"],
                senha,
            )
        )

    except Exception:
        limitador_login.finalizar(chave)
        raise

    limitador_login.finalizar(
        chave,
        falhou=not senha_correta,
    )

    return (usuario if senha_correta else None), 0


def buscar_usuario_logado():
    usuario_id = usuarios_conectados.get(request.sid)

    if usuario_id is None:
        return None

    usuario = db.buscar_usuario_por_id(usuario_id)

    if not usuario:
        usuarios_conectados.pop(
            request.sid,
            None,
        )

        return None

    if usuario["status"] != "ATIVA":
        usuarios_conectados.pop(
            request.sid,
            None,
        )

        return None

    return usuario


# =========================================================
# TOKENS DA API
# =========================================================


def obter_token_api():
    autorizacao = request.headers.get(
        "Authorization",
        "",
    )

    if not autorizacao.startswith("Bearer "):
        return None

    return autorizacao[len("Bearer ") :].strip()


def criar_token_api(usuario_id):
    token = secrets.token_urlsafe(32)

    tokens_api[token] = {
        "usuario_id": usuario_id,
        "expira_em": (time.time() + (TOKEN_API_HORAS * 60 * 60)),
    }

    return token


def buscar_usuario_api():
    token = obter_token_api()

    if not token:
        return None

    sessao = tokens_api.get(token)

    if not sessao:
        return None

    if time.time() >= sessao["expira_em"]:
        tokens_api.pop(
            token,
            None,
        )

        return None

    usuario = db.buscar_usuario_por_id(sessao["usuario_id"])

    if not usuario or usuario["status"] != "ATIVA":
        tokens_api.pop(
            token,
            None,
        )

        return None

    return usuario


def encerrar_sessoes_usuario(usuario_id):
    sessoes = [
        sid
        for sid, id_conectado in usuarios_conectados.items()
        if id_conectado == usuario_id
    ]

    for sid in sessoes:
        usuarios_conectados.pop(
            sid,
            None,
        )

    tokens = [
        token
        for token, sessao in tokens_api.items()
        if sessao["usuario_id"] == usuario_id
    ]

    for token in tokens:
        tokens_api.pop(
            token,
            None,
        )


# =========================================================
# OBJETOS PÚBLICOS
# =========================================================


def usuario_publico(usuario):
    return {
        "usuario_id": usuario["usuario_id"],
        "nome": usuario["nome"],
        "tipo_pessoa": usuario["tipo_pessoa"],
        "documento": usuario["documento"],
        "email": usuario["email"],
        "telefone": usuario["telefone"],
        "data_criacao": usuario["data_criacao"],
        "status": usuario["status"],
        "tipo_usuario": usuario["tipo_usuario"],
    }


def item_risco_publico(item):
    return {
        "risco_id": item["risco_id"],
        "nome": item["nome"],
        "tipo_pessoa": item["tipo_pessoa"],
        "documento": item["documento"],
        "motivo": item["motivo"],
        "data_adicao": item["data_adicao"],
    }


def transacao_publica(transacao):
    data_hora = datetime.fromisoformat(transacao["data_hora"])

    return {
        "transacao_id": transacao["transacao_id"],
        "lojista_id": transacao["lojista_id"],
        "pedido_id": transacao.get("pedido_id"),
        "origem": transacao.get(
            "origem",
            "WEB",
        ),
        "comprador_nome": transacao["comprador_nome"],
        "comprador_tipo_pessoa": transacao["comprador_tipo_pessoa"],
        "comprador_documento": transacao["comprador_documento"],
        "comprador_email": transacao["comprador_email"],
        "valor": transacao["valor"],
        "forma_pagamento": transacao["forma_pagamento"],
        "pontuacao_risco": transacao["pontuacao_risco"],
        "nivel_risco": transacao["nivel_risco"],
        "status_automatico": transacao["status_automatico"],
        "status": transacao["status"],
        "motivos_risco": transacao["motivos_risco"],
        "revisada": transacao["revisada"],
        "decisao_revisao": transacao["decisao_revisao"],
        "data_revisao": transacao["data_revisao"],
        "data_hora": data_hora.strftime("%d/%m/%Y %H:%M:%S"),
    }


def transacao_admin_publica(transacao):
    dados = transacao_publica(transacao)

    lojista = db.buscar_usuario_por_id(transacao["lojista_id"])

    if lojista:
        dados["lojista_nome"] = lojista["nome"]

        dados["lojista_email"] = lojista["email"]

    else:
        dados["lojista_nome"] = "Lojista não encontrado"

        dados["lojista_email"] = ""

    return dados


# =========================================================
# MOTOR DE RISCO
# =========================================================


def contar_transacoes_recentes(documento, data_hora):
    inicio = data_hora - timedelta(minutes=(JANELA_TENTATIVAS_MINUTOS))

    return db.contar_transacoes_recentes(
        documento,
        inicio,
        data_hora,
    )


def analisar_risco(documento, valor, data_hora):
    pontuacao = 0
    motivos = []

    if db.documento_na_lista_risco(documento):
        pontuacao += 50

        motivos.append(
            {
                "motivo": ("Comprador presente " "na lista de risco"),
                "pontos": 50,
            }
        )

    if 0 <= data_hora.hour < 6:
        pontuacao += 20

        motivos.append(
            {
                "motivo": ("Transação realizada " "em horário incomum"),
                "pontos": 20,
            }
        )

    if valor >= VALOR_ALTO:
        pontuacao += 30

        motivos.append(
            {
                "motivo": ("Valor elevado " "da transação"),
                "pontos": 30,
            }
        )

    tentativas = contar_transacoes_recentes(
        documento,
        data_hora,
    )

    if tentativas >= LIMITE_TENTATIVAS - 1:
        pontuacao += 40

        motivos.append(
            {
                "motivo": ("Múltiplas tentativas " "em curto período"),
                "pontos": 40,
            }
        )

    if pontuacao <= 29:
        nivel = "BAIXO"
        status = "APROVADA"

    elif pontuacao <= 59:
        nivel = "MÉDIO"

        status = "APROVADA COM ALERTA"

    elif pontuacao <= 89:
        nivel = "ALTO"
        status = "EM ANÁLISE"

    else:
        nivel = "CRÍTICO"
        status = "BLOQUEADA"

    return (
        pontuacao,
        nivel,
        status,
        motivos,
    )


# =========================================================
# PROCESSAMENTO DE TRANSAÇÕES
# =========================================================


def processar_transacao(
    lojista,
    dados,
    origem="WEB",
):
    dados, erro = validar_payload_transacao(dados)

    if erro:
        return erro

    pedido_id = dados["pedido_id"]

    comprador_nome = dados["comprador_nome"]

    comprador_tipo_pessoa = dados["comprador_tipo_pessoa"]

    comprador_documento = dados["comprador_documento"]

    comprador_email = dados["comprador_email"]

    valor = dados["valor"]

    forma_pagamento = dados["forma_pagamento"]

    transacao_existente = db.buscar_transacao_por_pedido(
        lojista["usuario_id"],
        pedido_id,
    )

    if transacao_existente:
        return {
            "sucesso": True,
            "duplicada": True,
            "mensagem": (
                "Este pedido já foi analisado. " "O resultado anterior foi reutilizado."
            ),
            "transacao": transacao_publica(transacao_existente),
        }

    if not comprador_nome:
        return {
            "sucesso": False,
            "campo": "comprador_nome",
            "mensagem": "Informe o nome do comprador.",
        }

    valido, resultado = validar_documento(
        comprador_documento,
        comprador_tipo_pessoa,
    )

    if not valido:
        return {
            "sucesso": False,
            "campo": "comprador_documento",
            "mensagem": resultado,
        }

    comprador_documento = resultado

    valido, resultado = validar_email(comprador_email)

    if not valido:
        return {
            "sucesso": False,
            "campo": "comprador_email",
            "mensagem": resultado,
        }

    comprador_email = resultado

    if forma_pagamento not in {
        "CARTAO",
        "PIX",
        "BOLETO",
    }:
        return {
            "sucesso": False,
            "mensagem": ("Forma de pagamento inválida."),
        }

    data_hora = datetime.now(FUSO_HORARIO)

    (
        pontuacao,
        nivel,
        status,
        motivos,
    ) = analisar_risco(
        comprador_documento,
        valor,
        data_hora,
    )

    dados_transacao = {
        "lojista_id": lojista["usuario_id"],
        "pedido_id": pedido_id,
        "origem": origem,
        "comprador_nome": comprador_nome,
        "comprador_tipo_pessoa": comprador_tipo_pessoa,
        "comprador_documento": comprador_documento,
        "comprador_email": comprador_email,
        "valor": valor,
        "forma_pagamento": forma_pagamento,
        "pontuacao_risco": pontuacao,
        "nivel_risco": nivel,
        "status_automatico": status,
        "status": status,
        "motivos_risco": motivos,
        "revisada": False,
        "decisao_revisao": None,
        "data_revisao": None,
        "data_hora": data_hora.isoformat(),
    }

    try:
        nova_transacao = db.criar_transacao(dados_transacao)

    except sqlite3.IntegrityError:
        transacao_existente = db.buscar_transacao_por_pedido(
            lojista["usuario_id"],
            pedido_id,
        )

        if transacao_existente:
            return {
                "sucesso": True,
                "duplicada": True,
                "mensagem": (
                    "Este pedido já foi analisado. "
                    "O resultado anterior foi reutilizado."
                ),
                "transacao": transacao_publica(transacao_existente),
            }

        raise

    return {
        "sucesso": True,
        "transacao": transacao_publica(nova_transacao),
    }


# =========================================================
# RESUMOS E ESTATÍSTICAS
# =========================================================


def gerar_resumo_lojista(lojista_id):
    transacoes = db.buscar_transacoes_por_lojista(lojista_id)

    return {
        "total": len(transacoes),
        "em_analise": sum(
            1 for transacao in transacoes if transacao["status"] == "EM ANÁLISE"
        ),
        "bloqueadas": sum(
            1 for transacao in transacoes if transacao["status"] == "BLOQUEADA"
        ),
    }


def gerar_resumo_admin():
    transacoes = db.listar_transacoes()

    return {
        "lojistas": len(db.listar_lojistas()),
        "transacoes": len(transacoes),
        "em_analise": sum(
            1 for transacao in transacoes if transacao["status"] == "EM ANÁLISE"
        ),
        "bloqueadas": sum(
            1 for transacao in transacoes if transacao["status"] == "BLOQUEADA"
        ),
    }


def gerar_estatisticas(transacoes):
    total = len(transacoes)

    valor_total = sum(transacao["valor"] for transacao in transacoes)

    soma_scores = sum(transacao["pontuacao_risco"] for transacao in transacoes)

    return {
        "total": total,
        "aprovadas": sum(
            1 for transacao in transacoes if transacao["status"] == "APROVADA"
        ),
        "aprovadas_alerta": sum(
            1
            for transacao in transacoes
            if transacao["status"] == ("APROVADA COM ALERTA")
        ),
        "em_analise": sum(
            1 for transacao in transacoes if transacao["status"] == "EM ANÁLISE"
        ),
        "bloqueadas": sum(
            1 for transacao in transacoes if transacao["status"] == "BLOQUEADA"
        ),
        "risco_baixo": sum(
            1 for transacao in transacoes if transacao["nivel_risco"] == "BAIXO"
        ),
        "risco_medio": sum(
            1 for transacao in transacoes if transacao["nivel_risco"] == "MÉDIO"
        ),
        "risco_alto": sum(
            1 for transacao in transacoes if transacao["nivel_risco"] == "ALTO"
        ),
        "risco_critico": sum(
            1 for transacao in transacoes if transacao["nivel_risco"] == "CRÍTICO"
        ),
        "revisoes": sum(1 for transacao in transacoes if transacao["revisada"]),
        "revisoes_aprovadas": sum(
            1 for transacao in transacoes if transacao["decisao_revisao"] == "APROVADA"
        ),
        "revisoes_bloqueadas": sum(
            1 for transacao in transacoes if transacao["decisao_revisao"] == "BLOQUEADA"
        ),
        "valor_total": round(
            valor_total,
            2,
        ),
        "ticket_medio": (
            round(
                valor_total / total,
                2,
            )
            if total
            else 0
        ),
        "score_medio": (
            round(
                soma_scores / total,
                1,
            )
            if total
            else 0
        ),
    }


# =========================================================
# ATUALIZAÇÕES EM TEMPO REAL
# =========================================================


def atualizar_web_lojista(lojista_id):
    transacoes = db.buscar_transacoes_por_lojista(lojista_id)

    lista = [transacao_publica(transacao) for transacao in reversed(transacoes)]

    resumo = gerar_resumo_lojista(lojista_id)

    for sid, usuario_id in list(usuarios_conectados.items()):
        if usuario_id != lojista_id:
            continue

        socketio.emit(
            "lista_minhas_transacoes",
            lista,
            to=sid,
        )

        socketio.emit(
            "resumo_lojista",
            resumo,
            to=sid,
        )


def atualizar_web_admin():
    transacoes = db.listar_transacoes()

    lista = [transacao_admin_publica(transacao) for transacao in reversed(transacoes)]

    resumo = gerar_resumo_admin()

    for sid, usuario_id in list(usuarios_conectados.items()):
        usuario = db.buscar_usuario_por_id(usuario_id)

        if usuario and usuario["tipo_usuario"] == "ADMIN":
            socketio.emit(
                "lista_transacoes_admin",
                lista,
                to=sid,
            )

            socketio.emit(
                "resumo_admin",
                resumo,
                to=sid,
            )


# =========================================================
# ROTAS WEB
# =========================================================


@app.get("/")
def index():
    return render_template("index.html")


# =========================================================
# API REST
# =========================================================


@app.get("/api/v1/health")
def api_health():
    banco_ok = db.testar_conexao()

    return jsonify(
        {
            "sucesso": banco_ok,
            "servico": "Transaction Risk Analyzer",
            "status": ("online" if banco_ok else "erro"),
            "versao": "1.0",
            "database": {
                "tipo": "SQLite",
                "status": ("conectado" if banco_ok else "desconectado"),
            },
        }
    ), (200 if banco_ok else 500)


@app.post("/api/v1/login")
def api_login():
    credenciais = extrair_credenciais_login(request.get_json(silent=True))

    if credenciais is None:
        return (
            jsonify(
                {
                    "sucesso": False,
                    "mensagem": "Dados de login inválidos.",
                }
            ),
            400,
        )

    email, senha = credenciais

    (
        usuario,
        retry_after,
    ) = autenticar_com_limite(
        email,
        senha,
    )

    if retry_after:
        resposta = jsonify(
            {
                "sucesso": False,
                "mensagem": (
                    "Muitas tentativas de login. " "Aguarde antes de tentar novamente."
                ),
            }
        )

        resposta.headers["Retry-After"] = str(retry_after)

        return resposta, 429

    if not usuario:
        return (
            jsonify(
                {
                    "sucesso": False,
                    "mensagem": "E-mail ou senha inválidos.",
                }
            ),
            401,
        )

    if usuario["status"] != "ATIVA":
        return (
            jsonify(
                {
                    "sucesso": False,
                    "mensagem": "Esta conta está inativa.",
                }
            ),
            403,
        )

    if usuario["tipo_usuario"] != "LOJISTA":
        return (
            jsonify(
                {
                    "sucesso": False,
                    "mensagem": (
                        "A API externa está disponível " "apenas para lojistas."
                    ),
                }
            ),
            403,
        )

    token = criar_token_api(usuario["usuario_id"])

    return jsonify(
        {
            "sucesso": True,
            "token": token,
            "expira_em_horas": TOKEN_API_HORAS,
            "usuario": usuario_publico(usuario),
        }
    )


@app.post("/api/v1/logout")
def api_logout():
    token = obter_token_api()

    if token:
        tokens_api.pop(
            token,
            None,
        )

    return jsonify(
        {
            "sucesso": True,
            "mensagem": "Logout realizado com sucesso.",
        }
    )


@app.post("/api/v1/transacoes/analisar")
def api_analisar_transacao():
    lojista = buscar_usuario_api()

    if not lojista:
        return (
            jsonify(
                {
                    "sucesso": False,
                    "mensagem": ("Token inválido, expirado " "ou não informado."),
                }
            ),
            401,
        )

    if lojista["tipo_usuario"] != "LOJISTA":
        return (
            jsonify(
                {
                    "sucesso": False,
                    "mensagem": "Operação não permitida.",
                }
            ),
            403,
        )

    resultado = processar_transacao(
        lojista,
        request.get_json(silent=True),
        origem="API",
    )

    if not resultado["sucesso"]:
        return jsonify(resultado), 400

    if resultado.get("duplicada"):
        return jsonify(resultado), 200

    atualizar_web_lojista(lojista["usuario_id"])

    atualizar_web_admin()

    return jsonify(resultado), 201


@app.get("/api/v1/transacoes")
def api_listar_transacoes():
    lojista = buscar_usuario_api()

    if not lojista:
        return (
            jsonify(
                {
                    "sucesso": False,
                    "mensagem": ("Token inválido, expirado " "ou não informado."),
                }
            ),
            401,
        )

    transacoes = db.buscar_transacoes_por_lojista(lojista["usuario_id"])

    return jsonify(
        {
            "sucesso": True,
            "transacoes": [
                transacao_publica(transacao) for transacao in reversed(transacoes)
            ],
        }
    )


# =========================================================
# SOCKET.IO - VERIFICAÇÃO DE CADASTRO
# =========================================================


@socketio.on("verificar_campo_cadastro")
def verificar_campo_cadastro(dados):
    if not isinstance(
        dados,
        dict,
    ):
        emitir_erro_socket(
            "resultado_verificacao_cadastro",
            "Dados de verificação inválidos.",
        )

        return

    campo = dados.get("campo")

    if campo not in {
        "documento",
        "email",
    }:
        return

    valor = dados.get("valor")

    if not isinstance(
        valor,
        str,
    ):
        return

    valor = valor.strip()

    if campo == "documento":
        if len(valor) > MAX_DOCUMENTO_COMPRADOR:
            return

        documento = valor.replace(".", "").replace("-", "").replace("/", "")

        tipo_pessoa = "PF" if len(documento) <= 11 else "PJ"

        valido, mensagem = validar_documento(
            documento,
            tipo_pessoa,
        )

        if not valido:
            emit(
                "resultado_verificacao_cadastro",
                {
                    "campo": "cadastro_documento",
                    "disponivel": False,
                    "mensagem": mensagem,
                },
            )

            return

        if db.buscar_usuario_por_documento(documento):
            emit(
                "resultado_verificacao_cadastro",
                {
                    "campo": "cadastro_documento",
                    "disponivel": False,
                    "mensagem": "Documento já cadastrado.",
                },
            )

            return

    if campo == "email":
        if len(valor) > MAX_EMAIL_COMPRADOR:
            return

        valido, email = validar_email(valor)

        if not valido:
            emit(
                "resultado_verificacao_cadastro",
                {
                    "campo": "cadastro_email",
                    "disponivel": False,
                    "mensagem": email,
                },
            )

            return

        if db.buscar_usuario_por_email(email):
            emit(
                "resultado_verificacao_cadastro",
                {
                    "campo": "cadastro_email",
                    "disponivel": False,
                    "mensagem": "E-mail já cadastrado.",
                },
            )

            return

    emit(
        "resultado_verificacao_cadastro",
        {
            "campo": f"cadastro_{campo}",
            "disponivel": True,
        },
    )


# =========================================================
# SOCKET.IO - CADASTRO
# =========================================================


@socketio.on("cadastrar_usuario")
def cadastrar_usuario_socket(dados):
    limites = {
        "nome": MAX_NOME_COMPRADOR,
        "tipo_pessoa": 2,
        "documento": MAX_DOCUMENTO_COMPRADOR,
        "email": MAX_EMAIL_COMPRADOR,
        "telefone": 20,
        "senha": MAX_SENHA_LOGIN,
    }

    (
        payload_valido,
        campo_invalido,
    ) = validar_campos_texto_payload(
        dados,
        limites,
    )

    if not payload_valido:
        emitir_erro_socket(
            "resultado_cadastro",
            ("Dados de cadastro inválidos " "ou muito longos."),
            (f"cadastro_{campo_invalido}" if campo_invalido else None),
        )

        return

    nome = (dados.get("nome") or "").strip()

    tipo_pessoa = (dados.get("tipo_pessoa") or "").strip().upper()

    documento = (
        (dados.get("documento") or "")
        .strip()
        .replace(".", "")
        .replace("-", "")
        .replace("/", "")
    )

    email = (dados.get("email") or "").strip().lower()

    telefone = (
        (dados.get("telefone") or "")
        .strip()
        .replace("(", "")
        .replace(")", "")
        .replace("-", "")
        .replace(" ", "")
    )

    senha = dados.get("senha") or ""

    if not nome:
        emitir_erro_socket(
            "resultado_cadastro",
            "Informe seu nome.",
            "cadastro_nome",
        )

        return

    valido, documento = validar_documento(
        documento,
        tipo_pessoa,
    )

    if not valido:
        emitir_erro_socket(
            "resultado_cadastro",
            documento,
            "cadastro_documento",
        )

        return

    if db.buscar_usuario_por_documento(documento):
        emitir_erro_socket(
            "resultado_cadastro",
            "Documento já cadastrado.",
            "cadastro_documento",
        )

        return

    valido, email = validar_email(email)

    if not valido:
        emitir_erro_socket(
            "resultado_cadastro",
            email,
            "cadastro_email",
        )

        return

    if db.buscar_usuario_por_email(email):
        emitir_erro_socket(
            "resultado_cadastro",
            "E-mail já cadastrado.",
            "cadastro_email",
        )

        return

    valido, telefone = validar_telefone(telefone)

    if not valido:
        emitir_erro_socket(
            "resultado_cadastro",
            telefone,
            "cadastro_telefone",
        )

        return

    if len(senha) < MIN_SENHA_CADASTRO:
        emitir_erro_socket(
            "resultado_cadastro",
            ("A senha deve ter pelo menos " f"{MIN_SENHA_CADASTRO} caracteres."),
            "cadastro_senha",
        )

        return

    try:
        novo_usuario = db.criar_usuario(
            nome=nome,
            tipo_pessoa=tipo_pessoa,
            documento=documento,
            email=email,
            telefone=telefone,
            senha_hash=(generate_password_hash(senha)),
            data_criacao=(datetime.now(FUSO_HORARIO).strftime("%d/%m/%Y")),
            status="ATIVA",
            tipo_usuario="LOJISTA",
        )

    except sqlite3.IntegrityError:
        emitir_erro_socket(
            "resultado_cadastro",
            ("E-mail ou documento " "já cadastrado."),
        )

        return

    usuarios_conectados[request.sid] = novo_usuario["usuario_id"]

    emit(
        "resultado_cadastro",
        {
            "sucesso": True,
            "mensagem": "Conta criada com sucesso!",
            "usuario": usuario_publico(novo_usuario),
        },
    )


# =========================================================
# SOCKET.IO - LOGIN
# =========================================================


@socketio.on("login")
def login_socket(dados):
    credenciais = extrair_credenciais_login(dados)

    if credenciais is None:
        emitir_erro_socket(
            "resultado_login",
            "Dados de login inválidos.",
        )

        return

    email, senha = credenciais

    (
        usuario,
        retry_after,
    ) = autenticar_com_limite(
        email,
        senha,
    )

    if retry_after:
        emit(
            "resultado_login",
            {
                "sucesso": False,
                "mensagem": (
                    "Muitas tentativas de login. " "Aguarde antes de tentar novamente."
                ),
                "retry_after": retry_after,
            },
        )

        return

    if not usuario:
        emitir_erro_socket(
            "resultado_login",
            "E-mail ou senha inválidos.",
        )

        return

    if usuario["status"] != "ATIVA":
        emitir_erro_socket(
            "resultado_login",
            "Esta conta está inativa.",
        )

        return

    usuarios_conectados[request.sid] = usuario["usuario_id"]

    emit(
        "resultado_login",
        {
            "sucesso": True,
            "usuario": usuario_publico(usuario),
        },
    )


# =========================================================
# SOCKET.IO - PEDIDO
# =========================================================


@socketio.on("verificar_pedido_id")
def verificar_pedido_id_socket(dados):
    lojista = buscar_usuario_logado()

    if not lojista or lojista["tipo_usuario"] != "LOJISTA":
        emit(
            "resultado_verificacao_pedido",
            {
                "sucesso": False,
                "mensagem": "Usuário não autenticado.",
            },
        )
        return

    if not isinstance(dados, dict):
        emit(
            "resultado_verificacao_pedido",
            {
                "sucesso": False,
                "mensagem": "Dados de verificação inválidos.",
            },
        )
        return

    pedido_id = dados.get(
        "pedido_id",
        "",
    )

    if pedido_id is None:
        pedido_id = ""

    if isinstance(pedido_id, bool) or not isinstance(
        pedido_id,
        (str, int),
    ):
        emit(
            "resultado_verificacao_pedido",
            {
                "sucesso": False,
                "mensagem": "O ID do pedido é inválido.",
            },
        )
        return

    pedido_id = str(pedido_id).strip()

    if not pedido_id:
        emit(
            "resultado_verificacao_pedido",
            {
                "sucesso": False,
                "mensagem": "Informe o ID do pedido.",
            },
        )
        return

    if len(pedido_id) > MAX_PEDIDO_ID:
        emit(
            "resultado_verificacao_pedido",
            {
                "sucesso": False,
                "mensagem": (
                    f"O ID do pedido deve ter no máximo " f"{MAX_PEDIDO_ID} caracteres."
                ),
            },
        )
        return

    transacao = db.buscar_transacao_por_pedido(
        lojista["usuario_id"],
        pedido_id,
    )

    if transacao:
        emit(
            "resultado_verificacao_pedido",
            {
                "sucesso": True,
                "pedido_id": pedido_id,
                "existe": True,
                "mensagem": (
                    "Este pedido já foi analisado. "
                    "O resultado anterior foi reutilizado."
                ),
                "transacao": transacao_publica(transacao),
            },
        )
        return

    emit(
        "resultado_verificacao_pedido",
        {
            "sucesso": True,
            "pedido_id": pedido_id,
            "existe": False,
            "mensagem": (
                "Pedido ainda não analisado. " "Preencha os dados da transação."
            ),
        },
    )


# =========================================================
# SOCKET.IO - TRANSAÇÕES DO LOJISTA
# =========================================================


@socketio.on("analisar_transacao")
def analisar_transacao_socket(dados):
    lojista = buscar_usuario_logado()

    if not lojista:
        emitir_erro_socket(
            "resultado_analise",
            "Usuário não autenticado.",
        )

        return

    if lojista["tipo_usuario"] != "LOJISTA":
        emitir_erro_socket(
            "resultado_analise",
            "Operação não permitida.",
        )

        return

    resultado = processar_transacao(
        lojista,
        dados,
        origem="WEB",
    )

    emit(
        "resultado_analise",
        resultado,
    )

    if resultado["sucesso"] and not resultado.get("duplicada"):
        atualizar_web_lojista(lojista["usuario_id"])

        atualizar_web_admin()


@socketio.on("listar_minhas_transacoes")
def listar_minhas_transacoes_socket():
    lojista = buscar_usuario_logado()

    if not lojista or lojista["tipo_usuario"] != "LOJISTA":
        return

    transacoes = db.buscar_transacoes_por_lojista(lojista["usuario_id"])

    emit(
        "lista_minhas_transacoes",
        [transacao_publica(transacao) for transacao in reversed(transacoes)],
    )

    emit(
        "resumo_lojista",
        gerar_resumo_lojista(lojista["usuario_id"]),
    )


@socketio.on("obter_estatisticas_lojista")
def obter_estatisticas_lojista_socket():
    lojista = buscar_usuario_logado()

    if not lojista or lojista["tipo_usuario"] != "LOJISTA":
        return

    transacoes = db.buscar_transacoes_por_lojista(lojista["usuario_id"])

    emit(
        "estatisticas_lojista",
        gerar_estatisticas(transacoes),
    )


# =========================================================
# SOCKET.IO - ADMIN
# =========================================================


@socketio.on("obter_resumo_admin")
def obter_resumo_admin_socket():
    admin = buscar_usuario_logado()

    if not admin or admin["tipo_usuario"] != "ADMIN":
        return

    emit(
        "resumo_admin",
        gerar_resumo_admin(),
    )


@socketio.on("obter_estatisticas_admin")
def obter_estatisticas_admin_socket():
    admin = buscar_usuario_logado()

    if not admin or admin["tipo_usuario"] != "ADMIN":
        return

    emit(
        "estatisticas_admin",
        gerar_estatisticas(db.listar_transacoes()),
    )


@socketio.on("listar_transacoes_admin")
def listar_transacoes_admin_socket():
    admin = buscar_usuario_logado()

    if not admin:
        emitir_erro_socket(
            "resultado_transacoes_admin",
            "Usuário não autenticado.",
        )

        return

    if admin["tipo_usuario"] != "ADMIN":
        emitir_erro_socket(
            "resultado_transacoes_admin",
            "Operação não permitida.",
        )

        return

    transacoes = db.listar_transacoes()

    emit(
        "lista_transacoes_admin",
        [transacao_admin_publica(transacao) for transacao in reversed(transacoes)],
    )

    emit(
        "resumo_admin",
        gerar_resumo_admin(),
    )


# =========================================================
# SOCKET.IO - REVISÃO MANUAL
# =========================================================


@socketio.on("revisar_transacao")
def revisar_transacao_socket(dados):
    admin = buscar_usuario_logado()

    if not admin:
        emitir_erro_socket(
            "resultado_revisao",
            "Usuário não autenticado.",
        )

        return

    if admin["tipo_usuario"] != "ADMIN":
        emitir_erro_socket(
            "resultado_revisao",
            "Operação não permitida.",
        )

        return

    valido, campo = validar_campos_texto_payload(
        dados,
        {"decisao": 10},
    )

    if not valido:
        emitir_erro_socket(
            "resultado_revisao",
            "Dados de revisão inválidos.",
            campo,
        )

        return

    transacao_id = extrair_id_positivo_payload(
        dados,
        "transacao_id",
    )

    if transacao_id is None:
        emitir_erro_socket(
            "resultado_revisao",
            "Transação inválida.",
        )

        return

    decisao = (dados.get("decisao") or "").strip().upper()

    if decisao not in {
        "APROVAR",
        "BLOQUEAR",
    }:
        emitir_erro_socket(
            "resultado_revisao",
            "Decisão inválida.",
        )

        return

    transacao = db.buscar_transacao_por_id(transacao_id)

    if not transacao:
        emitir_erro_socket(
            "resultado_revisao",
            "Transação não encontrada.",
        )

        return

    if transacao["status_automatico"] != "EM ANÁLISE":
        emitir_erro_socket(
            "resultado_revisao",
            ("Esta transação não precisa " "de revisão manual."),
        )

        return

    if transacao["revisada"]:
        emitir_erro_socket(
            "resultado_revisao",
            "Esta transação já foi revisada.",
        )

        return

    if decisao == "APROVAR":
        novo_status = "APROVADA"
        decisao_revisao = "APROVADA"

    else:
        novo_status = "BLOQUEADA"
        decisao_revisao = "BLOQUEADA"

    data_revisao = datetime.now(FUSO_HORARIO).strftime("%d/%m/%Y %H:%M:%S")

    revisada = db.atualizar_revisao_transacao(
        transacao_id=transacao_id,
        status=novo_status,
        decisao_revisao=decisao_revisao,
        data_revisao=data_revisao,
    )

    if not revisada:
        emitir_erro_socket(
            "resultado_revisao",
            "Esta transação já foi revisada.",
        )

        return

    emit(
        "resultado_revisao",
        {
            "sucesso": True,
            "mensagem": "Transação revisada com sucesso.",
        },
    )

    atualizar_web_lojista(transacao["lojista_id"])

    atualizar_web_admin()


# =========================================================
# SOCKET.IO - USUÁRIOS DO ADMIN
# =========================================================


@socketio.on("listar_usuarios_admin")
def listar_usuarios_admin_socket():
    admin = buscar_usuario_logado()

    if not admin:
        emitir_erro_socket(
            "resultado_usuarios_admin",
            "Usuário não autenticado.",
        )

        return

    if admin["tipo_usuario"] != "ADMIN":
        emitir_erro_socket(
            "resultado_usuarios_admin",
            "Operação não permitida.",
        )

        return

    emit(
        "lista_usuarios_admin",
        [usuario_publico(usuario) for usuario in db.listar_lojistas()],
    )


@socketio.on("alterar_status_usuario")
def alterar_status_usuario_socket(dados):
    admin = buscar_usuario_logado()

    if not admin:
        emitir_erro_socket(
            "resultado_status_usuario",
            "Usuário não autenticado.",
        )

        return

    if admin["tipo_usuario"] != "ADMIN":
        emitir_erro_socket(
            "resultado_status_usuario",
            "Operação não permitida.",
        )

        return

    valido, _ = validar_campos_texto_payload(
        dados,
        {"status": 10},
    )

    usuario_id = extrair_id_positivo_payload(
        dados,
        "usuario_id",
    )

    if not valido or usuario_id is None:
        emitir_erro_socket(
            "resultado_status_usuario",
            "Usuário inválido.",
        )

        return

    usuario = db.buscar_usuario_por_id(usuario_id)

    if not usuario:
        emitir_erro_socket(
            "resultado_status_usuario",
            "Usuário não encontrado.",
        )

        return

    if usuario["tipo_usuario"] != "LOJISTA":
        emitir_erro_socket(
            "resultado_status_usuario",
            ("Somente contas de lojistas " "podem ser alteradas."),
        )

        return

    novo_status = (dados.get("status") or "").strip().upper()

    if novo_status not in {
        "ATIVA",
        "INATIVA",
    }:
        emitir_erro_socket(
            "resultado_status_usuario",
            "Status inválido.",
        )

        return

    db.atualizar_status_usuario(
        usuario_id,
        novo_status,
    )

    if novo_status == "INATIVA":
        encerrar_sessoes_usuario(usuario_id)

        mensagem = "Conta desativada com sucesso."

    else:
        mensagem = "Conta ativada com sucesso."

    emit(
        "resultado_status_usuario",
        {
            "sucesso": True,
            "mensagem": mensagem,
        },
    )

    emit(
        "lista_usuarios_admin",
        [usuario_publico(usuario) for usuario in db.listar_lojistas()],
    )

    emit(
        "resumo_admin",
        gerar_resumo_admin(),
    )


# =========================================================
# SOCKET.IO - LISTA DE RISCO
# =========================================================


@socketio.on("listar_lista_risco")
def listar_lista_risco_socket():
    admin = buscar_usuario_logado()

    if not admin:
        emitir_erro_socket(
            "resultado_lista_risco",
            "Usuário não autenticado.",
        )

        return

    if admin["tipo_usuario"] != "ADMIN":
        emitir_erro_socket(
            "resultado_lista_risco",
            "Operação não permitida.",
        )

        return

    emit(
        "lista_risco_atualizada",
        [item_risco_publico(item) for item in db.listar_riscos()],
    )


@socketio.on("adicionar_lista_risco")
def adicionar_lista_risco_socket(dados):
    admin = buscar_usuario_logado()

    if not admin:
        emitir_erro_socket(
            "resultado_lista_risco",
            "Usuário não autenticado.",
        )

        return

    if admin["tipo_usuario"] != "ADMIN":
        emitir_erro_socket(
            "resultado_lista_risco",
            "Operação não permitida.",
        )

        return

    limites = {
        "nome": MAX_NOME_COMPRADOR,
        "tipo_pessoa": 2,
        "documento": MAX_DOCUMENTO_COMPRADOR,
        "motivo": 500,
    }

    (
        valido,
        campo,
    ) = validar_campos_texto_payload(
        dados,
        limites,
    )

    if not valido:
        emitir_erro_socket(
            "resultado_lista_risco",
            ("Dados da lista de risco " "inválidos ou muito longos."),
            (f"risco_{campo}" if campo else None),
        )

        return

    nome = (dados.get("nome") or "").strip()

    tipo_pessoa = (dados.get("tipo_pessoa") or "").strip().upper()

    documento = (
        (dados.get("documento") or "")
        .strip()
        .replace(".", "")
        .replace("-", "")
        .replace("/", "")
    )

    motivo = (dados.get("motivo") or "").strip()

    if not nome:
        emitir_erro_socket(
            "resultado_lista_risco",
            "Informe o nome.",
            "risco_nome",
        )

        return

    valido, documento = validar_documento(
        documento,
        tipo_pessoa,
    )

    if not valido:
        emitir_erro_socket(
            "resultado_lista_risco",
            documento,
            "risco_documento",
        )

        return

    if db.documento_na_lista_risco(documento):
        emitir_erro_socket(
            "resultado_lista_risco",
            ("Este documento já está " "na lista de risco."),
            "risco_documento",
        )

        return

    if not motivo:
        emitir_erro_socket(
            "resultado_lista_risco",
            "Informe o motivo.",
            "risco_motivo",
        )

        return

    try:
        db.adicionar_risco(
            nome=nome,
            tipo_pessoa=tipo_pessoa,
            documento=documento,
            motivo=motivo,
            data_adicao=(datetime.now(FUSO_HORARIO).strftime("%d/%m/%Y %H:%M:%S")),
        )

    except sqlite3.IntegrityError:
        emitir_erro_socket(
            "resultado_lista_risco",
            ("Este documento já está " "na lista de risco."),
            "risco_documento",
        )

        return

    emit(
        "resultado_lista_risco",
        {
            "sucesso": True,
            "mensagem": ("Documento adicionado " "à lista de risco."),
        },
    )

    emit(
        "lista_risco_atualizada",
        [item_risco_publico(item) for item in db.listar_riscos()],
    )


@socketio.on("remover_lista_risco")
def remover_lista_risco_socket(dados):
    admin = buscar_usuario_logado()

    if not admin:
        emitir_erro_socket(
            "resultado_lista_risco",
            "Usuário não autenticado.",
        )

        return

    if admin["tipo_usuario"] != "ADMIN":
        emitir_erro_socket(
            "resultado_lista_risco",
            "Operação não permitida.",
        )

        return

    risco_id = extrair_id_positivo_payload(
        dados,
        "risco_id",
    )

    if risco_id is None:
        emitir_erro_socket(
            "resultado_lista_risco",
            ("Item da lista de risco " "inválido."),
        )

        return

    if not db.buscar_item_risco_por_id(risco_id):
        emitir_erro_socket(
            "resultado_lista_risco",
            "Item não encontrado.",
        )

        return

    db.remover_risco(risco_id)

    emit(
        "resultado_lista_risco",
        {
            "sucesso": True,
            "mensagem": ("Documento removido " "da lista de risco."),
        },
    )

    emit(
        "lista_risco_atualizada",
        [item_risco_publico(item) for item in db.listar_riscos()],
    )


# =========================================================
# LOGOUT E DESCONEXÃO
# =========================================================


@socketio.on("logout")
def logout_socket():
    usuarios_conectados.pop(
        request.sid,
        None,
    )

    emit(
        "resultado_logout",
        {"sucesso": True},
    )


@socketio.on("disconnect")
def desconectado():
    usuarios_conectados.pop(
        request.sid,
        None,
    )


# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == "__main__":
    porta = int(
        os.environ.get(
            "PORT",
            "5000",
        )
    )

    socketio.run(
        app,
        host="0.0.0.0",
        port=porta,
    )
