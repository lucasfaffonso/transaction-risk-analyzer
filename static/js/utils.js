export function $(id) {
  return document.getElementById(id);
}


export function somenteDigitos(valor) {
  return String(valor || "").replace(/\D/g, "");
}


export function normalizarTexto(valor) {
  return String(valor ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[.\-/]/g, "")
    .toLowerCase()
    .trim();
}


export function formatarDocumento(valor) {
  if (!valor) {
    return "";
  }

  const documento = somenteDigitos(valor);

  if (documento.length === 11) {
    return (
      `${documento.slice(0, 3)}.` +
      `${documento.slice(3, 6)}.` +
      `${documento.slice(6, 9)}-` +
      documento.slice(9)
    );
  }

  if (documento.length === 14) {
    return (
      `${documento.slice(0, 2)}.` +
      `${documento.slice(2, 5)}.` +
      `${documento.slice(5, 8)}/` +
      `${documento.slice(8, 12)}-` +
      documento.slice(12)
    );
  }

  return valor;
}


export function formatarTelefone(valor) {
  if (!valor) {
    return "";
  }

  const telefone = somenteDigitos(valor);

  if (telefone.length === 11) {
    return (
      `(${telefone.slice(0, 2)}) ` +
      `${telefone.slice(2, 7)}-` +
      telefone.slice(7)
    );
  }

  if (telefone.length === 10) {
    return (
      `(${telefone.slice(0, 2)}) ` +
      `${telefone.slice(2, 6)}-` +
      telefone.slice(6)
    );
  }

  return valor;
}


export function formatarMoeda(valor) {
  return Number(valor || 0).toLocaleString(
    "pt-BR",
    {
      style: "currency",
      currency: "BRL"
    }
  );
}


export function limparMensagem(elemento) {
  if (!elemento) {
    return;
  }

  elemento.textContent = "";

  elemento.classList.remove(
    "sucesso",
    "erro-geral"
  );
}


export function mostrarMensagem(
  elemento,
  texto,
  sucesso = false
) {
  if (!elemento) {
    return;
  }

  limparMensagem(elemento);

  elemento.textContent = texto || "";

  if (!texto) {
    return;
  }

  elemento.classList.add(
    sucesso
      ? "sucesso"
      : "erro-geral"
  );
}


export function mostrarErro(campo, texto) {
  if (!campo) {
    return false;
  }

  const erro = document.getElementById(
    `erro_${campo.id}`
  );

  if (erro) {
    erro.textContent = texto;
  }

  campo.classList.add("erro-input");

  return false;
}


export function limparErro(campo) {
  if (!campo) {
    return;
  }

  const erro = document.getElementById(
    `erro_${campo.id}`
  );

  if (erro) {
    erro.textContent = "";
  }

  campo.classList.remove("erro-input");
}


export function atualizarCampoDocumento(
  tipo,
  label,
  campo,
  possessivo = false
) {
  const documento =
    tipo === "PF"
      ? "CPF"
      : "CNPJ";

  label.textContent = documento;

  campo.placeholder =
    possessivo
      ? `Digite seu ${documento}`
      : `Digite o ${documento}`;

  limparErro(campo);
}


export function aplicarClasseRisco(
  elemento,
  nivel
) {
  const classes = {
    BAIXO: "risco-baixo",
    "MÉDIO": "risco-medio",
    ALTO: "risco-alto",
    "CRÍTICO": "risco-critico"
  };

  const classe = classes[nivel];

  if (classe) {
    elemento.classList.add(classe);
  }
}


export function criarCelula(valor = "") {
  const td = document.createElement("td");

  td.textContent = valor ?? "";

  return td;
}


export function criarBotao(
  texto,
  classe,
  aoClicar
) {
  const botao = document.createElement(
    "button"
  );

  botao.type = "button";
  botao.textContent = texto;
  botao.className = classe;

  botao.addEventListener(
    "click",
    aoClicar
  );

  return botao;
}


export function criarBadgeOrigem(
  origem = "WEB"
) {
  const badge = document.createElement(
    "span"
  );

  badge.textContent = origem;

  badge.className =
    origem === "API"
      ? "badge-origem badge-api"
      : "badge-origem badge-web";

  return badge;
}