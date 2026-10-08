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
  mostrarErro,
  mostrarMensagem,
  normalizarTexto
} from "./utils.js";

import {
  validarDocumento,
  validarObrigatorio
} from "./validators.js";

import {
  abrirDetalhesTransacao
} from "./modal.js";


// =========================================================
// PAINEL
// =========================================================

const painelAdmin = $("painel_admin");

const menuAdmin = document.querySelectorAll(
  "[data-secao-admin]"
);

const secoesAdmin = document.querySelectorAll(
  ".secao-admin"
);


// =========================================================
// RESUMO
// =========================================================

const adminTotalLojistas = $("admin_total_lojistas");
const adminTotalTransacoes = $("admin_total_transacoes");
const adminEmAnalise = $("admin_em_analise");
const adminBloqueadas = $("admin_bloqueadas");


// =========================================================
// USUÁRIOS
// =========================================================

const adminListaUsuarios = $("admin_lista_usuarios");
const adminNenhumUsuario = $("admin_nenhum_usuario");
const mensagemStatusUsuario = $("mensagem_status_usuario");


// =========================================================
// TRANSAÇÕES
// =========================================================

const adminListaTransacoes = $("admin_lista_transacoes");
const adminNenhumaTransacao = $("admin_nenhuma_transacao");
const mensagemRevisao = $("mensagem_revisao");

const filtroAdminBusca = $("filtro_admin_busca");
const filtroAdminRisco = $("filtro_admin_risco");
const filtroAdminStatus = $("filtro_admin_status");
const filtroAdminOrigem = $("filtro_admin_origem");


// =========================================================
// LISTA DE RISCO
// =========================================================

const formListaRisco = $("form_lista_risco");

const riscoNome = $("risco_nome");
const riscoTipoPessoa = $("risco_tipo_pessoa");
const riscoDocumento = $("risco_documento");
const riscoMotivo = $("risco_motivo");

const labelRiscoDocumento = $("label_risco_documento");

const mensagemListaRisco = $("mensagem_lista_risco");

const listaRiscoTabela = $("lista_risco_tabela");
const listaRiscoVazia = $("lista_risco_vazia");


// =========================================================
// ESTATÍSTICAS
// =========================================================

const adminEstTotal = $("admin_est_total");
const adminEstAprovadas = $("admin_est_aprovadas");
const adminEstAlerta = $("admin_est_alerta");
const adminEstAnalise = $("admin_est_analise");
const adminEstBloqueadas = $("admin_est_bloqueadas");

const adminRiscoBaixo = $("admin_risco_baixo");
const adminRiscoMedio = $("admin_risco_medio");
const adminRiscoAlto = $("admin_risco_alto");
const adminRiscoCritico = $("admin_risco_critico");

const adminRevisoes = $("admin_revisoes");
const adminRevisoesAprovadas = $("admin_revisoes_aprovadas");
const adminRevisoesBloqueadas = $("admin_revisoes_bloqueadas");

const adminValorTotal = $("admin_valor_total");
const adminTicketMedio = $("admin_ticket_medio");
const adminScoreMedio = $("admin_score_medio");


// =========================================================
// NAVEGAÇÃO
// =========================================================

function mostrarSecaoAdmin(idSecao) {
  secoesAdmin.forEach(
    (secao) => {
      secao.classList.add("oculto");
    }
  );

  menuAdmin.forEach(
    (botao) => {
      botao.classList.remove("ativo");
    }
  );

  const secao = $(idSecao);

  if (secao) {
    secao.classList.remove("oculto");
  }

  const botao = document.querySelector(
    `[data-secao-admin="${idSecao}"]`
  );

  if (botao) {
    botao.classList.add("ativo");
  }
}


// =========================================================
// USUÁRIOS
// =========================================================

