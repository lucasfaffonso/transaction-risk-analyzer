import { state } from "./state.js";

import {
  inicializarAutenticacao
} from "./auth.js";

import {
  inicializarModal,
  fecharDetalhesTransacao
} from "./modal.js";

import {
  abrirPainelLojista,
  fecharPainelLojista,
  inicializarLojista
} from "./lojista.js";

import {
  abrirPainelAdmin,
  fecharPainelAdmin,
  inicializarAdmin
} from "./admin.js";

import {
  $
} from "./utils.js";


const telaLogin = $("tela_login");
const telaCadastro = $("tela_cadastro");

const aplicacao = $("aplicacao");

const tituloUsuario = $("titulo_usuario");
const tipoUsuario = $("tipo_usuario");


function esconderAutenticacao() {
  telaLogin.classList.add(
    "oculto"
  );

  telaCadastro.classList.add(
    "oculto"
  );
}


function abrirAplicacao(usuario) {
  if (!usuario) {
    return;
  }

  state.usuarioAtual = usuario;

  esconderAutenticacao();

  fecharPainelLojista();
  fecharPainelAdmin();

  aplicacao.classList.remove(
    "oculto"
  );

  tituloUsuario.textContent =
    `Olá, ${usuario.nome}`;

  if (
    usuario.tipo_usuario === "ADMIN"
  ) {
    tipoUsuario.textContent =
      "Administrador";

    abrirPainelAdmin(
      usuario
    );

    return;
  }

  tipoUsuario.textContent =
    "Lojista";

  abrirPainelLojista(
    usuario
  );
}


function encerrarAplicacao() {
  fecharPainelLojista();
  fecharPainelAdmin();
  fecharDetalhesTransacao();

  state.usuarioAtual = null;
  state.pedidoVerificadoId = null;
  state.transacoesLojista = [];
  state.transacoesAdmin = [];

  tituloUsuario.textContent = "";
  tipoUsuario.textContent = "";

  aplicacao.classList.add(
    "oculto"
  );
}


function inicializarAplicacao() {
  inicializarModal();

  inicializarLojista();

  inicializarAdmin();

  inicializarAutenticacao({
    onAuthenticated:
      abrirAplicacao,

    onLogout:
      encerrarAplicacao
  });
}


inicializarAplicacao();