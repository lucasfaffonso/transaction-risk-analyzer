import { socket } from "./socket.js";

import {
  $,
  atualizarCampoDocumento,
  limparErro,
  limparMensagem,
  mostrarErro,
  mostrarMensagem
} from "./utils.js";

import {
  validarConfirmacaoSenha,
  validarDocumento,
  validarEmail,
  validarObrigatorio,
  validarSenha,
  validarTelefone
} from "./validators.js";


// =========================================================
// ELEMENTOS
// =========================================================

// Telas
const telaLogin = $("tela_login");
const telaCadastro = $("tela_cadastro");
const aplicacao = $("aplicacao");


// Login
const formLogin = $("form_login");
const loginEmail = $("login_email");
const loginSenha = $("login_senha");
const mensagemLogin = $("mensagem_login");

const botaoAbrirCadastro = $("abrir_cadastro");


// Cadastro
const formCadastro = $("form_cadastro");

const cadastroNome = $("cadastro_nome");
const cadastroTipoPessoa = $("cadastro_tipo_pessoa");
const cadastroDocumento = $("cadastro_documento");
const cadastroEmail = $("cadastro_email");
const cadastroTelefone = $("cadastro_telefone");
const cadastroSenha = $("cadastro_senha");
const cadastroConfirmarSenha = $("cadastro_confirmar_senha");

const labelCadastroDocumento = $("label_cadastro_documento");
const mensagemCadastro = $("mensagem_cadastro");

const botaoAbrirLogin = $("abrir_login");


// Logout
const botaoSair = $("botao_sair");


// Sessão
const CHAVE_TOKEN_SESSAO = "transaction_risk_token_sessao";


// =========================================================
// CALLBACKS
// =========================================================

let aoAutenticar = null;
let aoSair = null;


// =========================================================
// TELAS
// =========================================================

export function mostrarLogin() {
  telaLogin.classList.remove("oculto");
  telaCadastro.classList.add("oculto");
  aplicacao.classList.add("oculto");

  limparMensagem(mensagemCadastro);
}


export function mostrarCadastro() {
  telaLogin.classList.add("oculto");
  telaCadastro.classList.remove("oculto");
  aplicacao.classList.add("oculto");

  limparMensagem(mensagemLogin);
}


// =========================================================
// AUXILIARES
// =========================================================

function limparErrosLogin() {
  limparErro(loginEmail);
  limparErro(loginSenha);
}


function limparErrosCadastro() {
  [
    cadastroNome,
    cadastroDocumento,
    cadastroEmail,
    cadastroTelefone,
    cadastroSenha,
    cadastroConfirmarSenha
  ].forEach(limparErro);
}


function restaurarFormularioCadastro() {
  formCadastro.reset();

  limparErrosCadastro();
  limparMensagem(mensagemCadastro);

  cadastroTipoPessoa.value = "PF";

  atualizarCampoDocumento(
    "PF",
    labelCadastroDocumento,
    cadastroDocumento,
    true
  );
}


function localizarCampoCadastro(nomeCampo) {
  const campos = {
    nome: cadastroNome,
    cadastro_nome: cadastroNome,

    documento: cadastroDocumento,
    cadastro_documento: cadastroDocumento,

    email: cadastroEmail,
    cadastro_email: cadastroEmail,

    telefone: cadastroTelefone,
    cadastro_telefone: cadastroTelefone,

    senha: cadastroSenha,
    cadastro_senha: cadastroSenha,

    confirmar_senha: cadastroConfirmarSenha,
    cadastro_confirmar_senha: cadastroConfirmarSenha
  };

  return campos[nomeCampo] || $(nomeCampo);
}


function salvarTokenSessao(token) {
  if (
    typeof token !== "string" ||
    !token
  ) {
    return;
  }

  sessionStorage.setItem(
    CHAVE_TOKEN_SESSAO,
    token
  );
}


function obterTokenSessao() {
  return sessionStorage.getItem(
    CHAVE_TOKEN_SESSAO
  );
}


function removerTokenSessao() {
  sessionStorage.removeItem(
    CHAVE_TOKEN_SESSAO
  );
}


function tentarRestaurarSessao() {
  const tokenSessao = obterTokenSessao();

  if (!tokenSessao) {
    return;
  }

  socket.emit(
    "restaurar_sessao",
    {
      token_sessao: tokenSessao
    }
  );
}


