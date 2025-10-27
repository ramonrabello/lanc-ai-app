# data_handler.py - LançAI: Módulo de Dados Híbrido (XML, CSV/XLSX)

import zipfile
import os
import xml.etree.ElementTree as ET
import pandas as pd
import streamlit as st
from typing import Dict, Any, Optional, Any
from io import BytesIO

# --- CONFIGURAÇÃO DE PASTAS ---
TEMP_FOLDER = "./temp_data"
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

# --- REGRAS DO MÓDULO DE MAPEAMENTO (USADO PARA XML) ---
MAPPING_RULES = {
    # CFOPs de Venda
    '5102': {'DEBITO': '1.01.01.002 - Clientes', 'CREDITO': '3.01.01.001 - Receita de Vendas'},
    # CFOPs de Compra para Industrialização
    '1101': {'DEBITO': '1.01.03.002 - Estoque de Matéria-Prima', 'CREDITO': '2.01.01.001 - Fornecedores Nacionais'},
    # ... (demais regras)
}

# --------------------------------------------------------------------------------
# --- LÓGICA DE PROCESSAMENTO CSV/XLSX (VISUALIZAÇÃO DE DADOS) ---
# --------------------------------------------------------------------------------

def load_and_validate_csv(filepath: str) -> Optional[pd.DataFrame]:
    """
    Carrega o DataFrame a partir do caminho do arquivo (CSV ou XLSX), 
    tentando diferentes encodings e delimitadores para resolver problemas de leitura.
    """
    try:
        if filepath.lower().endswith(('.xlsx', '.xls')):
            # Leitura de Excel (normalmente não tem problemas de encoding)
            df = pd.read_excel(filepath)
            
        elif filepath.lower().endswith('.csv'):
            # Tenta diferentes encodings e delimitadores para CSV
            encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1']
            delimiters_to_try = [',', ';']
            df = None
            
            for encoding in encodings_to_try:
                for delimiter in delimiters_to_try:
                    try:
                        # Tenta ler com a combinação atual de encoding e delimiter
                        df = pd.read_csv(filepath, encoding=encoding, sep=delimiter)
                        # Se a leitura for bem-sucedida e o DataFrame não estiver vazio, para o loop
                        if not df.empty:
                            # Heurística de validação: se tiver muitas colunas (indicando delimiter errado), tenta o próximo
                            if len(df.columns) > 1 and len(df.columns) < 50: # Assume um limite razoável de colunas
                                break # Sucesso na leitura
                            elif len(df.columns) == 1 and delimiter == ',':
                                # Se só tem 1 coluna, mas esperava vírgula, tenta ponto e vírgula na próxima
                                continue
                            elif len(df.columns) > 1:
                                break
                    except Exception:
                        continue # Tenta a próxima combinação
                if df is not None and not df.empty and len(df.columns) > 1:
                    break
            
            if df is None or df.empty:
                st.error("Falha ao ler o arquivo CSV. Verifique a codificação (encoding) e o separador (vírgula ou ponto e vírgula).")
                return None
        
        else:
            st.error("Formato de arquivo não suportado para visualização.")
            return None
        
        # Validação final
        if df.empty:
            st.error("O arquivo de dados está vazio. Não foi possível carregar os dados.")
            return None
            
        return df
        
    except Exception as e:
        # Erro genérico de leitura
        st.error(f"Erro ao ler ou processar o arquivo de dados. Detalhes: {type(e).__name__} - {e}")
        return None

def find_first_data_file(zip_ref: zipfile.ZipFile) -> Optional[str]:
    """Encontra o primeiro arquivo de dados (CSV ou XLSX) dentro do ZIP."""
    for name in zip_ref.namelist():
        lower_name = name.lower()
        if lower_name.endswith(('.csv', '.xlsx')):
            return name
    return None

def unpack_data_zip(uploaded_zip_file: Any) -> Optional[str]:
    """Descompacta o primeiro arquivo CSV/XLSX de um ZIP para o Módulo de Visualização."""
    
    zip_path = os.path.join(TEMP_FOLDER, uploaded_zip_file.name)
    
    try:
        # Garante que o buffer do arquivo enviado seja salvo no sistema de arquivos
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip_file.getbuffer())

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            first_data_file = find_first_data_file(zip_ref)
            
            if first_data_file:
                # Extrai apenas o primeiro arquivo de dados encontrado
                zip_ref.extract(first_data_file, TEMP_FOLDER)
                return os.path.join(TEMP_FOLDER, first_data_file)
            else:
                return None
    except zipfile.BadZipFile as e:
        st.error(f"Erro ao descompactar o arquivo ZIP: Arquivo corrompido ou formato inválido. Detalhes: {e}")
        return None
    except Exception as e:
        st.error(f"Erro ao descompactar o arquivo ZIP (para dados): {e}")
        return None
    finally:
        # CORREÇÃO CRÍTICA: Lida com PermissionError (WinError 32)
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except Exception:
                # Ignora a exceção se não conseguir remover imediatamente (arquivo em uso)
                pass


