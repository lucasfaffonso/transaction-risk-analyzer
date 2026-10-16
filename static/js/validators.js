import {
  limparErro,
  mostrarErro,
  somenteDigitos
} from "./utils.js";


export const MIN_SENHA_CADASTRO = 8;
export const MAX_PEDIDO_ID = 80;


// =========================================================
// CAMPOS OBRIGATÓRIOS
// =========================================================

export function validarObrigatorio(
  campo,
  mensagem = "Preencha este campo."
) {
  limparErro(campo);

  if (!campo.value.trim()) {
    return mostrarErro(
      campo,
      mensagem
    );
  }

  return true;
}


// =========================================================
// E-MAIL
// =========================================================

export function validarEmail(campo) {
  limparErro(campo);

  const email = campo.value
    .trim()
    .toLowerCase();

  if (!email) {
    return mostrarErro(
      campo,
      "Informe o e-mail."
    );
  }

  if (email.length > 254) {
    return mostrarErro(
      campo,
      "E-mail muito longo."
    );
  }

  const partes = email.split("@");

  if (partes.length !== 2) {
    return mostrarErro(
      campo,
      "E-mail inválido."
    );
  }

  const [usuario, dominio] = partes;

  if (
    !usuario ||
    !dominio ||
    !dominio.includes(".") ||
    dominio.startsWith(".") ||
    dominio.endsWith(".")
  ) {
    return mostrarErro(
      campo,
      "E-mail inválido."
    );
  }

  return true;
}


// =========================================================
// CPF / CNPJ
// =========================================================

export function validarDocumento(
  campo,
  tipoPessoa
) {
  limparErro(campo);

  const valorOriginal =
    campo.value.trim();

  if (!valorOriginal) {
    return mostrarErro(
      campo,
      "Informe o documento."
    );
  }

  const valorSemFormatacao =
    valorOriginal.replace(
      /[.\-/]/g,
      ""
    );

  if (!/^\d+$/.test(valorSemFormatacao)) {
    return mostrarErro(
      campo,
      "Documento deve conter apenas números."
    );
  }

  const documento =
    somenteDigitos(valorOriginal);

  if (
    tipoPessoa === "PF" &&
    documento.length !== 11
  ) {
    return mostrarErro(
      campo,
      "CPF precisa ter 11 dígitos."
    );
  }

  if (
    tipoPessoa === "PJ" &&
    documento.length !== 14
  ) {
    return mostrarErro(
      campo,
      "CNPJ precisa ter 14 dígitos."
    );
  }

  if (
    tipoPessoa !== "PF" &&
    tipoPessoa !== "PJ"
  ) {
    return mostrarErro(
      campo,
      "Tipo de pessoa inválido."
    );
  }

  return true;
}


// =========================================================
// TELEFONE
// =========================================================

export function validarTelefone(campo) {
  limparErro(campo);

  const valorOriginal =
    campo.value.trim();

  if (!valorOriginal) {
    return mostrarErro(
      campo,
      "Informe o telefone."
    );
  }

  if (
    !/^[\d()\-\s]+$/.test(
      valorOriginal
    )
  ) {
    return mostrarErro(
      campo,
      "Telefone deve conter apenas números."
    );
  }

  const telefone =
    somenteDigitos(valorOriginal);

  if (
    telefone.length !== 10 &&
    telefone.length !== 11
  ) {
    return mostrarErro(
      campo,
      "Telefone deve ter 10 ou 11 dígitos."
    );
  }

  return true;
}


// =========================================================
// SENHA
// =========================================================

export function validarSenha(
  campo,
  minimo = MIN_SENHA_CADASTRO
) {
  limparErro(campo);

  if (!campo.value) {
    return mostrarErro(
      campo,
      "Informe uma senha."
    );
  }

  if (campo.value.length < minimo) {
    return mostrarErro(
      campo,
      `A senha deve ter pelo menos ${minimo} caracteres.`
    );
  }

  return true;
}


export function validarConfirmacaoSenha(
  campoSenha,
  campoConfirmacao
) {
  limparErro(campoConfirmacao);

  if (!campoConfirmacao.value) {
    return mostrarErro(
      campoConfirmacao,
      "Confirme sua senha."
    );
  }

  if (
    campoConfirmacao.value !==
    campoSenha.value
  ) {
    return mostrarErro(
      campoConfirmacao,
      "As senhas não coincidem."
    );
  }

  return true;
}


// =========================================================
// ID da transação
// =========================================================

export function validarPedidoId(campo) {
  limparErro(campo);

  const pedidoId =
    campo.value.trim();

  if (!pedidoId) {
    return mostrarErro(
      campo,
      "Informe o ID da transação."
    );
  }

  if (
    pedidoId.length >
    MAX_PEDIDO_ID
  ) {
    return mostrarErro(
      campo,
      `O ID da transação deve ter no máximo ${MAX_PEDIDO_ID} caracteres.`
    );
  }

  return true;
}


// =========================================================
// VALOR DA TRANSAÇÃO
// =========================================================

export function validarValorTransacao(
  campo
) {
  limparErro(campo);

  if (!campo.value) {
    return mostrarErro(
      campo,
      "Informe o valor da compra."
    );
  }

  const valor = Number(
    campo.value
  );

  if (
    !Number.isFinite(valor) ||
    valor <= 0
  ) {
    return mostrarErro(
      campo,
      "O valor deve ser maior que zero."
    );
  }

  return true;
}