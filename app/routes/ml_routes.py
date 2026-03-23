import os
from fastapi import APIRouter, HTTPException
from app import schemas
import google.generativeai as genai
from dotenv import load_dotenv
import json

load_dotenv()

router = APIRouter(prefix="/gene", tags=["GeneAI"])

@router.post("/", response_model=schemas.GeneResponse)
def gerar_resolucao_tecnica(request: schemas.GeneRequest):
    """
    Recebe título e descrição da tarefa, monta o prompt para o Gemini e retorna o JSON gerado pela IA.
    """
    api_key = os.getenv("GEN_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave da API Gemini não configurada.")

    prompt = f'''
Tarefa: {request.titulo}\nDescrição: {request.descricao}\n
1. Reescreva o título e a descrição enviados, sem grandes alterações, apenas corrigindo erros gramaticais e de lógica. Chame-os de "titulo_sugerido" e "descricao_sugerida".
2. Gere DUAS opções de resoluções técnicas para essa tarefa, cada uma destrinchada em tópicos resumidos e diretos, como um passo a passo.
3. Ao final, sugira o nível de complexidade (baixo, médio ou alto).

Retorne a resposta no seguinte formato JSON:\n{{\n  "titulo": "...",\n  "descricao": "...",\n  "titulo_sugerido": "...",\n  "descricao_sugerida": "...",\n  "resolucoes": [\n    "Opção 1: ...",\n    "Opção 2: ..."\n  ],\n  "nivel_complexidade": "baixo|médio|alto"\n}}\n'''

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3-flash-preview")
        response = model.generate_content(prompt)
        resposta_texto = response.text.strip()
        resposta_json = json.loads(resposta_texto)
        return resposta_json
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Resposta da IA não está em formato JSON válido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar Gemini: {str(e)}")
