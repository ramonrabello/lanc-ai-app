import streamlit as st
import pandas as pd
import os
import zipfile
from dotenv import load_dotenv

# Importa a nova função de agente
from agent_brain import generate_accounting_summary_and_answer 
from data_handler import (
    load_and_validate_csv, 
    unpack_data_zip,        
    unpack_xml_zip_lancai,  
    process_xml_files,
    TEMP_FOLDER
) 


# --- 1. CONFIGURAÇÃO INICIAL E PALETA CROMÁTICA ---
load_dotenv()

# Paleta Cromática (Hex) do Projeto LançAI
PRIMARY_COLOR = "#C05533"  # Terracota Metálico
BG_DARK = "#1E2835"        # Grafite Industrial
SECONDARY_COLOR = "#8FA3BF" # Prata Holográfico
SUCCESS_COLOR = "#4D9E6D"   # Verde Minério
ERROR_COLOR = "#B34A4A"     # Ferro Oxidado
INFO_COLOR = "#4A7DA8"      # Cobalto

st.set_page_config(
    layout="wide", 
    page_title="LançAI: Agente de Análise e Query",
    initial_sidebar_state="expanded" 
)

# Aplicação da Paleta Cromática via CSS (Corrigido para exportação)
st.markdown(f"""
    <style>
    /* Definição Geral: Fundo Claro (#F0F4F9), Texto Escuro */
    .stApp, .stApp > header, div.block-container {{ 
        background-color: #F0F4F9; 
        color: {BG_DARK}; /* FORÇA O TEXTO PADRÃO A SER ESCURO */
    }}
    /* Estilo dos Botões de Ação Principal */
    div.stButton > button {{ background-color: {PRIMARY_COLOR}; color: white; border: none; padding: 10px 24px; border-radius: 8px; }}
    div.stButton > button:hover {{ background-color: #A84628; }}
    
    /* CORREÇÃO PARA EXPORTAÇÃO: Fundo escuro, texto escuro */
    div.stDownloadButton > button {{ 
        background-color: #465A6F; 
        color: {BG_DARK} !important; /* Texto do botão de exportação é agora PRETO */
        border: 1px solid {BG_DARK};
    }}
    
    /* CORREÇÃO CRÍTICA: Cor do texto dentro de TODOS os alertas (quadros) */
    .stAlert,
    .stAlert.stAlert-info,
    .stAlert.stAlert-success, 
    .stAlert.stAlert-warning, 
    .stAlert.stAlert-error {{ 
        color: {BG_DARK} !important; /* Força o texto dos quadros a ser escuro */
    }}
    /* Destaque para Regra Não Mapeada na Tabela */
    .stDataFrame table tr td:nth-child(4):contains("Regra Não Mapeada"),
    .stDataFrame table tr td:nth-child(5):contains("Regra Não Mapeada") {{
        background-color: {ERROR_COLOR} !important;
        color: white !important; 
    }}
    </style>
""", unsafe_allow_html=True)


# --- LÓGICA DA SESSÃO ---
def initialize_session_state():
    """Inicializa as variáveis de estado da sessão."""
    if 'df_data_analysis' not in st.session_state:
        st.session_state['df_data_analysis'] = None
    if 'df_lancamentos' not in st.session_state:
        st.session_state['df_lancamentos'] = None # DF principal para o Agente
    if 'mode' not in st.session_state:
        st.session_state['mode'] = 'none' 
    if 'initial_summary' not in st.session_state:
        st.session_state['initial_summary'] = None # Armazena o resumo da primeira chamada
    
    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(TEMP_FOLDER)

initialize_session_state()

# --- FUNÇÃO UNIFICADA PARA O QUADRO DE PERGUNTAS ---
def render_agent_query_interface(df: pd.DataFrame, is_fiscal_mode: bool = False):
    """Renderiza a interface de perguntas e respostas para o Agente LançAI."""
    
    st.markdown("---")
    st.subheader("2. Perguntas ao Agente LançAI (Análise Detalhada)")

    user_question = st.text_input(
        "Digite sua pergunta sobre os dados/lançamentos (Ex: 'Qual o valor total?', 'Quais as contas não mapeadas?')"
    )
    
    button_label = "Perguntar ao Agente"
    if not is_fiscal_mode:
        # Modo análise de dados genéricos
        button_label = "Perguntar ao Agente (Dados)"

    if st.button(button_label):
        if user_question:
            with st.spinner(f"💬 O Agente está processando sua pergunta: '{user_question}'..."):
                
                # Prepara a tarefa para o cérebro do agente
                task = user_question
                if not is_fiscal_mode:
                    # Se não for modo fiscal, passamos uma tarefa mais genérica
                    task = f"Analise o DataFrame e responda a esta pergunta: {user_question}"
                
                response_text = generate_accounting_summary_and_answer(df, task)
                
                st.markdown("#### 💬 Resposta do Agente:")
                st.success(response_text)
        else:
            st.warning("Por favor, digite sua pergunta antes de clicar no botão de envio.")


