# agent_brain.py - LançAI: Agente de Query e Validação Contábil (CORRIGIDO PARA COTA)

import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

# Carrega a chave da API
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") 

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY não encontrada. Verifique seu arquivo .env.")

# Inicialização do LLM
# CORREÇÃO: gemini-2.5-pro alterado para gemini-2.5-flash. Maior cota e velocidade.
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)

# --- SISTEMA DE PROMPT DO AGENTE LançAI (MAIS FLEXÍVEL) ---
SYSTEM_PROMPT_LANCAI = """
Você é o Agente de Análise Contábil LançAI, especializado em Contabilidade e Fiscal para a Indústria Metalúrgica.
Sua tarefa é analisar o DataFrame (df) de lançamentos contábeis.

INSTRUÇÕES:
1. **SEMPRE** comece sua resposta com um resumo conciso do que foi realizado ou analisado.
2. **PRIORIDADE 1 (Validação de Mapeamento):** Se a tarefa for a "análise inicial", sua prioridade é verificar a coluna 'Conta_Debito' ou 'Conta_Credito' por valores como 'Regra Não Mapeada'.
    * Se encontrar, liste as chaves de NF-e e CFOPs não mapeados e sugira a inclusão da regra.
3. **PRIORIDADE 2 (Perguntas Humanas):** Se a tarefa for uma pergunta específica (ex: 'valor total', 'nova tributação'), use sua capacidade de raciocínio sobre o DataFrame para responder.
    * Para **perguntas quantitativas** (Ex: 'valor total'), **utilize os dados do DataFrame para calcular a resposta**. Use a coluna 'Valor_Lancamento'.
    * Para **perguntas de compliance** (Ex: 'nova tributação'), use seu conhecimento fiscal e o contexto dos lançamentos para fornecer uma análise informada e um aviso de que a validação final é responsabilidade do Contador.

O DataFrame a ser analisado está no formato Markdown a seguir. Sua resposta deve ser baseada nos dados e no prompt:
"""

def generate_accounting_summary_and_answer(df_lancamentos: pd.DataFrame, user_question: str) -> str:
    """Invoca o LLM para analisar o DataFrame de lançamentos e responder à pergunta do usuário."""
    
    if df_lancamentos is None or df_lancamentos.empty:
        return "Não há dados de lançamentos contábeis para analisar."
    
    # 1. Converte o DF para Markdown para enviar ao LLM
    df_markdown = df_lancamentos.to_markdown(index=False)

    # 2. Cria o prompt combinando o sistema, o DF e a pergunta do usuário
    full_prompt = (
        SYSTEM_PROMPT_LANCAI + 
        f"\n\n--- INÍCIO DO DATAFRAME ---\n{df_markdown}\n--- FIM DO DATAFRAME ---\n\n" +
        f"PERGUNTA/TAREFA DO USUÁRIO: {user_question}"
    )
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("human", full_prompt)
    ])
    
    try:
        chain = prompt_template | llm
        response = chain.invoke({})
        return response.content

    except Exception as e:
        # Melhor feedback para o erro de cota
        if "ResourceExhausted" in str(e):
             return "Erro ao gerar a análise contábil pelo Agente LançAI. Detalhes: **Cota de API Excedida (ResourceExhausted)**. Verifique seu plano e os limites de uso no Google AI Studio."
        return f"Erro ao gerar a análise contábil pelo Agente LançAI. Detalhes: {type(e).__name__}. Verifique a API Key."