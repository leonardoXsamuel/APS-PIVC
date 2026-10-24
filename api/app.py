"""API do cofre biométrico (APS-12).  Subir com:  uvicorn api.app:app --reload

Públicas (terminal):  GET /api/recursos, POST /api/reconhecer
Admin (X-Admin-Token): usuários, cadastro, logs, exportação, alertas
"""
import hmac

import config
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core import fluxo, galeria, relatorios, seguranca
from db import repositorio
from db.conexao import banco_disponivel
from visao import embedding
from visao.captura import ErroVisao, decodificar

import mysql.connector

app = FastAPI(title="Cofre Biométrico")


# ---------- infraestrutura ----------
@app.on_event("startup")
def iniciar():
    if banco_disponivel():
        galeria.recarregar()


@app.exception_handler(ErroVisao)
async def erro_visao(_, exc: ErroVisao):
    return JSONResponse(status_code=422, content={"erro": exc.codigo, "mensagem": exc.mensagem})


@app.exception_handler(mysql.connector.Error)
async def erro_banco(_, exc):
    return JSONResponse(status_code=503, content={
        "erro": "banco_indisponivel",
        "mensagem": "Banco de dados indisponível. Verifique se o MySQL está no ar e avise o administrador.",
    })


def _token_ok(token: str) -> bool:
    return hmac.compare_digest(token.encode(), config.ADMIN_TOKEN.encode())


def admin(x_admin_token: str = Header(default="")):
    if not _token_ok(x_admin_token):
        raise HTTPException(401, "Token de administrador inválido.")


@app.get("/api/admin/verificar", dependencies=[Depends(admin)])
def verificar_admin():
    """Usado pela tela de login das páginas de administração."""
    return {"ok": True}


# ---------- terminal ----------
@app.get("/api/saude")
def saude():
    return {"banco": banco_disponivel(), "galeria": galeria.tamanho()}


@app.get("/api/recursos")
def recursos():
    return repositorio.listar_recursos()


@app.post("/api/reconhecer")  # APS-16
async def reconhecer(
    recurso_id: int = Form(...),
    pin: str = Form(""),
    imagens: list[UploadFile] = File(...),
):
    dados = [await f.read() for f in imagens]
    return fluxo.tentar_acesso(dados, recurso_id, pin)


# ---------- cadastro (APS-15) ----------
@app.get("/api/divisoes", dependencies=[Depends(admin)])
def divisoes():
    return repositorio.listar_divisoes()


@app.post("/api/usuarios", status_code=201, dependencies=[Depends(admin)])
async def cadastrar(
    nome: str = Form(...),
    matricula: str = Form(...),
    cargo: str = Form(""),
    divisao_id: int | None = Form(None),
    nivel: int = Form(...),
    pin: str = Form(""),
    fotos: list[UploadFile] = File(...),
):
    if nivel not in (1, 2, 3):
        raise HTTPException(422, "Nível deve ser 1, 2 ou 3.")
    if nivel == 2 and not divisao_id:
        raise HTTPException(422, "Diretor de divisão precisa de uma divisão vinculada.")
    if nivel == 3 and not seguranca.formato_pin_ok(pin):
        raise HTTPException(422, "Nível 3 exige PIN de 6 dígitos.")

    # extrai os vetores ANTES de gravar: foto ruim não deixa usuário pela metade
    vetores = [embedding.extrair(decodificar(await f.read())) for f in fotos]

    try:
        uid = repositorio.criar_usuario(
            nome, matricula, cargo or None, divisao_id, nivel,
            seguranca.hash_pin(pin) if nivel == 3 else None,
        )
    except mysql.connector.IntegrityError:
        raise HTTPException(409, f"Matrícula {matricula} já cadastrada.")
    for v in vetores:
        repositorio.adicionar_biometria(uid, embedding.para_bytes(v.vetor), v.qualidade)
    galeria.recarregar()
    return {"id": uid, "biometrias": len(vetores)}


