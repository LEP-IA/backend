import os
from fastapi import APIRouter, HTTPException
from app import schemas
import google.generativeai as genai
from dotenv import load_dotenv
import json
import re
import logging

load_dotenv()

router = APIRouter(prefix="/gene", tags=["GeneAI"])


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/", response_model=schemas.GeneResponse)
def gerar_resolucao_tecnica(request: schemas.GeneRequest):
    """
    Recebe título e descrição da tarefa, monta o prompt e retorna o JSON gerado pela IA.
    """
    api_keys = [
        os.getenv("GEN_API_KEY"),
        os.getenv("GEN_API_KEY_2"),
        os.getenv("GEN_API_KEY_3")
    ]


    api_keys = [key for key in api_keys if key and key.strip()]

    if not api_keys:
        raise HTTPException(status_code=500, detail="Nenhuma chave da API Gemini configurada.")

    prompt = f'''
Tarefa: {request.titulo}\nDescrição: {request.descricao}\n
1. Reescreva o título e a descrição enviados, sem grandes alterações, apenas corrigindo erros gramaticais e de lógica. Chame-os de "titulo_sugerido" e "descricao_sugerida".
2. Gere DUAS opções de resoluções técnicas para essa tarefa, cada uma destrinchada em tópicos resumidos e diretos, como um passo a passo.
3. Ao final, sugira o nível de complexidade (baixo, médio ou alto).

Retorne a resposta no seguinte formato JSON:\n{{\n  "titulo": "...",\n  "descricao": "...",\n  "titulo_sugerido": "...",\n  "descricao_sugerida": "...",\n  "resolucoes": [\n    "Opção 1: ...",\n    "Opção 2: ..."\n  ],\n  "nivel_complexidade": "baixo|médio|alto"\n}}\n'''

    errors = []

    for i, api_key in enumerate(api_keys):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-3-flash-preview")

            generation_config = {
                "temperature": 0.1,
                "max_output_tokens": 2048,
            }

            response = model.generate_content(prompt, generation_config=generation_config)

            if not response or not response.text:
                errors.append(f"Chave {i+1}: Resposta vazia da API")
                continue

            resposta_texto = response.text.strip()

            resposta_texto = resposta_texto.replace("```json", "").replace("```", "").strip()

            match = re.search(r'\{.*\}', resposta_texto, re.DOTALL)
            if match:
                resposta_json_str = match.group(0)
            else:
                resposta_json_str = resposta_texto

            try:
                resposta_json = json.loads(resposta_json_str)
            except json.JSONDecodeError as json_err:
                errors.append(f"Chave {i+1}: JSON inválido - {str(json_err)}")
                continue

            # Validar se o JSON
            required_fields = ["titulo_sugerido", "descricao_sugerida", "resolucoes", "nivel_complexidade"]
            missing_fields = [field for field in required_fields if field not in resposta_json]

            if missing_fields:
                errors.append(f"Chave {i+1}: Campos obrigatórios ausentes: {missing_fields}")
                continue

            return {
                "titulo_original": request.titulo,
                "descricao_original": request.descricao,
                "titulo_sugerido": resposta_json.get("titulo_sugerido", ""),
                "descricao_sugerida": resposta_json.get("descricao_sugerida", ""),
                "resolucoes": resposta_json.get("resolucoes", []),
                "nivel_complexidade": resposta_json.get("nivel_complexidade", "medio")
            }

        except Exception as e:
            error_msg = f"Chave {i+1}: {type(e).__name__}: {str(e)}"
            errors.append(error_msg)
            continue

    # Todas tentativas falharam
    raise HTTPException(
        status_code=503,
        detail="Serviço temporariamente indisponível. Tente novamente em alguns minutos."
    )