// =========================================================
// LOGIN
// =========================================================

function enviarLogin(event) {
  event.preventDefault();

  limparMensagem(mensagemLogin);

  const emailValido =
    validarEmail(loginEmail);

  const senhaValida =
    validarObrigatorio(
      loginSenha,
      "Informe a senha."
    );

  if (
    !emailValido ||
    !senhaValida
  ) {
    return;
  }

  socket.emit(
    "login",
    {
      email: loginEmail.value.trim(),
      senha: loginSenha.value
    }
  );
}


// =========================================================
// CADASTRO
// =========================================================

function enviarCadastro(event) {
  event.preventDefault();

  limparMensagem(mensagemCadastro);

  const validacoes = [
    validarObrigatorio(
      cadastroNome,
      "Informe o nome."
    ),

    validarDocumento(
      cadastroDocumento,
      cadastroTipoPessoa.value
    ),

    validarEmail(
      cadastroEmail
    ),

    validarTelefone(
      cadastroTelefone
    ),

    validarSenha(
      cadastroSenha
    ),

    validarConfirmacaoSenha(
      cadastroSenha,
      cadastroConfirmarSenha
    )
  ];

  if (validacoes.includes(false)) {
    return;
  }

  socket.emit(
    "cadastrar_usuario",
    {
      nome:
        cadastroNome.value.trim(),

      tipo_pessoa:
        cadastroTipoPessoa.value,

      documento:
        cadastroDocumento.value,

      email:
        cadastroEmail.value.trim(),

      telefone:
        cadastroTelefone.value,

      senha:
        cadastroSenha.value
    }
  );
}


// =========================================================
// VERIFICAÇÃO DE CADASTRO
// =========================================================

function verificarDocumentoCadastro() {
  if (
    !validarDocumento(
      cadastroDocumento,
      cadastroTipoPessoa.value
    )
  ) {
    return;
  }

  socket.emit(
    "verificar_campo_cadastro",
    {
      campo: "documento",
      valor: cadastroDocumento.value
    }
  );
}


function verificarEmailCadastro() {
  if (!validarEmail(cadastroEmail)) {
    return;
  }

  socket.emit(
    "verificar_campo_cadastro",
    {
      campo: "email",
      valor: cadastroEmail.value.trim()
    }
  );
}


// =========================================================
// LOGOUT
// =========================================================

function solicitarLogout() {
  socket.emit(
    "logout",
    {
      token_sessao: obterTokenSessao()
    }
  );
}


// =========================================================
// EVENTOS DO DOM
// =========================================================

function registrarEventosLogin() {
  formLogin.addEventListener(
    "submit",
    enviarLogin
  );

  loginEmail.addEventListener(
    "blur",
    () => validarEmail(loginEmail)
  );

  loginSenha.addEventListener(
    "blur",
    () => validarObrigatorio(
      loginSenha,
      "Informe a senha."
    )
  );

  [
    loginEmail,
    loginSenha
  ].forEach(
    (campo) => {
      campo.addEventListener(
        "input",
        () => limparErro(campo)
      );
    }
  );
}


function registrarEventosCadastro() {
  formCadastro.addEventListener(
    "submit",
    enviarCadastro
  );

  cadastroNome.addEventListener(
    "blur",
    () => validarObrigatorio(
      cadastroNome,
      "Informe o nome."
    )
  );

  cadastroDocumento.addEventListener(
    "blur",
    verificarDocumentoCadastro
  );

  cadastroEmail.addEventListener(
    "blur",
    verificarEmailCadastro
  );

  cadastroTelefone.addEventListener(
    "blur",
    () => validarTelefone(
      cadastroTelefone
    )
  );

  cadastroSenha.addEventListener(
    "blur",
    () => validarSenha(
      cadastroSenha
    )
  );

  cadastroConfirmarSenha.addEventListener(
    "blur",
    () => validarConfirmacaoSenha(
      cadastroSenha,
      cadastroConfirmarSenha
    )
  );

  [
    cadastroNome,
    cadastroDocumento,
    cadastroEmail,
    cadastroTelefone,
    cadastroSenha,
    cadastroConfirmarSenha
  ].forEach(
    (campo) => {
      campo.addEventListener(
        "input",
        () => limparErro(campo)
      );
    }
  );

  cadastroTipoPessoa.addEventListener(
    "change",
    () => {
      cadastroDocumento.value = "";

      atualizarCampoDocumento(
        cadastroTipoPessoa.value,
        labelCadastroDocumento,
        cadastroDocumento,
        true
      );
    }
  );
}