function renderizarUsuariosAdmin(usuarios) {
  adminListaUsuarios.innerHTML = "";

  adminNenhumUsuario.style.display =
    usuarios.length
      ? "none"
      : "block";


  usuarios.forEach(
    (usuario) => {
      const linha = document.createElement(
        "tr"
      );


      const status = document.createElement(
        "td"
      );

      const statusTexto =
        document.createElement(
          "span"
        );

      statusTexto.textContent =
        usuario.status;

      statusTexto.className =
        usuario.status === "ATIVA"
          ? "status-ativa"
          : "status-inativa";

      status.appendChild(
        statusTexto
      );


      const acao = document.createElement(
        "td"
      );

      const contaAtiva =
        usuario.status === "ATIVA";


      acao.appendChild(
        criarBotao(
          contaAtiva
            ? "Desativar"
            : "Ativar",

          contaAtiva
            ? "botao-desativar"
            : "botao-ativar",

          () => {
            limparMensagem(
              mensagemStatusUsuario
            );

            socket.emit(
              "alterar_status_usuario",
              {
                usuario_id:
                  usuario.usuario_id,

                status:
                  contaAtiva
                    ? "INATIVA"
                    : "ATIVA"
              }
            );
          }
        )
      );


      linha.append(
        criarCelula(
          usuario.usuario_id
        ),

        criarCelula(
          usuario.nome
        ),

        criarCelula(
          usuario.tipo_pessoa === "PF"
            ? "Pessoa Física"
            : "Pessoa Jurídica"
        ),

        criarCelula(
          formatarDocumento(
            usuario.documento
          )
        ),

        criarCelula(
          usuario.email
        ),

        criarCelula(
          formatarTelefone(
            usuario.telefone
          )
        ),

        criarCelula(
          usuario.data_criacao
        ),

        status,

        acao
      );


      adminListaUsuarios.appendChild(
        linha
      );
    }
  );
}


// =========================================================
// FILTROS DE TRANSAÇÕES
// =========================================================

