import json

from fastapi.exceptions import HTTPException
from fastapi import FastAPI, HTTPException, Path

import os

app = FastAPI()

# Rotas
@app.get("/", response_model=dict, 
        summary="Página inicial",
        description="Redireciona para a documentação interativa da API (Swagger UI).") 
def home():
    return {"escreva na URL": "http://127.0.0.1:5000/docs#/"}

PASTA_JSON = os.path.join(os.path.dirname(__file__), 'followers_and_following')

def listar_arquivos_json():
    arquivos = [f for f in os.listdir(PASTA_JSON) if f.endswith('.json')]
    return arquivos

def ler_arquivo_json(nome_arquivo):
    caminho = os.path.join(PASTA_JSON, nome_arquivo)
    if not os.path.isfile(caminho):
        raise HTTPException(status_code=404, detail='Arquivo não encontrado')
    with open(caminho, encoding='utf-8') as f:
        return json.load(f)

@app.get('/arquivos', response_model=list, summary='Lista arquivos JSON disponíveis')
def get_arquivos():
    return listar_arquivos_json()

@app.get('/arquivo/{nome}', response_model=dict, summary='Lê o conteúdo de um arquivo JSON')
def get_arquivo(nome: str = Path(..., description='Nome do arquivo JSON')):
    return ler_arquivo_json(nome)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=5000,
        reload=True,
        workers=1
    )