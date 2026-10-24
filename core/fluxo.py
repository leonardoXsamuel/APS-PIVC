"""Fluxo completo de uma tentativa de acesso — o que o terminal do cofre dispara.

 1 bloqueio?  2 recurso  3 imagem -> vetor  4 identificação  5 autorização
 6 (nível 3) prova de vida + PIN  7 registro em log (com evidência se negado)
"""
from datetime import datetime

from core import auditoria, matcher, permissoes, seguranca
from db import repositorio
from visao import embedding, liveness
from visao.captura import ErroVisao, decodificar

MENSAGENS = {
    "concedido": "Acesso concedido.",
    "negado_nivel": "Nível de permissão insuficiente para este recurso.",
    "negado_divisao": "Este recurso pertence a outra divisão.",
    "negado_horario": "Fora do horário de expediente (08h–18h).",
    "nao_reconhecido": "Pessoa não reconhecida.",
    "falha_liveness": "Prova de vida falhou. Pisque olhando para a câmera.",
    "pin_invalido": "PIN inválido.",
}


def _resposta(resultado, usuario=None, score=0.0, evidencia=None):
    return {
        "concedido": resultado == "concedido",
        "resultado": resultado,
        "mensagem": MENSAGENS[resultado],
        "usuario": usuario["nome"] if usuario else None,
        "nivel": usuario["nivel"] if usuario else None,
        "score": round(score, 4),
        "evidencia": evidencia,
    }


def tentar_acesso(imagens: list, recurso_id: int, pin: str = "", agora=None):
    """`imagens`: bytes de 1+ quadros (vários quadros alimentam a prova de vida).
    Levanta ErroVisao para falhas que não são tentativa de acesso (sem rosto, câmera...)."""
    agora = agora or datetime.now()

    restante = auditoria.segundos_de_bloqueio()
    if restante:
        raise ErroVisao("terminal_bloqueado", f"Terminal bloqueado por tentativas negadas. Aguarde {restante}s.")

    recurso = repositorio.obter_recurso(recurso_id)
    if not recurso:
        raise ErroVisao("recurso_invalido", "Recurso não encontrado.")
    if not imagens:
        raise ErroVisao("imagem_invalida", "Nenhuma imagem recebida.")

    quadros = [decodificar(b) for b in imagens]
    principal = quadros[0]
    vetor = embedding.extrair(principal).vetor

    usuario_id, score = matcher.identificar(vetor)
    if usuario_id is None:
        ev = auditoria.registrar(None, recurso, "nao_reconhecido", score, principal)
        return _resposta("nao_reconhecido", score=score, evidencia=ev)

    usuario = repositorio.obter_usuario(usuario_id)
    ok, motivo = permissoes.autorizar(usuario, recurso, agora)

    if ok and permissoes.exige_segundo_fator(recurso):
        try:
            vivo = liveness.piscou(quadros)
        except ImportError:  # sem MediaPipe, o cofre mais sensível não abre
            vivo = False
        if not vivo:
            ok, motivo = False, "falha_liveness"
        elif not seguranca.pin_valido(pin, usuario["pin_hash"]):
            ok, motivo = False, "pin_invalido"

    ev = auditoria.registrar(usuario_id, recurso, motivo, score, None if ok else principal)
    return _resposta(motivo, usuario, score, ev)
