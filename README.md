# Cofre Biométrico — Ministério do Meio Ambiente

Identificação facial com três níveis de permissão. APS 5º/6º Ciência da Computação 2026/2 · PIVC.

**Stack:** Python 3.11 · OpenCV · InsightFace (SCRFD + ArcFace) · MediaPipe (prova de vida) · FastAPI · MySQL · frontend web.

## Instalação

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        # ajuste DB_PASSWORD, ADMIN_TOKEN, PIN_PEPPER

python -m db.init_db          # cria o banco, tabelas e dados de demonstração
python main.py                # http://localhost:8000
```

O modelo `buffalo_l` (~300 MB) é baixado na primeira execução.

## Cadastrar biometrias

- **Pela tela:** `http://localhost:8000/cadastro.html` (pede o token do `.env`).
- **Em lote:** coloque fotos em `dados/cadastro/<matricula>/` e rode `python -m db.cadastro_lote`.

Dados de demonstração: matrículas `1001` (nível 1), `2001` (nível 2, Biodiversidade), `2002` (nível 2, Recursos Hídricos), `3001` (ministro, PIN `123456`).

## Níveis de acesso

| Nível | Quem | Pode |
|---|---|---|
| 1 | Servidores | Antessala e catálogo de toxinas |
| 2 | Diretores de divisão | + acervo da **própria** divisão, só 08h–18h |
| 3 | Ministro | Cofre principal; exige **prova de vida + PIN** |

Tentativas negadas gravam o quadro em `dados/evidencias/`; três negativas seguidas bloqueiam o terminal por 60 s; negativas no cofre principal acendem alerta na tela de logs.

## Estrutura

```
main.py · config.py
visao/   captura · preproc · detector · embedding · liveness   (fases 1–4)
core/    galeria · matcher · permissoes · auditoria · fluxo    (fase 5 + regras)
db/      schema.sql · repositorio · init_db · cadastro_lote
api/     app.py                                                (rotas)
web/     index (terminal) · cadastro · pessoas · logs
testes/  test_permissoes.py · avaliacao.py (FAR, FRR, ROC)
docs/    fluxo.md · gerar_figuras.py
```

Fluxo completo e rotas: [`docs/fluxo.md`](docs/fluxo.md).

## Testes e métricas

```powershell
pytest testes                       # regras de permissão
python -m testes.avaliacao          # acurácia, FAR, FRR, ROC, matriz de confusão
python docs/gerar_figuras.py foto.jpg   # figura das fases para a dissertação
```

Calibre `LIMIAR` (padrão 0,40) com a curva de `docs/figuras/roc.png`.

## Backlog (Jira APS)

| Sprint | Tarefas | Onde está |
|---|---|---|
| APS-1 Design | 6, 7, 8 | `docs/fluxo.md` |
| APS-2 Banco | 9, 10, 11 | `db/schema.sql`, `db/init_db.py` |
| APS-3 Backend | 12–19 | `api/`, `core/`, `visao/` |
| APS-4 Frontend | 20–23 | `web/` |
| APS-5 Documentação | 24 | este arquivo |
