"""Configuração central: limiar, câmera, credenciais do banco."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv é opcional
    pass

BASE_DIR = Path(__file__).resolve().parent
DIR_CADASTRO = BASE_DIR / "dados" / "cadastro"
DIR_EVIDENCIAS = BASE_DIR / "dados" / "evidencias"
DIR_FIGURAS = BASE_DIR / "docs" / "figuras"

DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "cofre_biometrico"),
}

# --- reconhecimento (fase 5) ---
LIMIAR = float(os.getenv("LIMIAR", "0.40"))   # similaridade do cosseno mínima
MODELO = "buffalo_l"                          # SCRFD + ArcFace
DET_SIZE = (640, 640)
CTX_ID = int(os.getenv("CTX_ID", "-1"))       # -1 CPU, 0 GPU

# --- qualidade da imagem ---
LUMINOSIDADE_MIN = 40        # média do canal L abaixo disso = escura demais
LARGURA_ROSTO_MIN = 80       # px; menor que isso = rosto muito longe
DET_SCORE_MIN = 0.50

# --- prova de vida (piscada, EAR) ---
EAR_FECHADO = 0.20
EAR_ABERTO = 0.25

# --- segurança ---
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin")
PIN_PEPPER = os.getenv("PIN_PEPPER", "pepper-dev")
HORARIO_EXPEDIENTE = (8, 18)     # nível 2 só dentro desse intervalo
NEGATIVAS_PARA_BLOQUEIO = 3      # sequência de negativas que trava o terminal
BLOQUEIO_SEGUNDOS = 60
JANELA_ALERTA_MIN = 5            # alertas do nível 3 exibidos no admin