@app.post("/api/usuarios/{uid}/biometrias", status_code=201, dependencies=[Depends(admin)])
async def adicionar_fotos(uid: int, fotos: list[UploadFile] = File(...)):
    if not repositorio.obter_usuario(uid):
        raise HTTPException(404, "Usuário não encontrado.")
    vetores = [embedding.extrair(decodificar(await f.read())) for f in fotos]
    for v in vetores:
        repositorio.adicionar_biometria(uid, embedding.para_bytes(v.vetor), v.qualidade)
    galeria.recarregar()
    return {"biometrias_adicionadas": len(vetores)}


# ---------- gerenciar pessoas (APS-19) ----------
class UsuarioEdicao(BaseModel):
    nome: str | None = None
    cargo: str | None = None
    divisao_id: int | None = None
    nivel: int | None = Field(default=None, ge=1, le=3)
    ativo: bool | None = None
    pin: str | None = None


@app.get("/api/usuarios", dependencies=[Depends(admin)])
def listar_usuarios():
    return repositorio.listar_usuarios()


@app.put("/api/usuarios/{uid}", dependencies=[Depends(admin)])
def editar(uid: int, dados: UsuarioEdicao):
    atual = repositorio.obter_usuario(uid)
    if not atual:
        raise HTTPException(404, "Usuário não encontrado.")
    campos = dados.model_dump(exclude_unset=True)
    pin = campos.pop("pin", None)
    if pin is not None:
        if not seguranca.formato_pin_ok(pin):
            raise HTTPException(422, "PIN deve ter 6 dígitos.")
        campos["pin_hash"] = seguranca.hash_pin(pin)
    nivel = campos.get("nivel", atual["nivel"])
    if nivel == 3 and not (campos.get("pin_hash") or atual["pin_hash"]):
        raise HTTPException(422, "Nível 3 exige PIN de 6 dígitos.")
    if nivel == 2 and not campos.get("divisao_id", atual["divisao_id"]):
        raise HTTPException(422, "Diretor de divisão precisa de uma divisão vinculada.")
    repositorio.atualizar_usuario(uid, campos)
    galeria.recarregar()
    return {"ok": True}


@app.delete("/api/usuarios/{uid}", dependencies=[Depends(admin)])
def remover(uid: int):
    if not repositorio.remover_usuario(uid):
        raise HTTPException(404, "Usuário não encontrado.")
    galeria.recarregar()
    return {"ok": True}


# ---------- logs (APS-18) ----------
def _filtrar(inicio, fim, usuario_id, resultado, limite=500):
    return repositorio.consultar_acessos(inicio, fim, usuario_id, resultado, limite)


@app.get("/api/logs", dependencies=[Depends(admin)])
def logs(inicio: str | None = None, fim: str | None = None,
         usuario_id: int | None = None, resultado: str | None = None):
    return _filtrar(inicio, fim, usuario_id, resultado)


@app.get("/api/logs/exportar", dependencies=[Depends(admin)])  # APS-19
def exportar(formato: str = "csv", inicio: str | None = None, fim: str | None = None,
             usuario_id: int | None = None, resultado: str | None = None):
    registros = _filtrar(inicio, fim, usuario_id, resultado, limite=10000)
    if formato == "pdf":
        corpo, tipo = relatorios.para_pdf(registros), "application/pdf"
    elif formato == "csv":
        corpo, tipo = relatorios.para_csv(registros), "text/csv"
    else:
        raise HTTPException(422, "Formato deve ser csv ou pdf.")
    return Response(corpo, media_type=tipo,
                    headers={"Content-Disposition": f'attachment; filename="auditoria.{formato}"'})


@app.get("/api/evidencia/{nome}")
def evidencia(nome: str, token: str = ""):
    """Foto da tentativa negada. Token na query porque <img> não envia cabeçalhos."""
    if not _token_ok(token):
        raise HTTPException(401, "Token de administrador inválido.")
    caminho = (config.DIR_EVIDENCIAS / nome).resolve()
    if caminho.parent != config.DIR_EVIDENCIAS.resolve() or not caminho.is_file():
        raise HTTPException(404, "Evidência não encontrada.")
    return FileResponse(caminho, media_type="image/jpeg")


@app.get("/api/alertas", dependencies=[Depends(admin)])
def alertas():
    return repositorio.alertas_recentes(config.JANELA_ALERTA_MIN)


# ---------- frontend estático (deve ser o último mount) ----------
app.mount("/", StaticFiles(directory=config.BASE_DIR / "web", html=True), name="web")
