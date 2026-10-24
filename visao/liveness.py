"""Prova de vida por piscada (EAR com MediaPipe FaceMesh)."""
import cv2
import numpy as np

import config

# índices do FaceMesh: p1, p2, p3, p4, p5, p6 de cada olho
_OLHO_DIR = (33, 160, 158, 133, 153, 144)
_OLHO_ESQ = (362, 385, 387, 263, 373, 380)

_mesh = None


def _facemesh():
    global _mesh
    if _mesh is None:
        import mediapipe as mp
        _mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True, max_num_faces=1, refine_landmarks=True
        )
    return _mesh


def _ear(pts, idx):
    p = [pts[i] for i in idx]
    vertical = np.linalg.norm(p[1] - p[5]) + np.linalg.norm(p[2] - p[4])
    horizontal = 2.0 * np.linalg.norm(p[0] - p[3])
    return vertical / horizontal if horizontal else 0.0


def ear_do_quadro(bgr: np.ndarray):
    """EAR médio dos dois olhos, ou None se o FaceMesh não achar rosto."""
    h, w = bgr.shape[:2]
    res = _facemesh().process(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    if not res.multi_face_landmarks:
        return None
    pts = np.array([[l.x * w, l.y * h] for l in res.multi_face_landmarks[0].landmark])
    return (_ear(pts, _OLHO_DIR) + _ear(pts, _OLHO_ESQ)) / 2.0


def piscou(quadros: list) -> bool:
    """True se, na sequência de quadros, os olhos foram vistos abertos e fechados."""
    ears = [e for e in (ear_do_quadro(q) for q in quadros) if e is not None]
    if len(ears) < 3:
        return False
    return min(ears) < config.EAR_FECHADO and max(ears) > config.EAR_ABERTO
