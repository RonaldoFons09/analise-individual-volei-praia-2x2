# Forced update for GitHub sync
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dashboard_data import carregar_dados_processados, COL_TIPO
# Importação das configurações (constantes) evitando "magic strings/numbers" no código
from configuracoes import ESTILOS_CSS, CORES_CATEGORIAS, CRITERIOS_AVALIACAO

# --- Configurações e Estilos ---

def configurar_pagina_inicial():
    """Configurações iniciais de metadados da página."""
    st.set_page_config(
        page_title="Dashboard de Performance - Vôlei",
        page_icon="🏐",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def aplicar_estilos_visuais():
    """Aplica o CSS global importado das configurações."""
    st.markdown(ESTILOS_CSS, unsafe_allow_html=True)

# --- Camada de Dados ---

@st.cache_data(ttl=60)
def obter_dados_com_cache():
    """Wrapper para carregar dados com cache do Streamlit."""
    return carregar_dados_processados()

# --- Camada de Filtros (Barra Lateral) ---

def aplicar_filtros_laterais(dados_completo):
    """
    Controla todos os filtros da sidebar e retorna o subconjunto de dados filtrado.
    """
    st.sidebar.header("Filtros")

    # Botão de reset
    if st.sidebar.button("🔄 Atualizar e Limpar Cache"):
        st.cache_data.clear()
        st.rerun()

    if dados_completo.empty:
        return dados_completo

    # 1. Filtro de Data
    data_minima_disponivel = dados_completo['Data'].min()
    data_maxima_disponivel = dados_completo['Data'].max()
    
    intervalo_selecionado = st.sidebar.date_input(
        "Período de Análise",
        [data_minima_disponivel, data_maxima_disponivel],
        min_value=data_minima_disponivel,
        max_value=data_maxima_disponivel
    )

    # Tratamento para seleção de data única ou intervalo
    if len(intervalo_selecionado) == 2:
        data_inicio, data_fim = intervalo_selecionado
    else:
        data_inicio = intervalo_selecionado[0]
        data_fim = intervalo_selecionado[0]

    mascara_periodo = (dados_completo['Data'] >= pd.to_datetime(data_inicio)) & (dados_completo['Data'] <= pd.to_datetime(data_fim))
    dados_filtrados = dados_completo.loc[mascara_periodo]

    # 1.5 Filtro de Contexto (Tipo) - Novo!
    tipos_disponiveis = sorted(dados_filtrados[COL_TIPO].unique().tolist())
    tipos_selecionados = st.sidebar.multiselect(
        "Contexto do Treino",
        tipos_disponiveis,
        placeholder="Selecione tipos (Ex: Racha, Específico)..."
    )

    if tipos_selecionados:
        dados_filtrados = dados_filtrados[dados_filtrados[COL_TIPO].isin(tipos_selecionados)]

    # 2. Filtro de Local
    locais_disponiveis = sorted(dados_filtrados['Local'].unique().tolist())
    local_escolhido = st.sidebar.selectbox("Local de Treino", ["Todos"] + locais_disponiveis)

    if local_escolhido != "Todos":
        dados_filtrados = dados_filtrados[dados_filtrados['Local'] == local_escolhido]

    st.sidebar.markdown("---")
    st.sidebar.subheader("Seleção de Fundamentos")

    # 3. Filtro de Categoria (Alto Nível)
    categorias_disponiveis = sorted(dados_filtrados['Categoria'].unique().tolist())
    categorias_selecionadas = st.sidebar.multiselect(
        "Categorias",
        categorias_disponiveis,
        placeholder="Selecione para filtrar..."
    )

    if categorias_selecionadas:
        dados_filtrados = dados_filtrados[dados_filtrados['Categoria'].isin(categorias_selecionadas)]

    # 4. Filtro de Detalhe (Baixo Nível)
    detalhes_disponiveis = sorted(dados_filtrados['Fundamentos'].unique().tolist())
    detalhes_selecionados = st.sidebar.multiselect(
        "Tipos Específicos", 
        detalhes_disponiveis,
        placeholder="Ex: Ataque - Diagonal..."
    )

    if detalhes_selecionados:
        dados_filtrados = dados_filtrados[dados_filtrados['Fundamentos'].isin(detalhes_selecionados)]

    return dados_filtrados

# --- Helpers de Visualização ---

def obter_cor_por_eficiencia(valor_eficiencia):
    """Retorna código Hex da cor baseado na eficiência."""
    if valor_eficiencia >= 0.70: return '#2ecc71' # Verde Excelente
    if valor_eficiencia >= 0.50: return '#f1c40f' # Amarelo Atenção
    return '#e74c3c' # Vermelho Crítico

def obter_texto_status(valor_eficiencia):
    """Retorna label de texto baseado na eficiência."""
    if valor_eficiencia >= 0.70: return 'Excelente'
    if valor_eficiencia >= 0.50: return 'Atenção'
    return 'Crítico'

# --- Componentes Visuais ---

def renderizar_kpis_globais(dados):
    """Exibe métricas de topo (KPIs)."""
    coluna_eficiencia, coluna_tentativas, coluna_acertos, coluna_sessoes = st.columns(4)
    
    total_tentativas = dados['Total Calculado'].sum()
    total_acertos = dados['Quantidade correta'].sum()
    
    # Previne divisão por zero
    percentual_eficiencia = (total_acertos / total_tentativas * 100) if total_tentativas > 0 else 0
    total_sessoes_unicas = dados['Data'].nunique()
    
    coluna_eficiencia.metric("Eficiência Geral", f"{percentual_eficiencia:.1f}%")
    coluna_tentativas.metric("Total de Ações", int(total_tentativas))
    coluna_acertos.metric("Acertos Totais", int(total_acertos))
    coluna_sessoes.metric("Sessões de Treino", total_sessoes_unicas)
    
    st.markdown("---")

def renderizar_metricas_por_categoria(dados):
    """Cards detalhados por categoria de fundamento."""
    st.subheader("Desempenho por Categoria")
    
    metricas_agrupadas = dados.groupby('Categoria').agg({
        'Quantidade correta': 'sum',
        'Total Calculado': 'sum'
    }).reset_index()
    
    metricas_agrupadas['Eficiencia'] = metricas_agrupadas['Quantidade correta'] / metricas_agrupadas['Total Calculado']
    
    # Definição de ordem de apresentação
    mapa_prioridade = {'Saque': 1, 'Recepção': 2, 'Levantamento': 3, 'Ataque': 4}
    metricas_agrupadas['Prioridade'] = metricas_agrupadas['Categoria'].map(mapa_prioridade).fillna(99)
    metricas_agrupadas = metricas_agrupadas.sort_values('Prioridade')
    
    container_colunas = st.columns(len(metricas_agrupadas))
    
    for indice, linha in metricas_agrupadas.iterrows():
        eficiencia_atual = linha['Eficiencia']
        cor_indicativa = obter_cor_por_eficiencia(eficiencia_atual)
        status_texto = obter_texto_status(eficiencia_atual)
        nome_categoria = linha['Categoria']
        
        # Busca texto de ajuda na configuração externa
        texto_ajuda = CRITERIOS_AVALIACAO.get(nome_categoria, "Sem critérios definidos.")
        
        # Renderiza em circular nas colunas
        with container_colunas[indice % len(container_colunas)]:
            # Linha colorida superior
            st.markdown(f"<div style='height: 4px; width: 100%; background-color: {cor_indicativa}; border-radius: 4px; margin-bottom: 8px;'></div>", unsafe_allow_html=True)
            
            st.metric(
                label=nome_categoria,
                value=f"{eficiencia_atual:.1%}",
                help=texto_ajuda
            )
            st.caption(f"**{status_texto}** • {int(linha['Total Calculado'])}/{int(linha['Quantidade correta'])} acertos")

    st.markdown("---")

def renderizar_quadrante_ataque(dados):
    """Gráfico de dispersão para análise tática de ataques."""
    st.subheader("Análise Tática de Ataque (Quadrante Mágico)")
    
    # Filtra apenas variações de ataque
    dados_somente_ataque = dados[dados['Fundamentos'].str.startswith('Ataque -')]
    
    if dados_somente_ataque.empty:
        st.info("Não há dados suficientes de ataque para gerar o quadrante.")
        return

    resumo_ataque = dados_somente_ataque.groupby('Fundamentos').agg({
        'Quantidade correta': 'sum',
        'Total Calculado': 'sum'
    }).reset_index()
    
    resumo_ataque['Eficiencia'] = resumo_ataque['Quantidade correta'] / resumo_ataque['Total Calculado']
    
    volume_medio = resumo_ataque['Total Calculado'].mean()
    meta_eficiencia_percentual = 0.60 
    
    grafico_dispersao = px.scatter(
        resumo_ataque,
        x='Total Calculado',
        y='Eficiencia',
        text='Fundamentos',
        size='Total Calculado',
        hover_data=['Quantidade correta'],
        color='Eficiencia',
        color_continuous_scale='RdYlGn',
        title="Relação Volume vs Eficiência"
    )
    
    # Linhas de referência (Quadrantes)
    grafico_dispersao.add_hline(y=meta_eficiencia_percentual, line_dash="dash", line_color="white", annotation_text="Meta")
    grafico_dispersao.add_vline(x=volume_medio, line_dash="dash", line_color="white", annotation_text="Volume Médio")
    
    # Anotações dos quadrantes
    max_x, min_x = resumo_ataque['Total Calculado'].max(), resumo_ataque['Total Calculado'].min()
    
    # Lista de tuplas com configuração das anotações
    config_quadrantes = [
        (max_x, 1.0, "💎 SEGURANÇA", "#2ecc71"),
        (min_x, 1.0, "🚀 POTENCIAL", "#3498db"),
        (max_x, 0.0, "⚠️ RISCO", "#e74c3c"),
        (min_x, 0.0, "🗑️ DESCARTE", "#7f8c8d")
    ]
    
    for pos_x, pos_y, rotulo, cor in config_quadrantes:
        grafico_dispersao.add_annotation(x=pos_x, y=pos_y, text=rotulo, showarrow=False, font=dict(color=cor, size=14))

    grafico_dispersao.update_layout(
        xaxis_title="Volume (Repetições)",
        yaxis_title="Eficiência (%)",
        yaxis_tickformat='.0%',
        height=500
    )
    
    st.plotly_chart(grafico_dispersao, use_container_width=True)

def renderizar_analise_detalhada_levantamento(dados):
    """
    Gráfico de Rosca (Donut) focado na causa dos erros de levantamento.
    Solicitado pelo usuário para identificar problemas técnicos vs táticos.
    """
    st.subheader("Raio-X do Levantamento: Análise de Causas")

    # 1. Filtrar apenas levantamentos
    # O filtro deve pegar tudo que começa com "Levantamento"
    dados_lev = dados[dados['Fundamentos'].str.startswith('Levantamento')].copy()

    if dados_lev.empty:
        st.info("Sem dados de levantamento para análise detalhada.")
        return

    # 2. Identificar Tipos (Sucessos e Erros)
    # Vamos classificar tudo: O que for "Bom" é Acerto, o resto é o nome do erro.
    
    def classificar_tipo(nome_fundamento):
        if "Bom" in nome_fundamento:
            return "✅ Acerto (Bola Boa)"
        else:
            # Limpa o nome do erro: "Levantamento - Dois Toques (Erro)" -> "Dois Toques"
            return nome_fundamento.replace('Levantamento - ', '').replace(' (Erro)', '').capitalize()

    dados_lev['Tipo Detalhado'] = dados_lev['Fundamentos'].apply(classificar_tipo)
    
    # 3. Agrupar por Tipo Detalhado
    resumo_geral = dados_lev.groupby('Tipo Detalhado')['Total Calculado'].sum().reset_index()
    
    total_acoes = resumo_geral['Total Calculado'].sum()
    
    if total_acoes == 0:
        st.warning("Sem dados de levantamento.")
        return

    # 4. Gráfico de Rosca (Donut)
    # Define cores para garantir que Acerto seja verde
    grafico_rosca = px.pie(
        resumo_geral,
        values='Total Calculado',
        names='Tipo Detalhado',
        title=f"Distribuição Total: {int(total_acoes)} Ações",
        hole=0.4,
        color='Tipo Detalhado',
        # Mapa de cores explícito para destacar o acerto e diferenciar erros
        color_discrete_map={
            "✅ Acerto (Bola Boa)": "#2ecc71", # Verde
            "Dois toque": "#e74c3c",           # Vermelho
            "Condução": "#e67e22",             # Laranja
            "Bola não permite ataque": "#f1c40f" # Amarelo
        } 
    )
    
    grafico_rosca.update_traces(textposition='inside', textinfo='percent+label+value')
    grafico_rosca.update_layout(showlegend=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.plotly_chart(grafico_rosca, use_container_width=True)
        
    with col2:
        st.markdown("#### Insights")
        
        # Filtra apenas os erros para dar o insight do vilão
        apenas_erros = resumo_geral[resumo_geral['Tipo Detalhado'] != "✅ Acerto (Bola Boa)"]
        
        if not apenas_erros.empty:
            maior_erro = apenas_erros.loc[apenas_erros['Total Calculado'].idxmax()]
            qtd_erro = maior_erro['Total Calculado']
            pct_erro_relativo = (qtd_erro / apenas_erros['Total Calculado'].sum()) * 100
            
            st.write(f"🛑 **Principal Erro:** {maior_erro['Tipo Detalhado']}")
            st.write(f"Soma **{int(qtd_erro)}** falhas.")
            
            tipo_erro_lower = maior_erro['Tipo Detalhado'].lower()
            if "dois toque" in tipo_erro_lower or "condução" in tipo_erro_lower:
                st.warning("⚠️ **Técnica:** Cuidado com o contato na bola. Treine o 'toque' isolado.")
            elif "bola não permite" in tipo_erro_lower:
                st.warning("⚠️ **Tática:** Melhore o deslocamento para chegar equilibrado.")
        else:
            st.success("🌟 Desempenho perfeito! Nenhum erro registrado.")


def renderizar_evolucao_temporal(dados):
    """Gráficos de linha mostrando histórico."""
    st.subheader("Histórico de Performance")
    
    # Gráfico 1: Visão Categórica
    evolucao_por_categoria = dados.groupby(['Data', 'Categoria']).agg({
        'Quantidade correta': 'sum',
        'Total Calculado': 'sum'
    }).reset_index()
    
    evolucao_por_categoria['Eficiencia'] = evolucao_por_categoria['Quantidade correta'] / evolucao_por_categoria['Total Calculado']
    
    grafico_linhas = px.line(
        evolucao_por_categoria,
        x='Data', 
        y='Eficiencia', 
        color='Categoria', 
        markers=True,
        color_discrete_map=CORES_CATEGORIAS, # Usa constante global
        title="Evolução Diária por Fundamento"
    )
    grafico_linhas.update_yaxes(tickformat='.0%')
    st.plotly_chart(grafico_linhas, use_container_width=True)
    




# --- Função Principal (Ponto de Entrada) ---

def main():
    configurar_pagina_inicial()
    aplicar_estilos_visuais()
    
    st.title("🏐 Análise de Desempenho - Vôlei de Praia")
    st.markdown("### Dashboard Profissional de Monitoramento de Treinos")
    
    dados_carregados = obter_dados_com_cache()
    
    if dados_carregados.empty:
        st.error("Não foi possível carregar os dados. Verifique a fonte de dados.")
        st.stop()
        
    dados_para_exibicao = aplicar_filtros_laterais(dados_carregados)
    
    renderizar_kpis_globais(dados_para_exibicao)
    renderizar_metricas_por_categoria(dados_para_exibicao)
    renderizar_analise_detalhada_levantamento(dados_para_exibicao) # Nova função adicionada
    renderizar_quadrante_ataque(dados_para_exibicao)
    renderizar_evolucao_temporal(dados_para_exibicao)


if __name__ == "__main__":
    main()
