"""Ponto de entrada: sobe a API e o terminal web em http://localhost:8000"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("api.app:app", host="127.0.0.1", port=8000)