function registrarEventosNavegacao() {
  botaoAbrirCadastro.addEventListener(
    "click",
    () => {
      limparMensagem(mensagemLogin);
      limparErrosLogin();

      mostrarCadastro();
    }
  );

  botaoAbrirLogin.addEventListener(
    "click",
    () => {
      limparMensagem(mensagemCadastro);
      limparErrosCadastro();

      mostrarLogin();
    }
  );

  botaoSair.addEventListener(
    "click",
    solicitarLogout
  );
}


// =========================================================
// EVENTOS DO SOCKET
// =========================================================

function registrarEventosSocket() {
  socket.on(
    "connect",
    tentarRestaurarSessao
  );


  socket.on(
    "resultado_verificacao_cadastro",
    (resultado) => {
      if (!resultado) {
        return;
      }

      if (resultado.disponivel) {
        return;
      }

      const campo =
        localizarCampoCadastro(
          resultado.campo
        );

      if (campo) {
        mostrarErro(
          campo,
          resultado.mensagem
        );
      }
    }
  );


  socket.on(
    "resultado_cadastro",
    (resultado) => {
      if (!resultado) {
        return;
      }

      if (!resultado.sucesso) {
        const campo =
          resultado.campo
            ? localizarCampoCadastro(
                resultado.campo
              )
            : null;

        if (campo) {
          mostrarErro(
            campo,
            resultado.mensagem
          );
        } else {
          mostrarMensagem(
            mensagemCadastro,
            resultado.mensagem,
            false
          );
        }

        return;
      }

      restaurarFormularioCadastro();

      salvarTokenSessao(
        resultado.token_sessao
      );

      if (typeof aoAutenticar === "function") {
        aoAutenticar(
          resultado.usuario
        );
      }
    }
  );


  socket.on(
    "resultado_login",
    (resultado) => {
      limparMensagem(
        mensagemLogin
      );

      if (
        !resultado ||
        !resultado.sucesso
      ) {
        mostrarMensagem(
          mensagemLogin,
          resultado?.mensagem ||
            "Não foi possível realizar o login.",
          false
        );

        return;
      }

      formLogin.reset();
      limparErrosLogin();

      salvarTokenSessao(
        resultado.token_sessao
      );

      if (typeof aoAutenticar === "function") {
        aoAutenticar(
          resultado.usuario
        );
      }
    }
  );


  socket.on(
    "resultado_restaurar_sessao",
    (resultado) => {
      if (
        !resultado ||
        !resultado.sucesso
      ) {
        removerTokenSessao();

        if (typeof aoSair === "function") {
          aoSair();
        }

        mostrarLogin();

        return;
      }

      if (typeof aoAutenticar === "function") {
        aoAutenticar(
          resultado.usuario
        );
      }
    }
  );


  socket.on(
    "resultado_logout",
    (resultado) => {
      if (
        !resultado ||
        !resultado.sucesso
      ) {
        return;
      }

      removerTokenSessao();

      restaurarFormularioCadastro();

      formLogin.reset();
      limparErrosLogin();

      limparMensagem(
        mensagemLogin
      );

      if (typeof aoSair === "function") {
        aoSair();
      }

      mostrarLogin();
    }
  );
}


// =========================================================
// INICIALIZAÇÃO
// =========================================================

export function inicializarAutenticacao({
  onAuthenticated,
  onLogout
} = {}) {
  aoAutenticar = onAuthenticated;
  aoSair = onLogout;

  registrarEventosLogin();
  registrarEventosCadastro();
  registrarEventosNavegacao();
  registrarEventosSocket();

  const tokenSessao = obterTokenSessao();

  if (tokenSessao) {
    if (socket.connected) {
      tentarRestaurarSessao();
    }
  } else {
    mostrarLogin();
  }

  atualizarCampoDocumento(
    cadastroTipoPessoa.value,
    labelCadastroDocumento,
    cadastroDocumento,
    true
  );
}