"""Registro de tentativas, evidência fotográfica e bloqueio por intrusão."""
import logging
from datetime import datetime

import cv2

import config
from db import repositorio

log = logging.getLogger("cofre.auditoria")


def salvar_evidencia(bgr, rotulo: str) -> str:
    config.DIR_EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    nome = f"{datetime.now():%Y%m%d_%H%M%S_%f}_{rotulo}.jpg"
    cv2.imwrite(str(config.DIR_EVIDENCIAS / nome), bgr)
    return f"dados/evidencias/{nome}"


def registrar(usuario_id, recurso, resultado, score, quadro=None):
    """Grava a tentativa. Toda negativa leva o quadro como evidência; negativa em
    recurso de nível 3 também marca alerta para o painel do admin."""
    negado = resultado != "concedido"
    evidencia = salvar_evidencia(quadro, resultado) if negado and quadro is not None else None
    alerta = negado and recurso is not None and recurso["nivel_minimo"] >= 3
    if alerta:
        log.warning("ALERTA: tentativa negada (%s) no recurso '%s'", resultado, recurso["nome"])
    repositorio.registrar_acesso(
        usuario_id, recurso["id"] if recurso else None, resultado, score, evidencia, alerta
    )
    return evidencia


def segundos_de_bloqueio() -> int:
    """Se as últimas N tentativas foram todas negadas e recentes, devolve o tempo restante."""
    n = config.NEGATIVAS_PARA_BLOQUEIO
    ultimas = repositorio.ultimos_resultados(n)
    if len(ultimas) < n or any(u["resultado"] == "concedido" for u in ultimas):
        return 0
    restante = config.BLOQUEIO_SEGUNDOS - int(ultimas[0]["idade"])
    return max(restante, 0)
