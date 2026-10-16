import { socket } from "./socket.js";
import { state } from "./state.js";

import {
  $,
  atualizarCampoDocumento,
  aplicarClasseRisco,
  criarBadgeOrigem,
  criarBotao,
  criarCelula,
  formatarDocumento,
  formatarMoeda,
  formatarTelefone,
  limparErro,
  limparMensagem,
  mostrarMensagem,
  normalizarTexto
} from "./utils.js";

import {
  validarDocumento,
  validarEmail,
  validarObrigatorio,
  validarPedidoId,
  validarValorTransacao
} from "./validators.js";

import {
  abrirDetalhesTransacao
} from "./modal.js";


// =========================================================
// ELEMENTOS DO PAINEL
// =========================================================

const painelLojista = $("painel_lojista");

const menuLojista = document.querySelectorAll(
  "[data-secao-lojista]"
);

const secoesLojista = document.querySelectorAll(
  ".secao-painel"
);


// =========================================================
// RESUMO
// =========================================================

const lojistaStatus = $("lojista_status");
const lojistaTotalTransacoes = $("lojista_total_transacoes");
const lojistaEmAnalise = $("lojista_em_analise");
const lojistaBloqueadas = $("lojista_bloqueadas");


// =========================================================
// CONTA
// =========================================================

const contaId = $("conta_id");
const contaNome = $("conta_nome");
const contaDocumento = $("conta_documento");
const contaEmail = $("conta_email");
const contaTelefone = $("conta_telefone");
const contaData = $("conta_data");


// =========================================================
// ANÁLISE DE TRANSAÇÃO
// =========================================================

const formTransacao = $("form_transacao");

const pedidoId = $("pedido_id");
const botaoVerificarPedido = $("botao_verificar_pedido");

const mensagemVerificacaoPedido = $(
  "mensagem_verificacao_pedido"
);

const dadosTransacao = $("dados_transacao");

const compradorNome = $("comprador_nome");
const compradorTipoPessoa = $("comprador_tipo_pessoa");
const compradorDocumento = $("comprador_documento");
const compradorEmail = $("comprador_email");

const transacaoValor = $("transacao_valor");
const formaPagamento = $("forma_pagamento");

const labelCompradorDocumento = $(
  "label_comprador_documento"
);

const mensagemAnalise = $("mensagem_analise");

const resultadoAnalise = $("resultado_analise");
const resultadoPontuacao = $("resultado_pontuacao");
const resultadoRisco = $("resultado_risco");
const resultadoStatus = $("resultado_status");
const resultadoMotivos = $("resultado_motivos");


// =========================================================
// HISTÓRICO
// =========================================================

const listaTransacoes = $("lista_transacoes");
const nenhumaTransacao = $("nenhuma_transacao");

const filtroLojistaBusca = $("filtro_lojista_busca");
const filtroLojistaRisco = $("filtro_lojista_risco");
const filtroLojistaStatus = $("filtro_lojista_status");
const filtroLojistaOrigem = $("filtro_lojista_origem");


// =========================================================
// ESTATÍSTICAS
// =========================================================

const lojistaEstTotal = $("lojista_est_total");
const lojistaEstAprovadas = $("lojista_est_aprovadas");
const lojistaEstAlerta = $("lojista_est_alerta");
const lojistaEstAnalise = $("lojista_est_analise");
const lojistaEstBloqueadas = $("lojista_est_bloqueadas");

const lojistaRiscoBaixo = $("lojista_risco_baixo");
const lojistaRiscoMedio = $("lojista_risco_medio");
const lojistaRiscoAlto = $("lojista_risco_alto");
const lojistaRiscoCritico = $("lojista_risco_critico");

const lojistaValorTotal = $("lojista_valor_total");
const lojistaTicketMedio = $("lojista_ticket_medio");
const lojistaScoreMedio = $("lojista_score_medio");


// =========================================================
// NAVEGAÇÃO
// =========================================================

function mostrarSecaoLojista(idSecao) {
  secoesLojista.forEach(
    (secao) => {
      secao.classList.add("oculto");
    }
  );

  menuLojista.forEach(
    (botao) => {
      botao.classList.remove("ativo");
    }
  );

  const secao = $(idSecao);

  if (secao) {
    secao.classList.remove("oculto");
  }

  const botao = document.querySelector(
    `[data-secao-lojista="${idSecao}"]`
  );

  if (botao) {
    botao.classList.add("ativo");
  }
}