# --- PROCESSAMENTO DE UPLOAD HÍBRIDO (COM CORREÇÃO DE FLUXO) ---
def process_uploaded_file(uploaded_file):
    """Lida com arquivos CSV/XLSX diretos ou ZIPs contendo CSVs/XMLs."""
    
    # Limpa o estado e arquivos temp para começar um NOVO upload
    clear_session_state() 
    
    # Limpa arquivos da pasta temp, ignorando erros de permissão
    for f in os.listdir(TEMP_FOLDER):
        try:
            os.remove(os.path.join(TEMP_FOLDER, f))
        except Exception:
            pass # Ignora o erro se o arquivo estiver em uso

    file_name = uploaded_file.name.lower()
    
    # CENÁRIO 1: CSV/XLSX Direto (MODO VISUALIZAÇÃO)
    if file_name.endswith(('.csv', '.xlsx')): 
        st.info("Arquivo de dados detectado. Carregando para visualização simples...")
        
        filepath = os.path.join(TEMP_FOLDER, uploaded_file.name)
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        df = load_and_validate_csv(filepath)
        if df is not None:
             st.session_state['mode'] = 'data_analysis' 
             st.session_state['df_data_analysis'] = df 
             st.success("Visualização de dados ativada.")
             st.rerun() # <-- REINTRODUZIDO
             return 

    # CENÁRIO 2: ZIP (Tenta LançAI Contábil primeiro, depois Visualização)
    elif file_name.endswith('.zip'):
        
        # Tenta 2A: MODO LANÇAI CONTÁBIL (XML)
        if unpack_xml_zip_lancai(uploaded_file):
            st.info("XMLs extraídos. Processando lançamentos contábeis...")
            df_lancamentos = process_xml_files()
            if df_lancamentos is not None:
                st.session_state['mode'] = 'lancai'
                st.session_state['df_lancamentos'] = df_lancamentos
                st.success("Módulo LançAI Contábil-Fiscal ativado. Resultados prontos para análise.")
                st.rerun() # <-- REINTRODUZIDO
                return 
            else:
                # O process_xml_files já limpa os XMLs extraídos
                st.warning("XMLs encontrados, mas o Agente LançAI não conseguiu gerar lançamentos válidos. Tentando modo Visualização de Dados...")

        # Tenta 2B: MODO VISUALIZAÇÃO DE DADOS (CSV/XLSX DENTRO DO ZIP)
        st.warning("Tentando extrair CSV/XLSX para visualização...")
        data_filepath = unpack_data_zip(uploaded_file) 
        
        if data_filepath:
            df = load_and_validate_csv(data_filepath)
            # O unpack_data_zip já removeu o ZIP, mas o load_and_validate_csv usa o arquivo extraído (CSV/XLSX)
            
            if df is not None:
                st.session_state['mode'] = 'data_analysis' 
                st.session_state['df_data_analysis'] = df 
                st.success("Visualização de dados ativada. Dados carregados do ZIP.")
                
                # Devemos remover o arquivo extraído CSV/XLSX antes do rerun
                try:
                    os.remove(data_filepath)
                except Exception:
                    pass
                
                st.rerun() # <-- REINTRODUZIDO
                return

        # FALHA EXPLÍCITA NO ZIP: Se chegou aqui, nada funcionou.
        st.session_state['mode'] = 'none'
        st.error("Falha ao processar o arquivo ZIP. Ele não continha XMLs de NF-e válidas para o LançAI nem arquivos CSV/XLSX para visualização de dados.")
        return

    # CENÁRIO 3: NENHUM ARQUIVO VÁLIDO ENCONTRADO
    st.session_state['mode'] = 'none'
    st.warning("Nenhum modo de processamento foi ativado. Por favor, carregue um arquivo válido.")

def clear_session_state():
    st.session_state['df_data_analysis'] = None
    st.session_state['df_lancamentos'] = None
    st.session_state['mode'] = 'none'
    st.session_state['initial_summary'] = None


# --- HEADER E IDENTIDADE VISUAL ---
col_logo, col_title = st.columns([1, 4])

with col_logo:
    LOGO_PATH = "logo_lancai.png" 
    if os.path.exists("logo_lancai.jpg"):
        st.image("logo_lancai.jpg", width=500)
    elif os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=500) 
    else:
        st.markdown(f"<h1 style='color: {PRIMARY_COLOR};'>LançAI</h1>", unsafe_allow_html=True)

with col_title:
    st.markdown(f"""
        <h1 style='color: {BG_DARK};'>LançAI: Agente de Análise e Query</h1>
        <p style='color: {SECONDARY_COLOR}; font-size: 18px;'>Automação Contábil e Análise de Dados Híbrida.</p>
    """, unsafe_allow_html=True)

st.markdown("---")

def on_upload_change():
    """Função de callback chamada quando o arquivo é carregado."""
    # O objeto do arquivo carregado é acessado via key
    uploaded_file = st.session_state.uploader_key
    
    if uploaded_file is not None:
        # 1. Processa o arquivo (isso chamará st.rerun() se bem-sucedido)
        process_uploaded_file(uploaded_file)
        
        # 2. CRÍTICO: Limpa o estado do uploader para que o próximo rerun não chame process_uploaded_file novamente
        st.session_state.uploader_key = None

