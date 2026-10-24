"""Fase 3 — Segmentação: SCRFD (caixa + 5 pontos) e alinhamento 112x112."""
import threading

import numpy as np

import config
from visao.captura import ErroVisao

_app = None
_trava = threading.Lock()


def modelo():
    """Carrega o buffalo_l uma única vez (download de ~300 MB na primeira execução)."""
    global _app
    with _trava:
        if _app is None:
            from insightface.app import FaceAnalysis
            _app = FaceAnalysis(name=config.MODELO)
            _app.prepare(ctx_id=config.CTX_ID, det_size=config.DET_SIZE)
    return _app


def detectar(bgr: np.ndarray) -> list:
    return modelo().get(bgr)


def exigir_um_rosto(rostos: list):
    """Garante exatamente um rosto, grande o bastante e com detecção confiável."""
    if not rostos:
        raise ErroVisao("sem_rosto", "Nenhum rosto detectado. Fique de frente para a câmera.")
    if len(rostos) > 1:
        raise ErroVisao("varios_rostos", "Mais de uma pessoa no enquadramento. Fique sozinho diante da câmera.")
    rosto = rostos[0]
    x1, _, x2, _ = rosto.bbox
    if (x2 - x1) < config.LARGURA_ROSTO_MIN:
        raise ErroVisao("rosto_longe", "Rosto muito longe. Aproxime-se da câmera (60–80 cm).")
    if float(rosto.det_score) < config.DET_SCORE_MIN:
        raise ErroVisao("baixa_qualidade", "Rosto pouco nítido. Melhore a iluminação e olhe para a câmera.")
    return rosto


def recorte_alinhado(bgr: np.ndarray, rosto) -> np.ndarray:
    """Alinha pelos 5 pontos (olhos na horizontal) e recorta 112x112 — entrada do ArcFace."""
    from insightface.utils.face_align import norm_crop
    return norm_crop(bgr, rosto.kps, image_size=112)
