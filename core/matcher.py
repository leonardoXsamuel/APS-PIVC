"""Fase 5 — Reconhecimento: similaridade do cosseno contra a galeria."""
import numpy as np

import config
from core import galeria


def identificar(vetor: np.ndarray, limiar: float = None):
    """Devolve (usuario_id | None, melhor_score). Vetores já vêm normalizados em L2,
    então o cosseno é um produto escalar — a galeria inteira em uma multiplicação."""
    limiar = config.LIMIAR if limiar is None else limiar
    ids, matriz = galeria.instantaneo()
    if len(ids) == 0:
        return None, 0.0
    scores = matriz @ vetor
    i = int(np.argmax(scores))
    melhor = float(scores[i])
    return (int(ids[i]), melhor) if melhor >= limiar else (None, melhor)
