"""Cria o banco e carrega os dados de demonstração (APS-10 e APS-11).

Uso:  python -m db.init_db
Os usuários de demonstração nascem SEM biometria: cadastre as fotos pela tela
de cadastro ou por `python -m db.cadastro_lote`.
"""
from pathlib import Path

import mysql.connector

import config
from core.seguranca import hash_pin

DEMO_DIVISOES = ["Biodiversidade", "Recursos Hídricos", "Clima e Qualidade do Ar"]

DEMO_RECURSOS = [  # nome, nivel_minimo, divisão (índice em DEMO_DIVISOES ou None)
    ("Antessala", 1, None),
    ("Catálogo de toxinas", 1, None),
    ("Acervo - Biodiversidade", 2, 0),
    ("Acervo - Recursos Hídricos", 2, 1),
    ("Cofre principal", 3, None),
]

DEMO_USUARIOS = [  # nome, matrícula, cargo, divisão, nível, pin
    ("Servidor Demonstração", "1001", "Analista Ambiental", 0, 1, None),
    ("Diretora de Biodiversidade", "2001", "Diretora de Divisão", 0, 2, None),
    ("Diretor de Recursos Hídricos", "2002", "Diretor de Divisão", 1, 2, None),
    ("Ministro do Meio Ambiente", "3001", "Ministro", None, 3, "123456"),
]


def main():
    cfg = {k: v for k, v in config.DB.items() if k != "database"}
    conn = mysql.connector.connect(**cfg)
    cur = conn.cursor()
    sql = (Path(__file__).with_name("schema.sql")).read_text(encoding="utf-8")
    linhas = [l for l in sql.splitlines() if not l.strip().startswith("--")]
    for comando in "\n".join(linhas).split(";"):
        if comando.strip():
            cur.execute(comando)
    conn.database = config.DB["database"]

    cur.execute("SELECT COUNT(*) FROM divisoes")
    if cur.fetchone()[0] == 0:
        ids = []
        for nome in DEMO_DIVISOES:
            cur.execute("INSERT INTO divisoes (nome) VALUES (%s)", (nome,))
            ids.append(cur.lastrowid)
        for nome, nivel, idx in DEMO_RECURSOS:
            cur.execute(
                "INSERT INTO recursos (nome, nivel_minimo, divisao_id) VALUES (%s,%s,%s)",
                (nome, nivel, ids[idx] if idx is not None else None),
            )
        for nome, mat, cargo, idx, nivel, pin in DEMO_USUARIOS:
            cur.execute(
                "INSERT INTO usuarios (nome, matricula, cargo, divisao_id, nivel, pin_hash) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (nome, mat, cargo, ids[idx] if idx is not None else None, nivel,
                 hash_pin(pin) if pin else None),
            )
        print("Dados de demonstração inseridos. PIN do ministro: 123456")
    conn.commit()
    cur.close()
    conn.close()
    print("Banco pronto.")


if __name__ == "__main__":
    main()