// =========================================================
// CONTA DO LOJISTA
// =========================================================

function preencherDadosConta(usuario) {
  contaId.textContent =
    usuario.usuario_id ?? "-";

  contaNome.textContent =
    usuario.nome ?? "-";

  contaDocumento.textContent =
    formatarDocumento(
      usuario.documento
    );

  contaEmail.textContent =
    usuario.email ?? "-";

  contaTelefone.textContent =
    formatarTelefone(
      usuario.telefone
    );

  contaData.textContent =
    usuario.data_criacao ?? "-";

  lojistaStatus.textContent =
    usuario.status ?? "-";
}


// =========================================================
// ID da transação
// =========================================================

function habilitarBotaoVerificacao() {
  botaoVerificarPedido.disabled = false;

  botaoVerificarPedido.textContent =
    "Verificar transação";
}


function desabilitarBotaoVerificacao() {
  botaoVerificarPedido.disabled = true;

  botaoVerificarPedido.textContent =
    "Verificando...";
}


function limparDadosTransacao() {
  compradorNome.value = "";
  compradorTipoPessoa.value = "PF";
  compradorDocumento.value = "";
  compradorEmail.value = "";
  transacaoValor.value = "";
  formaPagamento.value = "CARTAO";

  [
    compradorNome,
    compradorDocumento,
    compradorEmail,
    transacaoValor
  ].forEach(limparErro);

  atualizarCampoDocumento(
    "PF",
    labelCompradorDocumento,
    compradorDocumento
  );
}


function invalidarPedidoVerificado() {
  state.pedidoVerificadoId = null;

  dadosTransacao.classList.add(
    "oculto"
  );

  resultadoAnalise.classList.add(
    "oculto"
  );

  limparMensagem(
    mensagemVerificacaoPedido
  );

  limparMensagem(
    mensagemAnalise
  );
}


export function reiniciarAnalisePedido() {
  formTransacao.reset();

  state.pedidoVerificadoId = null;

  limparErro(pedidoId);

  limparDadosTransacao();

  limparMensagem(
    mensagemVerificacaoPedido
  );

  limparMensagem(
    mensagemAnalise
  );

  dadosTransacao.classList.add(
    "oculto"
  );

  resultadoAnalise.classList.add(
    "oculto"
  );

  habilitarBotaoVerificacao();
}


function verificarPedido() {
  limparMensagem(
    mensagemVerificacaoPedido
  );

  limparMensagem(
    mensagemAnalise
  );

  resultadoAnalise.classList.add(
    "oculto"
  );

  dadosTransacao.classList.add(
    "oculto"
  );

  state.pedidoVerificadoId = null;

  if (!validarPedidoId(pedidoId)) {
    return;
  }

  desabilitarBotaoVerificacao();

  socket.emit(
    "verificar_pedido_id",
    {
      pedido_id:
        pedidoId.value.trim()
    }
  );
}


// =========================================================
// RESULTADO DA ANÁLISE
// =========================================================

function mostrarResultadoAnalise(
  transacao
) {
  resultadoAnalise.classList.remove(
    "oculto"
  );

  resultadoPontuacao.textContent =
    transacao.pontuacao_risco ?? 0;

  resultadoRisco.textContent =
    transacao.nivel_risco ?? "-";

  resultadoStatus.textContent =
    transacao.status ?? "-";


  resultadoRisco.className =
    "risco-texto";

  aplicarClasseRisco(
    resultadoRisco,
    transacao.nivel_risco
  );


  resultadoMotivos.innerHTML = "";

  const motivos =
    transacao.motivos_risco || [];


  if (!motivos.length) {
    const item =
      document.createElement("li");

    item.textContent =
      "Nenhum fator de risco identificado.";

    resultadoMotivos.appendChild(
      item
    );

    return;
  }


  motivos.forEach(
    (motivo) => {
      const item =
        document.createElement("li");

      item.textContent =
        `+${motivo.pontos} - ${motivo.motivo}`;

      resultadoMotivos.appendChild(
        item
      );
    }
  );
}


// =========================================================
// FILTROS
// =========================================================

