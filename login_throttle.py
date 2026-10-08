import hashlib
import math
import time
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class _TentativasLogin:
    falhas: deque = field(default_factory=deque)
    em_andamento: int = 0
    bloqueado_ate: float = 0.0


class LimitadorTentativasLogin:
    def __init__(
        self,
        max_falhas=5,
        janela_segundos=600,
        cooldown_segundos=60,
        max_chaves=10000,
        relogio=None,
    ):
        if max_falhas < 1 or janela_segundos < 1 or cooldown_segundos < 1:
            raise ValueError("Os limites de tentativas devem ser positivos.")

        if max_chaves < 1:
            raise ValueError("max_chaves deve ser positivo.")

        self.max_falhas = max_falhas
        self.janela_segundos = janela_segundos
        self.cooldown_segundos = cooldown_segundos
        self.max_chaves = max_chaves

        self._relogio = relogio if relogio is not None else time.monotonic

        self._tentativas = OrderedDict()
        self._trava = Lock()

    @staticmethod
    def _gerar_chave(endereco_ip, identificador):
        endereco_ip = endereco_ip or "unknown"

        identificador = identificador.strip().lower()

        material = f"{endereco_ip}\0" f"{identificador}"

        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def _remover_falhas_antigas(self, tentativas, agora):
        limite = agora - self.janela_segundos

        while tentativas.falhas and tentativas.falhas[0] <= limite:
            tentativas.falhas.popleft()

    def _liberar_espaco(self):
        if len(self._tentativas) < self.max_chaves:
            return True

        for chave, tentativas in list(self._tentativas.items()):
            if tentativas.em_andamento == 0:
                del self._tentativas[chave]
                return True

        return False

    def iniciar(self, endereco_ip, identificador):
        chave = self._gerar_chave(endereco_ip, identificador)

        agora = self._relogio()

        with self._trava:
            tentativas = self._tentativas.get(chave)

            if tentativas is None:
                if not self._liberar_espaco():
                    return (None, self.cooldown_segundos)

                tentativas = _TentativasLogin()

                self._tentativas[chave] = tentativas

            else:
                self._tentativas.move_to_end(chave)

            self._remover_falhas_antigas(tentativas, agora)

            if tentativas.bloqueado_ate > agora:
                restante = math.ceil(tentativas.bloqueado_ate - agora)

                return None, restante

            if tentativas.bloqueado_ate:
                tentativas.bloqueado_ate = 0.0

            total_tentativas = len(tentativas.falhas) + tentativas.em_andamento

            if total_tentativas >= self.max_falhas:
                if len(tentativas.falhas) >= self.max_falhas:
                    restante = math.ceil(
                        self.janela_segundos - (agora - tentativas.falhas[0])
                    )

                    return (None, max(1, restante))

                return None, 1

            tentativas.em_andamento += 1

            return chave, 0

    def finalizar(self, chave, falhou=None):
        if chave is None:
            return

        agora = self._relogio()

        with self._trava:
            tentativas = self._tentativas.get(chave)

            if tentativas is None:
                return

            if tentativas.em_andamento > 0:
                tentativas.em_andamento -= 1

            if falhou is True:
                self._registrar_falha(tentativas, agora)

            elif falhou is False:
                tentativas.falhas.clear()
                tentativas.bloqueado_ate = 0.0

            self._tentativas.move_to_end(chave)

    def _registrar_falha(self, tentativas, agora):
        self._remover_falhas_antigas(tentativas, agora)

        tentativas.falhas.append(agora)

        if len(tentativas.falhas) >= self.max_falhas:
            tentativas.bloqueado_ate = agora + self.cooldown_segundos
