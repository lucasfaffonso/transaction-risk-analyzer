from login_throttle import LimitadorTentativasLogin


class RelogioFake:
    def __init__(self):
        self.tempo = 1000.0

    def agora(self):
        return self.tempo

    def avancar(self, segundos):
        self.tempo += segundos


def criar_limitador(relogio):
    return LimitadorTentativasLogin(
        max_falhas=3,
        janela_segundos=60,
        cooldown_segundos=30,
        max_chaves=100,
        relogio=relogio.agora,
    )


def registrar_falha(limitador, ip, email):
    chave, retry_after = limitador.iniciar(ip, email)

    assert retry_after == 0
    assert chave is not None

    limitador.finalizar(chave, falhou=True)


def test_primeira_tentativa_e_permitida():
    relogio = RelogioFake()

    limitador = criar_limitador(relogio)

    chave, retry_after = limitador.iniciar(
        "127.0.0.1",
        "teste@teste.com",
    )

    assert chave is not None
    assert retry_after == 0


def test_bloqueia_apos_numero_maximo_de_falhas():
    relogio = RelogioFake()

    limitador = criar_limitador(relogio)

    for _ in range(3):
        registrar_falha(
            limitador,
            "127.0.0.1",
            "teste@teste.com",
        )

    chave, retry_after = limitador.iniciar(
        "127.0.0.1",
        "teste@teste.com",
    )

    assert chave is None
    assert retry_after > 0


def test_bloqueio_nao_afeta_outro_usuario():
    relogio = RelogioFake()

    limitador = criar_limitador(relogio)

    for _ in range(3):
        registrar_falha(
            limitador,
            "127.0.0.1",
            "usuario1@teste.com",
        )

    chave, retry_after = limitador.iniciar(
        "127.0.0.1",
        "usuario2@teste.com",
    )

    assert chave is not None
    assert retry_after == 0


def test_bloqueio_nao_afeta_outro_ip():
    relogio = RelogioFake()

    limitador = criar_limitador(relogio)

    for _ in range(3):
        registrar_falha(
            limitador,
            "10.0.0.1",
            "teste@teste.com",
        )

    chave, retry_after = limitador.iniciar(
        "10.0.0.2",
        "teste@teste.com",
    )

    assert chave is not None
    assert retry_after == 0


def test_usuario_pode_tentar_novamente_apos_periodo():
    relogio = RelogioFake()

    limitador = criar_limitador(relogio)

    for _ in range(3):
        registrar_falha(
            limitador,
            "127.0.0.1",
            "teste@teste.com",
        )

    chave, retry_after = limitador.iniciar(
        "127.0.0.1",
        "teste@teste.com",
    )

    assert chave is None
    assert retry_after > 0

    # A janela das tentativas é de 60 segundos.
    # Após esse período, as falhas antigas deixam
    # de ser consideradas.
    relogio.avancar(61)

    chave, retry_after = limitador.iniciar(
        "127.0.0.1",
        "teste@teste.com",
    )

    assert chave is not None
    assert retry_after == 0


def test_tentativa_sem_falha_nao_gera_bloqueio():
    relogio = RelogioFake()

    limitador = criar_limitador(relogio)

    for _ in range(2):
        registrar_falha(
            limitador,
            "127.0.0.1",
            "teste@teste.com",
        )

    chave, retry_after = limitador.iniciar(
        "127.0.0.1",
        "teste@teste.com",
    )

    assert retry_after == 0

    limitador.finalizar(chave, falhou=False)

    chave, retry_after = limitador.iniciar(
        "127.0.0.1",
        "teste@teste.com",
    )

    assert chave is not None
    assert retry_after == 0