function filtrarTransacoesAdmin() {
  const busca =
    normalizarTexto(
      filtroAdminBusca.value
    );

  const risco =
    filtroAdminRisco.value;

  const status =
    filtroAdminStatus.value;

  const origem =
    filtroAdminOrigem.value;


  return state.transacoesAdmin.filter(
    (transacao) => {
      const camposBusca = [
        transacao.transacao_id,
        transacao.pedido_id || "",
        transacao.lojista_nome,
        transacao.lojista_email,
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


function aplicarFiltrosAdmin() {
  renderizarTransacoesAdmin(
    filtrarTransacoesAdmin()
  );
}


export function limparFiltrosAdmin() {
  filtroAdminBusca.value = "";
  filtroAdminRisco.value = "";
  filtroAdminStatus.value = "";
  filtroAdminOrigem.value = "";
}


// =========================================================
// TRANSAÇÕES
// =========================================================

function renderizarTransacoesAdmin(
  transacoes
) {
  adminListaTransacoes.innerHTML = "";

  adminNenhumaTransacao.style.display =
    transacoes.length
      ? "none"
      : "block";


  transacoes.forEach(
    (transacao) => {
      const linha =
        document.createElement(
          "tr"
        );


      // Origem
      const origem =
        document.createElement(
          "td"
        );

      origem.appendChild(
        criarBadgeOrigem(
          transacao.origem || "WEB"
        )
      );


      // Risco
      const risco =
        criarCelula(
          transacao.nivel_risco
        );

      aplicarClasseRisco(
        risco,
        transacao.nivel_risco
      );


      // Ações
      const acao =
        document.createElement(
          "td"
        );

      const container =
        document.createElement(
          "div"
        );

      container.className =
        "acoes-transacao";


      container.appendChild(
        criarBotao(
          "Detalhes",
          "botao-detalhes",
          () => {
            abrirDetalhesTransacao(
              transacao,
              true
            );
          }
        )
      );


      if (
        transacao.status_automatico ===
          "EM ANÁLISE" &&
        !transacao.revisada
      ) {
        container.append(
          criarBotao(
            "Aprovar",
            "botao-aprovar",
            () => {
              revisarTransacao(
                transacao.transacao_id,
                "APROVAR"
              );
            }
          ),

          criarBotao(
            "Bloquear",
            "botao-bloquear",
            () => {
              revisarTransacao(
                transacao.transacao_id,
                "BLOQUEAR"
              );
            }
          )
        );
      } else if (
        transacao.revisada
      ) {
        const texto =
          document.createElement(
            "span"
          );

        texto.className =
          "texto-revisado";

        texto.textContent =
          transacao.decisao_revisao
            ? `Revisada: ${transacao.decisao_revisao}`
            : "Revisada";

        container.appendChild(
          texto
        );
      }


      acao.appendChild(
        container
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
          transacao.lojista_nome
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

        origem,

        criarCelula(
          transacao.pontuacao_risco
        ),

        risco,

        criarCelula(
          transacao.status
        ),

        acao
      );


      adminListaTransacoes.appendChild(
        linha
      );
    }
  );
}


// =========================================================
// REVISÃO MANUAL
// =========================================================

function revisarTransacao(
  transacaoId,
  decisao
) {
  limparMensagem(
    mensagemRevisao
  );

  socket.emit(
    "revisar_transacao",
    {
      transacao_id:
        transacaoId,

      decisao:
        decisao
    }
  );
}


// =========================================================
// LISTA DE RISCO
// =========================================================

function limparFormularioRisco() {
  formListaRisco.reset();

  riscoTipoPessoa.value = "PF";

  [
    riscoNome,
    riscoDocumento,
    riscoMotivo
  ].forEach(limparErro);

  atualizarCampoDocumento(
    "PF",
    labelRiscoDocumento,
    riscoDocumento
  );
}


function renderizarListaRisco(lista) {
  listaRiscoTabela.innerHTML = "";

  listaRiscoVazia.style.display =
    lista.length
      ? "none"
      : "block";


  lista.forEach(
    (item) => {
      const linha =
        document.createElement(
          "tr"
        );

      const acao =
        document.createElement(
          "td"
        );


      acao.appendChild(
        criarBotao(
          "Remover",
          "botao-remover",
          () => {
            removerDaListaRisco(
              item.risco_id
            );
          }
        )
      );


      linha.append(
        criarCelula(
          item.risco_id
        ),

        criarCelula(
          item.nome
        ),

        criarCelula(
          formatarDocumento(
            item.documento
          )
        ),

        criarCelula(
          item.motivo
        ),

        criarCelula(
          item.data_adicao
        ),

        acao
      );


      listaRiscoTabela.appendChild(
        linha
      );
    }
  );
}


function enviarListaRisco(event) {
  event.preventDefault();

  limparMensagem(
    mensagemListaRisco
  );


  const validacoes = [
    validarObrigatorio(
      riscoNome,
      "Informe o nome."
    ),

    validarDocumento(
      riscoDocumento,
      riscoTipoPessoa.value
    ),

    validarObrigatorio(
      riscoMotivo,
      "Informe o motivo."
    )
  ];


  if (validacoes.includes(false)) {
    return;
  }


  socket.emit(
    "adicionar_lista_risco",
    {
      nome:
        riscoNome.value.trim(),

      tipo_pessoa:
        riscoTipoPessoa.value,

      documento:
        riscoDocumento.value,

      motivo:
        riscoMotivo.value.trim()
    }
  );
}


function removerDaListaRisco(riscoId) {
  limparMensagem(
    mensagemListaRisco
  );

  socket.emit(
    "remover_lista_risco",
    {
      risco_id:
        riscoId
    }
  );
}


// =========================================================
// ESTATÍSTICAS
// =========================================================

function preencherEstatisticasAdmin(
  dados
) {
  adminEstTotal.textContent =
    dados.total ?? 0;

  adminEstAprovadas.textContent =
    dados.aprovadas ?? 0;

  adminEstAlerta.textContent =
    dados.aprovadas_alerta ?? 0;

  adminEstAnalise.textContent =
    dados.em_analise ?? 0;

  adminEstBloqueadas.textContent =
    dados.bloqueadas ?? 0;


  adminRiscoBaixo.textContent =
    dados.risco_baixo ?? 0;

  adminRiscoMedio.textContent =
    dados.risco_medio ?? 0;

  adminRiscoAlto.textContent =
    dados.risco_alto ?? 0;

  adminRiscoCritico.textContent =
    dados.risco_critico ?? 0;


  adminRevisoes.textContent =
    dados.revisoes ?? 0;

  adminRevisoesAprovadas.textContent =
    dados.revisoes_aprovadas ?? 0;

  adminRevisoesBloqueadas.textContent =
    dados.revisoes_bloqueadas ?? 0;


  adminValorTotal.textContent =
    formatarMoeda(
      dados.valor_total
    );

  adminTicketMedio.textContent =
    formatarMoeda(
      dados.ticket_medio
    );

  adminScoreMedio.textContent =
    dados.score_medio ?? 0;
}


// =========================================================
// EVENTOS DO MENU
// =========================================================

function registrarEventosMenu() {
  menuAdmin.forEach(
    (botao) => {
      botao.addEventListener(
        "click",
        () => {
          const secao =
            botao.dataset.secaoAdmin;


          mostrarSecaoAdmin(
            secao
          );


          if (
            secao === "admin_inicio"
          ) {
            socket.emit(
              "obter_resumo_admin"
            );
          }


          if (
            secao === "admin_usuarios"
          ) {
            limparMensagem(
              mensagemStatusUsuario
            );

            socket.emit(
              "listar_usuarios_admin"
            );
          }


          if (
            secao === "admin_transacoes"
          ) {
            limparMensagem(
              mensagemRevisao
            );

            socket.emit(
              "listar_transacoes_admin"
            );
          }


          if (
            secao === "admin_risco"
          ) {
            limparMensagem(
              mensagemListaRisco
            );

            socket.emit(
              "listar_lista_risco"
            );
          }


          if (
            secao ===
            "admin_estatisticas"
          ) {
            socket.emit(
              "obter_estatisticas_admin"
            );
          }
        }
      );
    }
  );
}


// =========================================================
// EVENTOS DOS FILTROS
// =========================================================

function registrarEventosFiltros() {
  filtroAdminBusca.addEventListener(
    "input",
    aplicarFiltrosAdmin
  );


  [
    filtroAdminRisco,
    filtroAdminStatus,
    filtroAdminOrigem
  ].forEach(
    (campo) => {
      campo.addEventListener(
        "change",
        aplicarFiltrosAdmin
      );
    }
  );
}


// =========================================================
// EVENTOS DA LISTA DE RISCO
// =========================================================

function registrarEventosListaRisco() {
  formListaRisco.addEventListener(
    "submit",
    enviarListaRisco
  );


  riscoNome.addEventListener(
    "blur",
    () => validarObrigatorio(
      riscoNome,
      "Informe o nome."
    )
  );


  riscoDocumento.addEventListener(
    "blur",
    () => validarDocumento(
      riscoDocumento,
      riscoTipoPessoa.value
    )
  );


  riscoMotivo.addEventListener(
    "blur",
    () => validarObrigatorio(
      riscoMotivo,
      "Informe o motivo."
    )
  );


  [
    riscoNome,
    riscoDocumento,
    riscoMotivo
  ].forEach(
    (campo) => {
      campo.addEventListener(
        "input",
        () => limparErro(campo)
      );
    }
  );


  riscoTipoPessoa.addEventListener(
    "change",
    () => {
      riscoDocumento.value = "";

      atualizarCampoDocumento(
        riscoTipoPessoa.value,
        labelRiscoDocumento,
        riscoDocumento
      );
    }
  );
}


// =========================================================
// EVENTOS DO SOCKET
// =========================================================

function registrarEventosSocket() {
  // Resumo
  socket.on(
    "resumo_admin",
    (resumo) => {
      if (!resumo) {
        return;
      }

      adminTotalLojistas.textContent =
        resumo.lojistas ?? 0;

      adminTotalTransacoes.textContent =
        resumo.transacoes ?? 0;

      adminEmAnalise.textContent =
        resumo.em_analise ?? 0;

      adminBloqueadas.textContent =
        resumo.bloqueadas ?? 0;
    }
  );


  // Estatísticas
  socket.on(
    "estatisticas_admin",
    (dados) => {
      if (!dados) {
        return;
      }

      preencherEstatisticasAdmin(
        dados
      );
    }
  );


  // Usuários
  socket.on(
    "lista_usuarios_admin",
    (usuarios) => {
      renderizarUsuariosAdmin(
        Array.isArray(usuarios)
          ? usuarios
          : []
      );
    }
  );


  socket.on(
    "resultado_usuarios_admin",
    (resultado) => {
      if (
        resultado &&
        !resultado.sucesso
      ) {
        mostrarMensagem(
          mensagemStatusUsuario,
          resultado.mensagem,
          false
        );
      }
    }
  );


  socket.on(
    "resultado_status_usuario",
    (resultado) => {
      if (!resultado) {
        return;
      }

      mostrarMensagem(
        mensagemStatusUsuario,
        resultado.mensagem,
        resultado.sucesso
      );


      if (resultado.sucesso) {
        socket.emit(
          "listar_usuarios_admin"
        );

        socket.emit(
          "obter_resumo_admin"
        );
      }
    }
  );


  // Transações
  socket.on(
    "lista_transacoes_admin",
    (transacoes) => {
      state.transacoesAdmin =
        Array.isArray(transacoes)
          ? transacoes
          : [];

      aplicarFiltrosAdmin();
    }
  );


  socket.on(
    "resultado_transacoes_admin",
    (resultado) => {
      if (
        resultado &&
        !resultado.sucesso
      ) {
        mostrarMensagem(
          mensagemRevisao,
          resultado.mensagem,
          false
        );
      }
    }
  );


  // Revisão
  socket.on(
    "resultado_revisao",
    (resultado) => {
      if (!resultado) {
        return;
      }

      mostrarMensagem(
        mensagemRevisao,
        resultado.mensagem,
        resultado.sucesso
      );


      if (resultado.sucesso) {
        socket.emit(
          "listar_transacoes_admin"
        );

        socket.emit(
          "obter_resumo_admin"
        );

        socket.emit(
          "obter_estatisticas_admin"
        );
      }
    }
  );


  // Lista de risco
  socket.on(
    "resultado_lista_risco",
    (resultado) => {
      if (!resultado) {
        return;
      }


      if (!resultado.sucesso) {
        const campo =
          resultado.campo
            ? $(resultado.campo)
            : null;


        if (campo) {
          mostrarErro(
            campo,
            resultado.mensagem
          );

          limparMensagem(
            mensagemListaRisco
          );
        } else {
          mostrarMensagem(
            mensagemListaRisco,
            resultado.mensagem,
            false
          );
        }

        return;
      }


      mostrarMensagem(
        mensagemListaRisco,
        resultado.mensagem,
        true
      );

      limparFormularioRisco();

      socket.emit(
        "listar_lista_risco"
      );
    }
  );


  socket.on(
    "lista_risco_atualizada",
    (lista) => {
      renderizarListaRisco(
        Array.isArray(lista)
          ? lista
          : []
      );
    }
  );
}


// =========================================================
// ABRIR PAINEL
// =========================================================

export function abrirPainelAdmin(
  usuario
) {
  state.usuarioAtual = usuario;

  painelAdmin.classList.remove(
    "oculto"
  );

  mostrarSecaoAdmin(
    "admin_inicio"
  );

  socket.emit(
    "obter_resumo_admin"
  );
}


// =========================================================
// FECHAR / LIMPAR
// =========================================================

export function fecharPainelAdmin() {
  painelAdmin.classList.add(
    "oculto"
  );

  state.transacoesAdmin = [];

  limparFiltrosAdmin();

  limparMensagem(
    mensagemStatusUsuario
  );

  limparMensagem(
    mensagemRevisao
  );

  limparMensagem(
    mensagemListaRisco
  );

  limparFormularioRisco();

  adminListaUsuarios.innerHTML = "";
  adminListaTransacoes.innerHTML = "";
  listaRiscoTabela.innerHTML = "";
}


// =========================================================
// INICIALIZAÇÃO
// =========================================================

export function inicializarAdmin() {
  registrarEventosMenu();
  registrarEventosFiltros();
  registrarEventosListaRisco();
  registrarEventosSocket();

  atualizarCampoDocumento(
    riscoTipoPessoa.value,
    labelRiscoDocumento,
    riscoDocumento
  );
}