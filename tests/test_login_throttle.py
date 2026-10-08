from login_throttle import LimitadorTentativasLogin


class RelogioFalso:
    def __init__(self):
        self.tempo = 0.0

    def __call__(self):
        return self.tempo

    def avancar(self, segundos):
        self.tempo += segundos


def criar_limitador(
    relogio,
    max_falhas=3,
    janela=60,
    cooldown=30,
):
    return LimitadorTentativasLogin(
        max_falhas=max_falhas,
        janela_segundos=janela,
        cooldown_segundos=cooldown,
        relogio=relogio,
    )


def registrar_falha(
    limitador,
    ip="127.0.0.1",
    email="usuario@teste.com",
):
    chave, retry_after = limitador.iniciar(
        ip,
        email,
    )

    assert chave is not None
    assert retry_after == 0

    limitador.finalizar(
        chave,
        falhou=True,
    )


def test_primeira_tentativa_e_permitida():
    relogio = RelogioFalso()

    limitador = criar_limitador(relogio)

    chave, retry_after = limitador.iniciar(
        "127.0.0.1",
        "usuario@teste.com",
    )

    assert chave is not None
    assert retry_after == 0

    limitador.finalizar(
        chave,
        falhou=False,
    )


def test_bloqueia_apos_numero_maximo_de_falhas():
    relogio = RelogioFalso()

    limitador = criar_limitador(
        relogio,
        max_falhas=3,
        cooldown=30,
    )

    for _ in range(3):
        registrar_falha(limitador)

    chave, retry_after = limitador.iniciar(
        "127.0.0.1",
        "usuario@teste.com",
    )

    assert chave is None
    assert retry_after > 0
    assert retry_after <= 30


def test_bloqueio_nao_afeta_outro_usuario():
    relogio = RelogioFalso()

    limitador = criar_limitador(
        relogio,
        max_falhas=3,
    )

    for _ in range(3):
        registrar_falha(
            limitador,
            ip="127.0.0.1",
            email="bloqueado@teste.com",
        )

    chave_bloqueado, retry_after = limitador.iniciar(
        "127.0.0.1",
        "bloqueado@teste.com",
    )

    assert chave_bloqueado is None
    assert retry_after > 0

    chave_outro, retry_outro = limitador.iniciar(
        "127.0.0.1",
        "outro@teste.com",
    )

    assert chave_outro is not None
    assert retry_outro == 0

    limitador.finalizar(
        chave_outro,
        falhou=False,
    )


def test_bloqueio_nao_afeta_outro_ip():
    relogio = RelogioFalso()

    limitador = criar_limitador(
        relogio,
        max_falhas=3,
    )

    for _ in range(3):
        registrar_falha(
            limitador,
            ip="192.168.0.10",
            email="usuario@teste.com",
        )

    chave, retry_after = limitador.iniciar(
        "192.168.0.20",
        "usuario@teste.com",
    )

    assert chave is not None
    assert retry_after == 0

    limitador.finalizar(
        chave,
        falhou=False,
    )


def test_usuario_pode_tentar_novamente_apos_periodo():
    relogio = RelogioFalso()

    limitador = criar_limitador(
        relogio,
        max_falhas=3,
        janela=60,
        cooldown=30,
    )

    for _ in range(3):
        registrar_falha(limitador)

    chave, retry_after = limitador.iniciar(
        "127.0.0.1",
        "usuario@teste.com",
    )

    assert chave is None
    assert retry_after > 0

    relogio.avancar(61)

    chave, retry_after = limitador.iniciar(
        "127.0.0.1",
        "usuario@teste.com",
    )

    assert chave is not None
    assert retry_after == 0

    limitador.finalizar(
        chave,
        falhou=False,
    )


def test_tentativa_sem_falha_nao_gera_bloqueio():
    relogio = RelogioFalso()

    limitador = criar_limitador(
        relogio,
        max_falhas=3,
    )

    for _ in range(10):
        chave, retry_after = limitador.iniciar(
            "127.0.0.1",
            "usuario@teste.com",
        )

        assert chave is not None
        assert retry_after == 0

        limitador.finalizar(
            chave,
            falhou=False,
        )
