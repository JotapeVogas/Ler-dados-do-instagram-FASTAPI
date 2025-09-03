from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
import os, json

app = FastAPI(
    title="Instagram Data Reader",
    description="API simples para ler dados do Instagram usando Literal",
    version="1.0.0"
)

PASTA_JSON = os.path.join(os.path.dirname(__file__), 'followers_and_following')

class UserInfo(BaseModel):
    username: str
    href: str
    timestamp: Optional[int] = None
    formatted_date: Optional[str] = None

def formatar_timestamp(timestamp: int) -> str:
    try:
        return datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S')
    except:
        return "Data inválida"

def extrair_dados_usuario(item: Dict) -> UserInfo:
    string_data = item.get("string_list_data", [{}])[0]
    timestamp = string_data.get("timestamp")
    return UserInfo(
        username=string_data.get("value", ""),
        href=string_data.get("href", ""),
        timestamp=timestamp,
        formatted_date=formatar_timestamp(timestamp) if timestamp else None
    )

def ler_arquivo_json(nome_arquivo: str) -> Dict[str, Any]:
    caminho = os.path.join(PASTA_JSON, nome_arquivo)
    if not os.path.isfile(caminho):
        raise HTTPException(status_code=404, detail=f'Arquivo {nome_arquivo} não encontrado')
    try:
        with open(caminho, encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail=f'Erro ao ler o arquivo {nome_arquivo}')

def processar_dados_usuarios(dados: Any, chave_relacionamento: Optional[str] = None) -> List[UserInfo]:
    usuarios = []
    if isinstance(dados, dict) and chave_relacionamento and chave_relacionamento in dados:
        lista_dados = dados[chave_relacionamento]
    elif isinstance(dados, list):
        lista_dados = dados
    else:
        return usuarios
    
    for item in lista_dados:
        try:
            usuario = extrair_dados_usuario(item)
            usuarios.append(usuario)
        except:
            continue
    return usuarios

def criar_arquivo_nao_seguem_de_volta():
    try:
        dados_following = ler_arquivo_json("following.json")
        dados_followers = ler_arquivo_json("followers_1.json")
        
        seguindo = processar_dados_usuarios(dados_following, "relationships_following")
        seguidores = processar_dados_usuarios(dados_followers)
        
        usernames_seguidores = {u.username for u in seguidores}
        nao_seguem_de_volta = [u for u in seguindo if u.username not in usernames_seguidores]
        
        json_data = []
        for user in nao_seguem_de_volta:
            json_data.append({
                "title": "",
                "media_list_data": [],
                "string_list_data": [{
                    "href": user.href,
                    "value": user.username,
                    "timestamp": user.timestamp or int(datetime.now().timestamp())
                }]
            })
        
        caminho_arquivo = os.path.join(PASTA_JSON, 'nao_me_seguem_de_volta.json')
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        return len(json_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Erro ao criar arquivo: {str(e)}')

@app.get('/arquivo/{arquivo}', response_model=List[UserInfo])
def ler_arquivo_instagram(
    arquivo: Literal[
        "amigos_proximos",
        "seguidores", 
        "pessoas_que_sigo",
        "solicitacoes_recebidas",
        "ocultar_story_de",
        "solicitacoes_pendentes",
        "desseguidos_recentemente", 
        "solicitacoes_recentes",
        "sugestoes_removidas",
        "nao_me_seguem_de_volta"
    ] = Path(..., description='Selecione o tipo de dados que deseja ver'),
):
    mapeamento_arquivos = {
        'amigos_proximos': 'close_friends.json',
        'seguidores': 'followers_1.json',
        'pessoas_que_sigo': 'following.json',
        'solicitacoes_recebidas': 'follow_requests_you\'ve_received.json',
        'ocultar_story_de': 'hide_story_from.json',
        'solicitacoes_pendentes': 'pending_follow_requests.json',
        'desseguidos_recentemente': 'recently_unfollowed_profiles.json',
        'solicitacoes_recentes': 'recent_follow_requests.json',
        'sugestoes_removidas': 'removed_suggestions.json',
        'nao_me_seguem_de_volta': 'nao_me_seguem_de_volta.json'
    }
    
    nome_arquivo_real = mapeamento_arquivos.get(arquivo)
    
    if arquivo == "nao_me_seguem_de_volta":
        total_criados = criar_arquivo_nao_seguem_de_volta()
        print(f"Arquivo criado com {total_criados} pessoas que não te seguem de volta")
    
    dados = ler_arquivo_json(nome_arquivo_real)
    
    mapeamento_chaves = {
        'following.json': 'relationships_following',
        'close_friends.json': 'relationships_close_friends', 
        'pending_follow_requests.json': 'relationships_follow_requests_sent',
        'recently_unfollowed_profiles.json': 'relationships_unfollowed_users',
        'hide_story_from.json': 'relationships_hide_stories_from',
        'removed_suggestions.json': 'relationships_dismissed_suggested_users',
        'recent_follow_requests.json': 'relationships_follow_requests_sent'
    }
    
    chave = mapeamento_chaves.get(nome_arquivo_real)
    usuarios = processar_dados_usuarios(dados, chave)

    for user in usuarios:
        user.timestamp = None
        user.formatted_date = None
    
    return usuarios

@app.get("/", summary="Página inicial")
def home():
    return {
        "digite /docs no final da URL"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=5000,
        reload=True,
        workers=1
    )