function filtrarTransacoes() {
  const busca =
    normalizarTexto(
      filtroLojistaBusca.value
    );

  const risco =
    filtroLojistaRisco.value;

  const status =
    filtroLojistaStatus.value;

  const origem =
    filtroLojistaOrigem.value;


  return state.transacoesLojista.filter(
    (transacao) => {
      const camposBusca = [
        transacao.transacao_id,
        transacao.pedido_id || "",
        transacao.comprador_nome,
        transacao.comprador_documento,
        transacao.comprador_email
      ];

      const correspondeBusca =
        !busca ||
        normalizarTexto(
          camposBusca.join(" ")
        ).includes(busca);

      const correspondeRisco =
        !risco ||
        transacao.nivel_risco === risco;

      const correspondeStatus =
        !status ||
        transacao.status === status;

      const correspondeOrigem =
        !origem ||
        (
          transacao.origem || "WEB"
        ) === origem;

      return (
        correspondeBusca &&
        correspondeRisco &&
        correspondeStatus &&
        correspondeOrigem
      );
    }
  );
}


function aplicarFiltrosLojista() {
  renderizarTransacoes(
    filtrarTransacoes()
  );
}


export function limparFiltrosLojista() {
  filtroLojistaBusca.value = "";
  filtroLojistaRisco.value = "";
  filtroLojistaStatus.value = "";
  filtroLojistaOrigem.value = "";
}


// =========================================================
// TABELA DE TRANSAÇÕES
// =========================================================

function renderizarTransacoes(
  transacoes
) {
  listaTransacoes.innerHTML = "";

  nenhumaTransacao.style.display =
    transacoes.length
      ? "none"
      : "block";


  transacoes.forEach(
    (transacao) => {
      const linha =
        document.createElement("tr");


      const risco =
        criarCelula(
          transacao.nivel_risco
        );

      aplicarClasseRisco(
        risco,
        transacao.nivel_risco
      );


      const origem =
        document.createElement("td");

      origem.appendChild(
        criarBadgeOrigem(
          transacao.origem || "WEB"
        )
      );


      const acao =
        document.createElement("td");

      acao.appendChild(
        criarBotao(
          "Detalhes",
          "botao-detalhes",
          () => {
            abrirDetalhesTransacao(
              transacao,
              false
            );
          }
        )
      );


      linha.append(
        criarCelula(
          transacao.transacao_id
        ),

        criarCelula(
          transacao.pedido_id || "-"
        ),

        criarCelula(
          transacao.data_hora
        ),

        criarCelula(
          transacao.comprador_nome
        ),

        criarCelula(
          formatarDocumento(
            transacao.comprador_documento
          )
        ),

        criarCelula(
          formatarMoeda(
            transacao.valor
          )
        ),

        criarCelula(
          transacao.forma_pagamento
        ),

        risco,

        criarCelula(
          transacao.status
        ),

        origem,

        acao
      );


      listaTransacoes.appendChild(
        linha
      );
    }
  );
}


// =========================================================
// ESTATÍSTICAS
// =========================================================

function preencherEstatisticasLojista(
  dados
) {
  lojistaEstTotal.textContent =
    dados.total ?? 0;

  lojistaEstAprovadas.textContent =
    dados.aprovadas ?? 0;

  lojistaEstAlerta.textContent =
    dados.aprovadas_alerta ?? 0;

  lojistaEstAnalise.textContent =
    dados.em_analise ?? 0;

  lojistaEstBloqueadas.textContent =
    dados.bloqueadas ?? 0;


  lojistaRiscoBaixo.textContent =
    dados.risco_baixo ?? 0;

  lojistaRiscoMedio.textContent =
    dados.risco_medio ?? 0;

  lojistaRiscoAlto.textContent =
    dados.risco_alto ?? 0;

  lojistaRiscoCritico.textContent =
    dados.risco_critico ?? 0;


  lojistaValorTotal.textContent =
    formatarMoeda(
      dados.valor_total
    );

  lojistaTicketMedio.textContent =
    formatarMoeda(
      dados.ticket_medio
    );

  lojistaScoreMedio.textContent =
    dados.score_medio ?? 0;
}


// =========================================================
// ENVIO DA TRANSAÇÃO
// =========================================================

