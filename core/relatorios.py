"""Exportação do log de auditoria em CSV e PDF."""
import csv
import io

COLUNAS = ["ocorrido_em", "usuario", "recurso", "resultado", "score"]
TITULOS = ["Data/hora", "Pessoa", "Recurso", "Resultado", "Score"]


def _linha(r):
    return [
        str(r["ocorrido_em"]),
        r["usuario"] or "— não reconhecido —",
        r["recurso"] or "—",
        r["resultado"],
        f"{r['score']:.3f}" if r["score"] is not None else "",
    ]


def para_csv(registros) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(TITULOS)
    w.writerows(_linha(r) for r in registros)
    return ("﻿" + buf.getvalue()).encode("utf-8")  # BOM para o Excel abrir com acentos


def para_pdf(registros) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), title="Relatório de auditoria")
    estilos = getSampleStyleSheet()
    dados = [TITULOS] + [_linha(r) for r in registros]
    tabela = Table(dados, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0C6A70")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]
    for i, r in enumerate(registros, start=1):
        if r["resultado"] != "concedido":
            estilo.append(("TEXTCOLOR", (3, i), (3, i), colors.HexColor("#A93B2C")))
    tabela.setStyle(TableStyle(estilo))
    doc.build([
        Paragraph("Cofre Biométrico — Relatório de auditoria", estilos["Title"]),
        Paragraph(f"{len(registros)} registro(s)", estilos["Normal"]),
        tabela,
    ])
    return buf.getvalue()