# --------------------------------------------------------------------------------
# --- LÓGICA DE PROCESSAMENTO XML (MÓDULO CONTÁBIL-FISCAL) ---
# --------------------------------------------------------------------------------

def unpack_xml_zip_lancai(uploaded_zip_file: Any) -> bool:
    """Descompacta um arquivo ZIP e salva os XMLs na pasta temporária para o LançAI."""
    zip_path = os.path.join(TEMP_FOLDER, uploaded_zip_file.name)
    try:
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip_file.getbuffer())

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            xml_files = [f for f in zip_ref.namelist() if f.lower().endswith('.xml')]
            
            if not xml_files:
                return False

            zip_ref.extractall(TEMP_FOLDER, members=xml_files)
        
        return True
    except zipfile.BadZipFile as e:
        st.error(f"Erro ao descompactar o arquivo ZIP (XML): Arquivo corrompido ou formato inválido. Detalhes: {e}")
        return False
    except Exception as e:
        st.error(f"Erro ao descompactar o arquivo ZIP (XML): {e}")
        return False
    finally:
        # CORREÇÃO CRÍTICA: Lida com PermissionError (WinError 32)
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except Exception:
                # Ignora a exceção se não conseguir remover imediatamente (arquivo em uso)
                pass


def parse_xml_to_dict(xml_path: str) -> Optional[Dict[str, Any]]:
    """Analisa um XML de NF-e e extrai campos fiscais chave (CFOP, Valor, Emitente)."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        namespace = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        inf_nfe = root.find('.//nfe:infNFe', namespace)
        
        if inf_nfe is None:
            return None

        chave_nfe = inf_nfe.attrib.get('Id', '').replace('NFe', '')
        # Tenta pegar o CFOP do primeiro item (simplificado)
        cfop_elem = root.find('.//nfe:det/nfe:prod/nfe:CFOP', namespace)
        cfop = cfop_elem.text if cfop_elem is not None else "0000"
        
        # Tenta pegar o valor total
        v_total_elem = root.find('.//nfe:ICMSTot/nfe:vNF', namespace)
        valor_total = float(v_total_elem.text) if v_total_elem is not None and v_total_elem.text else 0.0

        x_nome_emit_elem = root.find('.//nfe:emit/nfe:xNome', namespace)
        nome_emitente = x_nome_emit_elem.text if x_nome_emit_elem is not None else 'Emitente Desconhecido'

        return {
            'NFe_Chave': chave_nfe,
            'Emissor': nome_emitente,
            'CFOP_Principal': cfop,
            'Valor_Total': valor_total,
            'XML_Path': os.path.basename(xml_path)
        }
    except Exception:
        # Erro de parsing (XML inválido ou não NF-e esperado)
        return None

def apply_accounting_rules(df_parsed: pd.DataFrame) -> pd.DataFrame:
    """Aplica as regras contábeis (débito/crédito) baseadas no CFOP."""
    df_parsed['Conta_Debito'] = 'Regra Não Mapeada'
    df_parsed['Conta_Credito'] = 'Regra Não Mapeada'
    df_parsed['Valor_Lancamento'] = df_parsed['Valor_Total']

    def map_cfop_to_accounts(row):
        cfop = str(row['CFOP_Principal'])
        rule = MAPPING_RULES.get(cfop)
        
        if rule:
            row['Conta_Debito'] = rule['DEBITO']
            row['Conta_Credito'] = rule['CREDITO']
            
        return row

    return df_parsed.apply(map_cfop_to_accounts, axis=1)

def process_xml_files() -> Optional[pd.DataFrame]:
    """Orquestra a leitura, parsing e aplicação de regras nos XMLs."""
    xml_files = [os.path.join(TEMP_FOLDER, f) for f in os.listdir(TEMP_FOLDER) if f.lower().endswith('.xml')]
    
    if not xml_files:
        return None
        
    parsed_data = []
    
    # 1. Parsing dos XMLs
    parsing_bar = st.progress(0, text="Analisando XMLs...")
    for i, xml_file in enumerate(xml_files):
        data = parse_xml_to_dict(xml_file)
        if data:
            parsed_data.append(data)
        parsing_bar.progress((i + 1) / len(xml_files), text=f"Analisando XMLs: {i+1} de {len(xml_files)}")
    parsing_bar.empty()
    
    if not parsed_data:
        st.error("Nenhum XML válido de nota fiscal foi encontrado ou analisado com sucesso.")
        return None

    df_parsed = pd.DataFrame(parsed_data)
    
    # 2. Aplicação das Regras
    df_lancamentos = apply_accounting_rules(df_parsed.copy())
    
    # 3. Limpeza dos arquivos temporários
    # Adicionando try...except aqui também por segurança na limpeza dos XMLs
    for f in xml_files:
        try:
            os.remove(f)
        except Exception:
            pass
        
    return df_lancamentos