function enviarTransacao(event) {
  event.preventDefault();

  limparMensagem(
    mensagemAnalise
  );


  const pedidoAtual =
    pedidoId.value.trim();


  if (!validarPedidoId(pedidoId)) {
    return;
  }


  if (
    state.pedidoVerificadoId !==
    pedidoAtual
  ) {
    dadosTransacao.classList.add(
      "oculto"
    );

    mostrarMensagem(
      mensagemVerificacaoPedido,
      "Verifique o ID da transação antes de continuar.",
      false
    );

    return;
  }


  if (
    dadosTransacao.classList.contains(
      "oculto"
    )
  ) {
    return;
  }


  const validacoes = [
    validarObrigatorio(
      compradorNome,
      "Informe o nome do comprador."
    ),

    validarDocumento(
      compradorDocumento,
      compradorTipoPessoa.value
    ),

    validarEmail(
      compradorEmail
    ),

    validarValorTransacao(
      transacaoValor
    )
  ];


  if (validacoes.includes(false)) {
    return;
  }


  socket.emit(
    "analisar_transacao",
    {
      pedido_id:
        pedidoAtual,

      comprador_nome:
        compradorNome.value.trim(),

      comprador_tipo_pessoa:
        compradorTipoPessoa.value,

      comprador_documento:
        compradorDocumento.value,

      comprador_email:
        compradorEmail.value.trim(),

      valor:
        Number(
          transacaoValor.value
        ),

      forma_pagamento:
        formaPagamento.value
    }
  );
}


// =========================================================
// EVENTOS DO FORMULÁRIO
// =========================================================

function registrarEventosFormulario() {
  pedidoId.addEventListener(
    "input",
    () => {
      limparErro(pedidoId);

      invalidarPedidoVerificado();
    }
  );


  pedidoId.addEventListener(
    "keydown",
    (event) => {
      if (event.key === "Enter") {
        event.preventDefault();

        verificarPedido();
      }
    }
  );


  botaoVerificarPedido.addEventListener(
    "click",
    verificarPedido
  );


  compradorNome.addEventListener(
    "blur",
    () => validarObrigatorio(
      compradorNome,
      "Informe o nome do comprador."
    )
  );


  compradorDocumento.addEventListener(
    "blur",
    () => validarDocumento(
      compradorDocumento,
      compradorTipoPessoa.value
    )
  );


  compradorEmail.addEventListener(
    "blur",
    () => validarEmail(
      compradorEmail
    )
  );


  transacaoValor.addEventListener(
    "blur",
    () => validarValorTransacao(
      transacaoValor
    )
  );


  [
    compradorNome,
    compradorDocumento,
    compradorEmail,
    transacaoValor
  ].forEach(
    (campo) => {
      campo.addEventListener(
        "input",
        () => limparErro(campo)
      );
    }
  );


  compradorTipoPessoa.addEventListener(
    "change",
    () => {
      compradorDocumento.value = "";

      atualizarCampoDocumento(
        compradorTipoPessoa.value,
        labelCompradorDocumento,
        compradorDocumento
      );
    }
  );


  formTransacao.addEventListener(
    "submit",
    enviarTransacao
  );
}


// =========================================================
// EVENTOS DOS FILTROS
// =========================================================

function registrarEventosFiltros() {
  filtroLojistaBusca.addEventListener(
    "input",
    aplicarFiltrosLojista
  );


  [
    filtroLojistaRisco,
    filtroLojistaStatus,
    filtroLojistaOrigem
  ].forEach(
    (campo) => {
      campo.addEventListener(
        "change",
        aplicarFiltrosLojista
      );
    }
  );
}


// =========================================================
// EVENTOS DO MENU
// =========================================================

function registrarEventosMenu() {
  menuLojista.forEach(
    (botao) => {
      botao.addEventListener(
        "click",
        () => {
          const secao =
            botao.dataset.secaoLojista;


          mostrarSecaoLojista(
            secao
          );


          if (
            secao ===
            "lojista_analisar"
          ) {
            reiniciarAnalisePedido();

            pedidoId.focus();
          }


          if (
            secao ===
              "lojista_inicio" ||
            secao ===
              "lojista_transacoes"
          ) {
            socket.emit(
              "listar_minhas_transacoes"
            );
          }


          if (
            secao ===
            "lojista_estatisticas"
          ) {
            socket.emit(
              "obter_estatisticas_lojista"
            );
          }
        }
      );
    }
  );
}


// =========================================================
// EVENTOS DO SOCKET
// =========================================================