# --- SIDEBAR (UPLOAD) ---
with st.sidebar:
    st.header("Upload de Dados LançAI")
    
    # Substituímos o if uploaded_file: pela lógica de callback.
    # O arquivo é salvo em st.session_state.uploader_key
    st.file_uploader(
        "Carregue seu arquivo CSV, Excel ou ZIP (XML/CSV)",
        type=["csv", "zip", "xlsx"],
        key='uploader_key',                  # A chave salva o arquivo no session_state
        on_change=on_upload_change,          # Chama a função acima quando o arquivo muda
        label_visibility="visible"
    )

# ==============================================================================
# 3. EXIBIÇÃO DA INTERFACE E INVOCACÃO DO AGENTE
# ==============================================================================

if st.session_state.get('mode') == 'lancai':
    # --- MODO LANÇAI CONTÁBIL (XML) ---
    df = st.session_state.df_lancamentos
    
    st.subheader("1. Lançamentos Gerados e Análise Inicial")
    
    # 3.1. Chamada Inicial do Agente (Auditoria e Resumo)
    if st.session_state.get('initial_summary') is None:
        
        with st.spinner(f"🧠 O Agente LançAI está auditando {len(df)} lançamentos e gerando o resumo inicial..."):
            initial_task = "Faça a análise inicial do DataFrame. Forneça o resumo e a auditoria de mapeamentos (Regra Não Mapeada)."
            summary_text = generate_accounting_summary_and_answer(df, initial_task)
            st.session_state['initial_summary'] = summary_text
            
            # ESTE RERUN É VITAL para que o spinner desapareça e o resumo seja exibido
            st.rerun()

    # Exibir o resumo inicial após a primeira chamada
    if st.session_state.get('initial_summary'):
        st.markdown("#### 🧠 Análise e Validação Inicial do Agente LançAI:")
        st.info(st.session_state.initial_summary)

    # 3.2. Interface de Perguntas e Respostas
    render_agent_query_interface(df, is_fiscal_mode=True)

    # 3.3. Prévia e Exportação
    with st.expander("📝 Lançamentos Contábeis Gerados (Prévia)"):
        st.dataframe(df, use_container_width=True)
        nao_mapeados = len(df[df['Conta_Debito'] == 'Regra Não Mapeada'])
        st.markdown(f"**Total de Lançamentos Não Mapeados:** {nao_mapeados}")

    st.markdown("---")
    st.markdown("#### ⬇️ 3. Geração de Saída (Exportação)")
    csv_export = df[['NFe_Chave', 'Emissor', 'CFOP_Principal', 'Conta_Debito', 'Conta_Credito', 'Valor_Lancamento']].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Exportar Lançamentos (CSV) - Formato de Integração",
        data=csv_export,
        file_name='lancamentos_lancai_prontos.csv',
        mime='text/csv',
        type="secondary"
    )
    st.success("✅ Processamento Contábil Concluído e Agente pronto para perguntas.")


elif st.session_state.get('mode') == 'data_analysis':
    # --- MODO VISUALIZAÇÃO DE DADOS (CSV/XLSX) ---
    df = st.session_state.df_data_analysis
    
    st.subheader("1. Visualização de Dados (CSV/XLSX)")
    st.info("O arquivo foi carregado com sucesso. Abaixo está uma prévia do DataFrame. O Agente de Query está disponível para análise de dados.")
    
    if df is not None:
        st.dataframe(df, use_container_width=True)
        
        # INCLUSÃO: Exibe as dimensões e as colunas (atendendo ao requisito)
        st.markdown(f"**Dimensões do DataFrame:** {len(df)} linhas e {len(df.columns)} colunas.")
        
        with st.expander("▶️ Ver Colunas e Tipos de Dados"):
            # Exibe as colunas e os tipos de dados
            info = pd.DataFrame({
                'Coluna': df.columns,
                'Tipo de Dado': df.dtypes.astype(str)
            })
            st.dataframe(info, use_container_width=True, hide_index=True)

        # 2. Interface de Perguntas e Respostas
        render_agent_query_interface(df, is_fiscal_mode=False)
        
    st.markdown("---")
    st.markdown("#### ⬇️ 3. Exportação")
    csv_export = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Exportar DataFrame (CSV)",
        data=csv_export,
        file_name='dados_lancai_carregados.csv',
        mime='text/csv',
        type="secondary"
    )


else:
    # --- MODO INICIAL ---
    st.subheader("Instruções de Uso")
    # A cor do texto é forçada para BG_DARK
    st.markdown(f"""
        <p style='color: {BG_DARK}; font-size: 18px;'>
        Por favor, faça o upload de um arquivo na barra lateral para começar a análise:
        </p>
        <ul>
            <li><b>Para Automação Contábil-Fiscal (XML/ZIP):</b> O Agente irá processar, auditar e estará pronto para responder perguntas sobre os lançamentos.</li>
            <li><b>Para Visualização de Dados (CSV/XLSX):</b> Apenas a prévia será exibida.</li>
        </ul>
    """, unsafe_allow_html=True)