// Utilidades compartilhadas pelas quatro telas.
const MENU = [
  ["/", "Terminal do cofre"], ["/cadastro.html", "Cadastro"],
  ["/pessoas.html", "Pessoas"], ["/logs.html", "Logs"],
];

function menu() {
  const atual = location.pathname === "/index.html" ? "/" : location.pathname;
  const sair = sessionStorage.getItem("admin_token")
    ? `<a href="#" id="sair" style="margin-left:auto">Sair</a>` : "";
  document.body.insertAdjacentHTML("afterbegin",
    "<nav>" + MENU.map(([h, t]) => `<a href="${h}" class="${h === atual ? "on" : ""}">${t}</a>`).join("") + sair + "</nav>");
  document.getElementById("sair")?.addEventListener("click", ev => {
    ev.preventDefault(); sessionStorage.removeItem("admin_token"); location.href = "/";
  });
}

// Token guardado na sessão (aba). Só é gravado depois que o servidor o aceita.
function token() { return sessionStorage.getItem("admin_token") || ""; }

// Pergunta ao servidor se o token vale. Devolve "ok", "invalido" ou "fora".
async function verificarToken(t) {
  try {
    const r = await fetch("/api/admin/verificar", { headers: { "X-Admin-Token": t } });
    return r.ok ? "ok" : (r.status === 401 ? "invalido" : "fora");
  } catch { return "fora"; }
}

function liberarPagina() { document.body.classList.add("liberado"); }

// Porta das páginas de administração (<body class="admin">): o conteúdo só aparece
// depois que o servidor confirmar o token. "Cancelar" volta ao terminal público.
async function exigirAdmin() {
  const guardado = token();
  if (guardado && await verificarToken(guardado) === "ok") return liberarPagina();
  sessionStorage.removeItem("admin_token");

  return new Promise(resolve => {
    const fundo = document.createElement("div");
    fundo.className = "loginbg";
    fundo.innerHTML = `<form class="card login" autocomplete="off">
      <h2>Acesso administrativo</h2>
      <p style="color:var(--mut);margin:0">Informe o token de administrador (variável ADMIN_TOKEN do arquivo .env).</p>
      <input type="password" name="t" placeholder="Token" required autofocus>
      <div class="erro" hidden></div>
      <div class="row"><button type="submit">Entrar</button>
        <button type="button" class="sec" id="cancelarLogin">Cancelar</button></div></form>`;
    document.body.append(fundo);
    const form = fundo.querySelector("form"), campo = form.t, erro = fundo.querySelector(".erro");
    fundo.querySelector("#cancelarLogin").onclick = () => location.replace("/");
    form.onsubmit = async ev => {
      ev.preventDefault();
      const t = campo.value.trim(); if (!t) return;
      form.querySelector("button[type=submit]").disabled = true;
      const r = await verificarToken(t);
      form.querySelector("button[type=submit]").disabled = false;
      if (r === "ok") {
        sessionStorage.setItem("admin_token", t);
        fundo.remove(); liberarPagina(); resolve();
      } else {
        erro.hidden = false;
        erro.textContent = r === "fora" ? "Servidor fora do ar. Verifique se a API está rodando." : "Token incorreto.";
        campo.value = ""; campo.focus();
      }
    };
  });
}

// Chamada à API; devolve JSON ou lança Error com a mensagem do servidor.
async function api(caminho, opcoes = {}, admin = false) {
  opcoes.headers = { ...(opcoes.headers || {}) };
  if (admin) opcoes.headers["X-Admin-Token"] = token();
  let r;
  try { r = await fetch(caminho, opcoes); }
  catch { throw new Error("Servidor fora do ar. Verifique se a API está rodando."); }
  if (r.status === 401) {
    sessionStorage.removeItem("admin_token");
    if (admin) setTimeout(() => location.reload(), 1200);   // reabre a tela de login
    throw new Error("Token de administrador inválido.");
  }
  const tipo = r.headers.get("content-type") || "";
  const corpo = tipo.includes("json") ? await r.json() : await r.blob();
  if (!r.ok) throw new Error(corpo.mensagem || corpo.detail || "Erro inesperado.");
  return corpo;
}

// --- câmera ---
async function abrirCamera(video) {
  if (!navigator.mediaDevices?.getUserMedia)
    throw new Error("Este navegador não permite câmera. Abra em http://localhost:8000.");
  try {
    const s = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: false });
    video.srcObject = s;
    await video.play();
  } catch (e) {
    throw new Error(e.name === "NotAllowedError"
      ? "Permissão de câmera negada. Libere a câmera no navegador."
      : "Câmera não encontrada. Conecte uma webcam e recarregue.");
  }
}

function quadro(video) {
  if (!video.videoWidth) return Promise.reject(new Error("A câmera ainda não está ativa."));
  const c = document.createElement("canvas");
  c.width = video.videoWidth; c.height = video.videoHeight;
  c.getContext("2d").drawImage(video, 0, 0);
  return new Promise(res => c.toBlob(res, "image/jpeg", 0.92));
}

const esperar = ms => new Promise(r => setTimeout(r, ms));
function esc(s) { return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
document.addEventListener("DOMContentLoaded", menu);