function registrarEventosSocket() {
  socket.on(
    "resultado_verificacao_pedido",
    (resultado) => {
      habilitarBotaoVerificacao();


      if (
        !resultado ||
        !resultado.sucesso
      ) {
        state.pedidoVerificadoId =
          null;

        dadosTransacao.classList.add(
          "oculto"
        );

        resultadoAnalise.classList.add(
          "oculto"
        );

        mostrarMensagem(
          mensagemVerificacaoPedido,
          resultado?.mensagem ||
            "Não foi possível verificar o pedido.",
          false
        );

        return;
      }


      const pedidoAtual =
        pedidoId.value.trim();


      if (
        pedidoAtual !==
        resultado.pedido_id
      ) {
        return;
      }


      state.pedidoVerificadoId =
        resultado.pedido_id;

      limparMensagem(
        mensagemAnalise
      );


      if (resultado.existe) {
        dadosTransacao.classList.add(
          "oculto"
        );

        mostrarMensagem(
          mensagemVerificacaoPedido,
          resultado.mensagem,
          true
        );

        mostrarResultadoAnalise(
          resultado.transacao
        );

        return;
      }


      resultadoAnalise.classList.add(
        "oculto"
      );

      limparDadosTransacao();

      dadosTransacao.classList.remove(
        "oculto"
      );

      mostrarMensagem(
        mensagemVerificacaoPedido,
        resultado.mensagem,
        true
      );

      compradorNome.focus();
    }
  );


  socket.on(
    "resultado_analise",
    (resultado) => {
      if (
        !resultado ||
        !resultado.sucesso
      ) {
        const campo =
          resultado?.campo
            ? $(resultado.campo)
            : null;

        if (campo) {
          import("./utils.js").then(
            ({ mostrarErro }) => {
              mostrarErro(
                campo,
                resultado.mensagem
              );
            }
          );
        } else {
          mostrarMensagem(
            mensagemAnalise,
            resultado?.mensagem ||
              "Não foi possível analisar a transação.",
            false
          );
        }

        return;
      }


      state.pedidoVerificadoId =
        resultado.transacao.pedido_id;


      dadosTransacao.classList.add(
        "oculto"
      );

      limparDadosTransacao();


      if (resultado.duplicada) {
        mostrarMensagem(
          mensagemVerificacaoPedido,
          "Esta transação já foi analisada. O resultado anterior foi reutilizado.",
          true
        );
      } else {
        mostrarMensagem(
          mensagemVerificacaoPedido,
          "Pedido analisado com sucesso.",
          true
        );
      }


      mostrarResultadoAnalise(
        resultado.transacao
      );


      socket.emit(
        "listar_minhas_transacoes"
      );
    }
  );


  socket.on(
    "lista_minhas_transacoes",
    (transacoes) => {
      state.transacoesLojista =
        Array.isArray(transacoes)
          ? transacoes
          : [];

      aplicarFiltrosLojista();
    }
  );


  socket.on(
    "resumo_lojista",
    (resumo) => {
      if (!resumo) {
        return;
      }

      lojistaTotalTransacoes.textContent =
        resumo.total ?? 0;

      lojistaEmAnalise.textContent =
        resumo.em_analise ?? 0;

      lojistaBloqueadas.textContent =
        resumo.bloqueadas ?? 0;
    }
  );


  socket.on(
    "estatisticas_lojista",
    (dados) => {
      if (!dados) {
        return;
      }

      preencherEstatisticasLojista(
        dados
      );
    }
  );
}


// =========================================================
// ABRIR PAINEL
// =========================================================

export function abrirPainelLojista(
  usuario
) {
  state.usuarioAtual = usuario;

  painelLojista.classList.remove(
    "oculto"
  );

  preencherDadosConta(
    usuario
  );

  mostrarSecaoLojista(
    "lojista_inicio"
  );

  reiniciarAnalisePedido();

  socket.emit(
    "listar_minhas_transacoes"
  );
}


// =========================================================
// FECHAR / LIMPAR
// =========================================================

export function fecharPainelLojista() {
  painelLojista.classList.add(
    "oculto"
  );

  state.transacoesLojista = [];
  state.pedidoVerificadoId = null;

  limparFiltrosLojista();

  reiniciarAnalisePedido();

  listaTransacoes.innerHTML = "";
}


// =========================================================
// INICIALIZAÇÃO
// =========================================================

export function inicializarLojista() {
  registrarEventosMenu();
  registrarEventosFormulario();
  registrarEventosFiltros();
  registrarEventosSocket();

  atualizarCampoDocumento(
    compradorTipoPessoa.value,
    labelCompradorDocumento,
    compradorDocumento
  );
}