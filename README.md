# 🧠 LançAI: Agente Autônomo de Automação Contábil-Fiscal (MVP)

## Visão Geral do Projeto

O **LançAI** é um Agente Autônomo desenvolvido para otimizar o processo de geração de lançamentos contábeis em grandes indústrias, com foco inicial no setor metalúrgico. 

Este MVP (Produto Mínimo Viável) automatiza a leitura e o parsing de documentos fiscais (XML de NF-e/CT-e) contidos em um arquivo ZIP, aplica regras de mapeamento (CFOP -> Débito/Crédito) e utiliza a IA do Gemini (via LangChain) para validar os resultados e identificar lançamentos não mapeados, gerando um resumo gerencial para o contador.

### Público Alvo
Contadores e Analistas Contábeis e Fiscais da indústria metalúrgica.

## Estrutura do Projeto

| Arquivo/Pasta | Finalidade |
| :--- | :--- |
| `main.py` | Interface principal em Streamlit (UI/UX). Coordena o fluxo e aplica a paleta cromática LançAI. |
| `data_handler.py` | Módulo de **Dados e Regras**. Responsável pela descompactação do ZIP, parsing dos XMLs, e aplicação das regras de mapeamento contábil (CFOP). |
| `agent_brain.py` | Módulo do **Cérebro do Agente**. Utiliza o Gemini para analisar o DataFrame final, buscando inconsistências (Regras Não Mapeadas) e gerando o resumo contábil. |
| `logo_lancai.jpg` | Logotipo do projeto (Identidade Visual). |
| `requirements.txt` | Lista de dependências Python. |
| `.env` | Variáveis de ambiente, contendo a chave de API (crucial para o agente). |
| `temp_xmls/` | **Pasta de trabalho temporária.** Criada pelo `data_handler` para salvar os XMLs extraídos antes do processamento. |

## 🚀 Como Executar o LançAI (MVP)

Siga os passos abaixo para colocar o Agente LançAI em funcionamento.

### 1. Pré-requisitos

* Python 3.9+ instalado.
* Chave de API do Google Gemini (Google AI Studio ou Google Cloud).

### 2. Configuração do Ambiente

1.  **Crie o ambiente virtual (Recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows use: .\venv\Scripts\activate
    ```

2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure a Chave de API:**
    * Crie um arquivo chamado **`.env`** na pasta raiz do projeto.
    * Adicione sua chave de API nele:
        ```env
        GOOGLE_API_KEY="SUA_CHAVE_AQUI"
        # Ou (recomendado pelo LangChain)
        GEMINI_API_KEY="SUA_CHAVE_AQUI" 
        ```

### 3. Execução

1.  **Execute o aplicativo Streamlit:**
    ```bash
    streamlit run main.py
    ```
2.  O aplicativo será aberto no seu navegador padrão.
3.  **Fluxo de Uso:**
    * Carregue um arquivo ZIP contendo XMLs de NF-e/CT-e.
    * Clique em "2. Iniciar Geração de Lançamentos".
    * O agente processará os XMLs, aplicará as regras e gerará a análise final do Gemini.
    * Exporte os lançamentos prontos em CSV.

---

## 🎨 Paleta Cromática LançAI

O projeto segue a paleta definida para a indústria metalúrgica, focando na usabilidade e hierarquia de dados:

| Função | Cor | HEX |
| :--- | :--- | :--- |
| **Primária** (Botões) | Terracota Metálico | `#C05533` |
| **Secundária** (Texto, Elementos) | Prata Holográfico | `#8FA3BF` |
| **Fundo Escuro** (Header) | Grafite Industrial | `#1E2835` |
| **Fundo Claro** (App Background) | Aço Brilhante | `#F0F4F9` |
| **Erro** (Não Mapeado) | Ferro Oxidado | `#B34A4A` |
| **Informação** (Alertas) | Cobalto | `#4A7DA8` |

## 📄 Licença

MIT License

Copyright (c) 2025 Ramon Rabello (em nome do Grupo_284 do Curso I2A2 - Agentes Autônomos)

A permissão é concedida, gratuitamente, a qualquer pessoa que obtenha uma cópia deste software e dos arquivos de documentação associados (o "Software"), para lidar com o Software sem restrições, incluindo, sem limitação, os direitos de usar, copiar, modificar, mesclar, publicar, distribuir, sublicenciar e/ou vender cópias do Software, e permitir que pessoas a quem o Software é fornecido o façam, sujeito às seguintes condições:

O aviso de copyright acima e este aviso de permissão deverão ser incluídos em todas as cópias ou partes substanciais do Software.

O SOFTWARE É FORNECIDO "NO ESTADO EM QUE SE ENCONTRA", SEM GARANTIA DE QUALQUER TIPO, EXPRESSA OU IMPLÍCITA, INCLUINDO, MAS NÃO SE LIMITANDO ÀS GARANTIAS DE COMERCIALIZAÇÃO, ADEQUAÇÃO A UM DETERMINADO FIM E NÃO VIOLAÇÃO. EM NENHUMA HIPÓTESE OS AUTORES OU DETENTORES DOS DIREITOS AUTORAIS SERÃO RESPONSÁVEIS POR QUALQUER REIVINDICAÇÃO, DANO OU OUTRA RESPONSABILIDADE, SEJA EM UMA AÇÃO DE CONTRATO, DELITO OU DE OUTRA FORMA, DECORRENTE DE, OU EM CONEXÃO COM O SOFTWARE OU O USO OU OUTRAS NEGOCIAÇÕES NO SOFTWARE.
