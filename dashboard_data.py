# Forced update for GitHub sync
import pandas as pd
import numpy as np
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# --- Constantes de Domínio e Configuração ---

NOME_ABA_PLANILHA = 'Página1'

# Nomes de Colunas (Origem)
COL_DATA = 'Data'
COL_LOCAL = 'Local'
COL_FUNDAMENTOS = 'Fundamentos'
COL_QTD_CORRETA = 'Quantidade correta'
COL_QTD_ERRADA = 'Quantidade errada'
COL_QTD_TOTAL = 'Quantidade total'

# Nomes de Colunas (Destino/Calculadas)
COL_CATEGORIA = 'Categoria'
COL_TOTAL_CALCULADO = 'Total Calculado'
COL_EFICIENCIA = 'Eficiencia'

# Strings de Regra de Negócio
PREFIXO_ATAQUE = 'Ataque'
TEXTO_LEVANTAMENTO = 'Levantamento'
TEXTO_RECEPCAO = 'Recepção'
TEXTO_SAQUE = 'Saque'
CATEGORIA_OUTROS = 'Outros'

# Casos Especiais (Regras de Negócio)
CASO_LEVANTAMENTO_BOM = 'Levantamento - Bom (não considere manchete)'
CASOS_LEVANTAMENTO_ERRO_FATAL = [
    'Levantamento - Bola não permite ataque (Erro)', 
    'Levantamento - Dois toque (Erro)', 
    'Levantamento - Condução (Erro)'
]

# --- Funções de ETL (Extract, Transform, Load) ---

def obter_conexao_e_dados_brutos() -> pd.DataFrame:
    """
    Estabelece conexão com o Google Sheets e lê os dados brutos.
    
    Returns:
        pd.DataFrame: DataFrame contendo os dados crus da planilha.
    
    Raises:
        Exception: Se houver falha na conexão ou leitura.
    """
    try:
        conexao = st.connection("gsheets", type=GSheetsConnection)
        dados_brutos = conexao.read(worksheet=NOME_ABA_PLANILHA, header=1)
        return dados_brutos
    except Exception as erro:
        raise Exception(f"Falha crítica ao acessar planilha Google Sheets: {erro}")

def limpar_e_padronizar_dados(dados: pd.DataFrame) -> pd.DataFrame:
    """
    Realiza a limpeza inicial, tipagem e padronização de colunas.
    
    Args:
        dados (pd.DataFrame): Dados brutos.
        
    Returns:
        pd.DataFrame: Dados limpos e tipados.
    """
    if dados.empty:
        return dados

    # Remove espaços em branco do nome das colunas
    dados.columns = dados.columns.str.strip()
    
    # Remove linhas inválidas (sem dados nos campos chave)
    # Adicionado .copy() para evitar SettingWithCopyWarning
    dados = dados.dropna(subset=[COL_DATA, COL_FUNDAMENTOS]).copy()
    
    # Conversão de Data (DD/MM/AAAA)
    dados[COL_DATA] = pd.to_datetime(dados[COL_DATA], dayfirst=True, errors='coerce')
    
    # Conversão de Colunas Numéricas
    colunas_para_converter = [COL_QTD_CORRETA, COL_QTD_ERRADA, COL_QTD_TOTAL]
    for coluna in colunas_para_converter:
        dados[coluna] = pd.to_numeric(dados[coluna], errors='coerce').fillna(0)
        
    return dados

def identificar_categoria(texto_fundamento: str) -> str:
    """
    Categoriza o fundamento baseado em seu texto descritivo.
    
    Args:
        texto_fundamento (str): Descrição do fundamento (ex: 'Ataque - Diagonal').
        
    Returns:
        str: Categoria macro (Ataque, Saque, etc.).
    """
    texto = str(texto_fundamento).strip()
    
    if texto.startswith(PREFIXO_ATAQUE):
        return PREFIXO_ATAQUE
    if TEXTO_LEVANTAMENTO in texto:
        return TEXTO_LEVANTAMENTO
    if TEXTO_RECEPCAO in texto:
        return TEXTO_RECEPCAO
    if TEXTO_SAQUE in texto:
        return TEXTO_SAQUE
        
    return CATEGORIA_OUTROS

def aplicar_regras_negocio_volei(dados: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica regras de negócio específicas para corrigir inconsistências na entrada de dados.
    
    Args:
        dados (pd.DataFrame): DataFrame pré-processado.
        
    Returns:
        pd.DataFrame: DataFrame com correções lógicas aplicadas.
    """
    # Regra 1: Levantamento 'Bom' implica 100% de acerto (copia Total para Correta)
    filtro_lev_bom = dados[COL_FUNDAMENTOS] == CASO_LEVANTAMENTO_BOM
    dados.loc[filtro_lev_bom, COL_QTD_CORRETA] = dados.loc[filtro_lev_bom, COL_QTD_TOTAL]
    dados.loc[filtro_lev_bom, COL_QTD_ERRADA] = 0

    # Regra 2: Erros fatais de levantamento implicam 100% de erro
    filtro_lev_erro = dados[COL_FUNDAMENTOS].isin(CASOS_LEVANTAMENTO_ERRO_FATAL)
    dados.loc[filtro_lev_erro, COL_QTD_CORRETA] = 0
    dados.loc[filtro_lev_erro, COL_QTD_ERRADA] = dados.loc[filtro_lev_erro, COL_QTD_TOTAL]

    # Regra 3: Remover linhas totalizadoras para evitar contagem duplicada
    # (O usuário informou que 'Levantamento' e 'Ataque' já são a soma das subcategorias)
    fundamentos_para_remover = [TEXTO_LEVANTAMENTO, PREFIXO_ATAQUE]
    # Filtra onde o Fundamento NÃO É exatamente igual aos termos totalizadores
    dados = dados[~dados[COL_FUNDAMENTOS].isin(fundamentos_para_remover)].copy()


    return dados

def calcular_metricas_performance(dados: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula KPIs e métricas derivadas para análise.
    
    Args:
        dados (pd.DataFrame): Dados limpos e corrigidos.
        
    Returns:
        pd.DataFrame: Dados enriquecidos com eficiência e categorias.
    """
    # Categorização
    dados[COL_CATEGORIA] = dados[COL_FUNDAMENTOS].apply(identificar_categoria)

    # Cálculo do Volume Total Real (Pós-regras)
    dados[COL_TOTAL_CALCULADO] = dados[COL_QTD_CORRETA] + dados[COL_QTD_ERRADA]
    
    # Cálculo de Eficiência (0.00 a 1.00)
    # Evita divisão por zero retornando 0
    dados[COL_EFICIENCIA] = dados.apply(
        lambda linha: linha[COL_QTD_CORRETA] / linha[COL_TOTAL_CALCULADO] 
                      if linha[COL_TOTAL_CALCULADO] > 0 else 0.0, 
        axis=1
    )
    
    return dados

def carregar_dados_processados() -> pd.DataFrame:
    """
    Fachada (Facade) principal para o pipeline de dados.
    Executa: Extração -> Limpeza -> Regras de Negócio -> Enriquecimento.
    
    Returns:
        pd.DataFrame: DataFrame final pronto para consumo do Dashboard.
    """
    try:
        dados = obter_conexao_e_dados_brutos()
        dados = limpar_e_padronizar_dados(dados)
        dados = aplicar_regras_negocio_volei(dados)
        dados = calcular_metricas_performance(dados)
        return dados
    except Exception as erro:
        st.error(f"Erro durante o processamento de dados: {erro}")
        return pd.DataFrame()
