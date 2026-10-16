import os
import secrets

from flask import Flask
from flask_socketio import SocketIO

import model
from controller import registrar_controller

# =========================================================
# APLICAÇÃO
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)

app.json.ensure_ascii = False


# =========================================================
# SOCKET.IO
# =========================================================

socketio = SocketIO(app, cors_allowed_origins="*")


# =========================================================
# BANCO DE DADOS
# =========================================================

model.inicializar_banco(os.environ.get("ADMIN_INITIAL_PASSWORD"))


# =========================================================
# CONTROLLER
# =========================================================

registrar_controller(app, socketio)


# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
