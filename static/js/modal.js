import {
  $,
  formatarDocumento,
  formatarMoeda
} from "./utils.js";


const modalDetalhes = $("modal_detalhes");
const modalDetalhesTitulo = $("modal_detalhes_titulo");
const modalDetalhesSubtitulo = $("modal_detalhes_subtitulo");
const modalDetalhesConteudo = $("modal_detalhes_conteudo");
const fecharModalDetalhes = $("fechar_modal_detalhes");


// =========================================================
// AUXILIARES
// =========================================================

function criarItemDetalhe(
  rotulo,
  valor
) {
  const item = document.createElement(
    "div"
  );

  item.className = "detalhe-item";


  const label = document.createElement(
    "span"
  );

  label.textContent = rotulo;


  const conteudo = document.createElement(
    "strong"
  );

  conteudo.textContent =
    valor ?? "-";


  item.append(
    label,
    conteudo
  );

  return item;
}


function adicionarSecaoDetalhes(
  tituloTexto,
  itens
) {
  const bloco = document.createElement(
    "section"
  );

  bloco.className = "detalhe-secao";


  const titulo = document.createElement(
    "h4"
  );

  titulo.textContent = tituloTexto;


  const grid = document.createElement(
    "div"
  );

  grid.className = "detalhes-grid";


  itens.forEach(
    ([rotulo, valor]) => {
      grid.appendChild(
        criarItemDetalhe(
          rotulo,
          valor
        )
      );
    }
  );


  bloco.append(
    titulo,
    grid
  );

  modalDetalhesConteudo.appendChild(
    bloco
  );
}


function adicionarMotivos(transacao) {
  const bloco = document.createElement(
    "section"
  );

  bloco.className = "detalhe-secao";


  const titulo = document.createElement(
    "h4"
  );

  titulo.textContent =
    "Motivos do score";


  const lista = document.createElement(
    "ul"
  );

  lista.className =
    "lista-motivos-detalhes";


  const motivos =
    transacao.motivos_risco || [];


  if (!motivos.length) {
    const item = document.createElement(
      "li"
    );

    item.textContent =
      "Nenhum fator de risco identificado.";

    lista.appendChild(item);
  } else {
    motivos.forEach(
      (motivo) => {
        const item =
          document.createElement(
            "li"
          );

        item.textContent =
          `+${motivo.pontos} - ${motivo.motivo}`;

        lista.appendChild(item);
      }
    );
  }


  bloco.append(
    titulo,
    lista
  );

  modalDetalhesConteudo.appendChild(
    bloco
  );
}


// =========================================================
// ABRIR MODAL
// =========================================================

export function abrirDetalhesTransacao(
  transacao,
  mostrarLojista = false
) {
  modalDetalhesConteudo.innerHTML = "";


  modalDetalhesTitulo.textContent =
    `Transação #${transacao.transacao_id}`;


  modalDetalhesSubtitulo.textContent =
    `${transacao.data_hora} • Origem ${transacao.origem || "WEB"}`;


  // Lojista
  if (mostrarLojista) {
    adicionarSecaoDetalhes(
      "Lojista",
      [
        [
          "Nome",
          transacao.lojista_nome
        ],
        [
          "E-mail",
          transacao.lojista_email
        ]
      ]
    );
  }


  // Comprador
  adicionarSecaoDetalhes(
    "Comprador",
    [
      [
        "Nome",
        transacao.comprador_nome
      ],
      [
        "Tipo",
        transacao.comprador_tipo_pessoa === "PF"
          ? "Pessoa Física"
          : "Pessoa Jurídica"
      ],
      [
        "Documento",
        formatarDocumento(
          transacao.comprador_documento
        )
      ],
      [
        "E-mail",
        transacao.comprador_email
      ]
    ]
  );


  // Compra
  adicionarSecaoDetalhes(
    "Compra",
    [
      [
        "ID do pedido",
        transacao.pedido_id || "-"
      ],
      [
        "Valor",
        formatarMoeda(
          transacao.valor
        )
      ],
      [
        "Pagamento",
        transacao.forma_pagamento
      ],
      [
        "Origem",
        transacao.origem || "WEB"
      ]
    ]
  );


  // Análise de risco
  adicionarSecaoDetalhes(
    "Análise de risco",
    [
      [
        "Score",
        transacao.pontuacao_risco
      ],
      [
        "Nível de risco",
        transacao.nivel_risco
      ],
      [
        "Status automático",
        transacao.status_automatico
      ],
      [
        "Status atual",
        transacao.status
      ]
    ]
  );


  adicionarMotivos(transacao);


  // Revisão manual
  if (
    transacao.revisada ||
    transacao.status_automatico ===
      "EM ANÁLISE"
  ) {
    adicionarSecaoDetalhes(
      "Revisão manual",
      [
        [
          "Revisada",
          transacao.revisada
            ? "Sim"
            : "Não"
        ],
        [
          "Decisão",
          transacao.decisao_revisao ||
            "Aguardando revisão"
        ],
        [
          "Data da revisão",
          transacao.data_revisao ||
            "-"
        ]
      ]
    );
  }


  modalDetalhes.classList.remove(
    "oculto"
  );

  document.body.classList.add(
    "modal-aberto"
  );
}


// =========================================================
// FECHAR MODAL
// =========================================================

export function fecharDetalhesTransacao() {
  modalDetalhes.classList.add(
    "oculto"
  );

  document.body.classList.remove(
    "modal-aberto"
  );
}


// =========================================================
// INICIALIZAÇÃO
// =========================================================

export function inicializarModal() {
  fecharModalDetalhes.addEventListener(
    "click",
    fecharDetalhesTransacao
  );


  modalDetalhes.addEventListener(
    "click",
    (event) => {
      if (
        event.target === modalDetalhes
      ) {
        fecharDetalhesTransacao();
      }
    }
  );


  document.addEventListener(
    "keydown",
    (event) => {
      if (
        event.key === "Escape" &&
        !modalDetalhes.classList.contains(
          "oculto"
        )
      ) {
        fecharDetalhesTransacao();
      }
    }
  );
}