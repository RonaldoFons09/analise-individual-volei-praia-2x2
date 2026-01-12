import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dashboard_data import load_data

# Page Configuration
st.set_page_config(
    page_title="Vôlei Performance Dashboard",
    page_icon="🏐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Professional" Look
st.markdown("""
    <style>
        .stApp {
            background-color: #0e1117;
            color: #fafafa;
        }
        .metric-card {
            background-color: #262730;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1, h2, h3 {
            font-family: 'Segoe UI', sans-serif;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# Load Data
# Load Data
# ttl=60 ensures data is refreshed every 60 seconds automatically
@st.cache_data(ttl=60)
def get_data():
    # Load from Google Sheets (Source is handled inside load_data via secrets)
    return load_data()

# Refresh Button in Sidebar
if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

df = get_data()

# Header
st.title("🏐 Análise de Desempenho - Vôlei de Praia")
st.markdown("### Dashboard Profissional de Monitoramento de Treinos")

if df.empty:
    st.error("Não foi possível carregar os dados. Verifique o arquivo Excel.")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filtros")

# Date Filter
# Date Filter
min_date = df['Data'].min()
max_date = df['Data'].max()
date_range = st.sidebar.date_input(
    "Período",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Handle cases where date_input might return a single date (e.g. initial load or single selection)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = date_range[0]
    end_date = date_range[0]


# Filter Data by Date
mask_date = (df['Data'] >= pd.to_datetime(start_date)) & (df['Data'] <= pd.to_datetime(end_date))
filtered_df = df.loc[mask_date]

# Location Filter
locations = sorted(filtered_df['Local'].unique().tolist())
selected_location = st.sidebar.selectbox("Local", ["Todos"] + locations)

if selected_location != "Todos":
    filtered_df = filtered_df[filtered_df['Local'] == selected_location]

st.sidebar.markdown("---")
st.sidebar.subheader("Filtrar Fundamentos")

# Category Filter (New High Level Filter)
categories = sorted(filtered_df['Categoria'].unique().tolist())
selected_categories = st.sidebar.multiselect(
    "1. Selecione Categorias (Opcional)",
    categories,
    placeholder="Todas as categorias"
)

# Filter by Category first if selected
if selected_categories:
    filtered_df = filtered_df[filtered_df['Categoria'].isin(selected_categories)]

# Specific Fundament Filter (Dependent on Category)
# Note: changing default to [] (empty) prevents the "Wall of Tags"
available_fundaments = sorted(filtered_df['Fundamentos'].unique().tolist())
selected_fundament = st.sidebar.multiselect(
    "2. Detalhes Específicos (Opcional)", 
    available_fundaments,
    placeholder="Todos os tipos"
)

if selected_fundament:
    filtered_df = filtered_df[filtered_df['Fundamentos'].isin(selected_fundament)]

# Custom CSS for Sidebar to look more "Modern"
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            background-color: #1a1c24;
        }
        /* Custom styling for multiselect tags to be less aggressive */
        .stMultiSelect span[data-baseweb="tag"] {
            background-color: #262730 !important;
            border: 1px solid #4a4d5a;
        }
    </style>
""", unsafe_allow_html=True)

# --- MAIN DASHBOARD ---

# KPIs
col1, col2, col3, col4 = st.columns(4)

total_attempts = filtered_df['Total Calculated'].sum()
total_correct = filtered_df['Quantidade correta'].sum()
overall_efficiency = (total_correct / total_attempts * 100) if total_attempts > 0 else 0
total_sessions = filtered_df['Data'].nunique()

col1.metric("Eficiência Geral", f"{overall_efficiency:.1f}%")
col2.metric("Total de Ações", int(total_attempts))
col3.metric("Acertos Totais", int(total_correct))
col4.metric("Sessões de Treino", total_sessions)

st.markdown("---")

# Visualizations
# --- GENERAL PERFORMANCE ANALYSIS ---
st.subheader("Desempenho Geral (Agrupado)")

# Threshold Helper
def get_color(efficiency):
    if efficiency >= 0.70:
        return '#2ecc71' # Green (Excellent)
    elif efficiency >= 0.50:
        return '#f1c40f' # Yellow (Attention)
    else:
        return '#e74c3c' # Red (Critical)

def get_status(efficiency):
    if efficiency >= 0.70:
        return 'Excelente'
    elif efficiency >= 0.50:
        return 'Atenção'
    else:
        return 'Crítico'

# Group by Category (Ataque, Levantamento, etc)
cat_group = filtered_df.groupby('Categoria').agg({
    'Quantidade correta': 'sum',
    'Total Calculated': 'sum'
}).reset_index()

cat_group['Eficiencia'] = cat_group['Quantidade correta'] / cat_group['Total Calculated']

# Order logic: Saque, Recepção, Levantamento, Ataque (Logic flow of the game) or just standard sort
order_map = {'Saque': 1, 'Recepção': 2, 'Levantamento': 3, 'Ataque': 4}
cat_group['Order'] = cat_group['Categoria'].map(order_map).fillna(99)
cat_group = cat_group.sort_values('Order')

# Display Metrics Cards
cols = st.columns(len(cat_group))

# Criteria Guide
criteria_map = {
    'Recepção': "**✅ Certa:**\nSempre na zona de levantamento, próximo à rede e bola na frente.\n\n**❌ Errada:**\nBola fora da zona de levantamento.",
    'Ataque': "**✅ Certa:**\nPonto direto.\n\n**❌ Errada:**\nBola fora, bloqueio direto, defesa adversária.",
    'Levantamento': "**✅ Certa:**\nAltura adequada; Ataque possível; Atacante equilibrado.\n\n**❌ Errada:**\nDois toques; Condução; Bola não permite ataque.",
    'Saque': "**✅ Certa:**\nBola dentro da quadra adversária.\n\n**❌ Errada:**\nBola fora, bola na rede."
}

for idx, row in cat_group.iterrows():
    eff = row['Eficiencia']
    color = get_color(eff)
    status = get_status(eff)
    cat = row['Categoria']
    tooltip = criteria_map.get(cat, "Sem critério definido.")
    
    with cols[idx % len(cols)]:
        # Colored bar to maintain the visual cue
        st.markdown(f"<div style='height: 4px; width: 100%; background-color: {color}; border-radius: 4px; margin-bottom: 8px;'></div>", unsafe_allow_html=True)
        
        # Native Metric with Help Tooltip (Markdown supported)
        st.metric(
            label=cat,
            value=f"{eff:.1%}",
            help=tooltip,
            delta=None # Delta removed to keep cleaner, info moving to caption
        )
        # Caption for details
        st.caption(f"**{status}** • {int(row['Total Calculated'])}/{int(row['Quantidade correta'])} acertos")

st.markdown("---")


# --- MAGIC QUADRANT (TACTICAL ANALYSIS) ---
st.subheader("Mapa de Decisão de Ataque (Quadrante Mágico)", help="""
**Como interpretar os quadrantes:**
\n
💎 **SEGURANÇA** (Alta Eficiência + Alto Volume):  
Seus golpes de confiança. Continue usando!
\n
🚀 **POTENCIAL** (Alta Eficiência + Baixo Volume):  
Golpes que você acerta, mas usa pouco. **Dica Tática:** Tente usar mais vezes no jogo.
\n
⚠️ **RISCO/VÍCIO** (Baixa Eficiência + Alto Volume):  
Golpes que você usa muito, mas erra muito. **Dica Tática:** Pare de insistir ou treine separado.
\n
🗑️ **DESCARTE** (Baixa Eficiência + Baixo Volume):  
Golpes que não funcionam. Evite.
""")

# Filter for Attack Variations ONLY
# We want specific types like "Ataque - Pinga", "Ataque - Diagonal". 
# So we filter for strings starting with 'Ataque -'
attack_df = filtered_df[filtered_df['Fundamentos'].str.startswith('Ataque -')]

if attack_df.empty:
    st.info("Sem dados de variações de ataque para o período selecionado.")
else:
    # Group again specifically for this chart
    attack_group = attack_df.groupby('Fundamentos').agg({
        'Quantidade correta': 'sum',
        'Total Calculated': 'sum'
    }).reset_index()
    
    attack_group['Eficiencia'] = attack_group['Quantidade correta'] / attack_group['Total Calculated']

    # Determine thresholds for quadrants based on Attack data
    avg_volume = attack_group['Total Calculated'].mean()
    target_efficiency = 0.60 

    fig_scat = px.scatter(
        attack_group,
        x='Total Calculated',
        y='Eficiencia',
        text='Fundamentos',
        size='Total Calculated', # Bubble size = Volume
        hover_data=['Quantidade correta'],
        color='Eficiencia',
        color_continuous_scale='RdYlGn',
        title=f"Volume (x) vs Eficiência (y) - Variações de Ataque"
    )

    # Reference lines to form quadrants
    fig_scat.add_hline(y=target_efficiency, line_dash="dash", line_color="white", annotation_text="Meta Eficiência")
    fig_scat.add_vline(x=avg_volume, line_dash="dash", line_color="white", annotation_text="Média Volume")

    # Quadrant Labels (Fixed positions/Smart positions)
    # Top Right: Security
    fig_scat.add_annotation(x=attack_group['Total Calculated'].max(), y=1.0, text="💎 SEGURANÇA", showarrow=False, font=dict(color="#2ecc71", size=14))
    # Top Left: Potential
    fig_scat.add_annotation(x=attack_group['Total Calculated'].min(), y=1.0, text="🚀 POTENCIAL", showarrow=False, font=dict(color="#3498db", size=14))
    # Bottom Right: Vices/Risk
    fig_scat.add_annotation(x=attack_group['Total Calculated'].max(), y=0.0, text="⚠️ RISCO/VÍCIO", showarrow=False, font=dict(color="#e74c3c", size=14))
    # Bottom Left: Discard
    fig_scat.add_annotation(x=attack_group['Total Calculated'].min(), y=0.0, text="🗑️ DESCARTE", showarrow=False, font=dict(color="#7f8c8d", size=14))

    # Custom Hover Template
    fig_scat.update_traces(
        textposition='top center',
        hovertemplate="<b>%{text}</b><br>Eficiência: %{y:.0%}<br>Volume: %{x}<br>Acertos: %{customdata[0]}<extra></extra>"
    )
    fig_scat.update_layout(
        xaxis_title="Volume de Tentativas",
        yaxis_title="Eficiência (%)",
        yaxis_tickformat='.0%',
        coloraxis_colorbar=dict(
            tickformat='.0%',
            title="Eficiência"
        ),
        height=500
    )

    st.plotly_chart(
        fig_scat, 
        use_container_width=True,
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtons': [['toImage']] # Only show Download Image button
        }
    )

# Efficiency Over Time (General)
st.subheader("Evolução da Eficiência Geral no Tempo")
time_group = filtered_df.groupby('Data').agg({
    'Quantidade correta': 'sum',
    'Total Calculated': 'sum'
}).reset_index()
time_group['Eficiencia'] = time_group['Quantidade correta'] / time_group['Total Calculated']

fig_line_general = px.line(
    time_group,
    x='Data',
    y='Eficiencia',
    markers=True,
    title="Evolução da Eficiência Geral Diária"
)
fig_line_general.update_yaxes(tickformat='.0%')
st.plotly_chart(
    fig_line_general,
    use_container_width=True,
    config={
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtons': [['toImage']]
    }
)

# Efficiency Over Time (Categorized)
st.subheader("Evolução da Eficiência no Tempo por Categoria")

# Group by Date and Category
time_cat_group = filtered_df.groupby(['Data', 'Categoria']).agg({
    'Quantidade correta': 'sum',
    'Total Calculated': 'sum'
}).reset_index()

time_cat_group['Eficiencia'] = time_cat_group['Quantidade correta'] / time_cat_group['Total Calculated']

# Define custom colors for consistency
category_colors = {
    'Ataque': '#e74c3c',       # Red-ish
    'Levantamento': '#f1c40f', # Yellow-ish
    'Recepção': '#3498db',     # Blue-ish
    'Saque': '#2ecc71',        # Green-ish
    'Outros': '#95a5a6'
}

fig_line = px.line(
    time_cat_group,
    x='Data',
    y='Eficiencia',
    color='Categoria',
    markers=True,
    color_discrete_map=category_colors,
    title="Evolução da Eficiência Diária por Fundamento"
)
fig_line.update_yaxes(tickformat='.0%')
st.plotly_chart(
    fig_line, 
    use_container_width=True,
    config={
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtons': [['toImage']]
    }
)

# Table below the chart
st.markdown("##### Tabela de Eficiência Diária")
# Pivot for better reading: Dates as rows, Categories as columns
pivot_table = time_cat_group.pivot(index='Data', columns='Categoria', values='Eficiencia')
st.dataframe(
    pivot_table.style.format('{:.1%}'),
    width='stretch'
)


# Detailed Data View
st.markdown("---")
st.subheader("Detalhamento dos Dados")
with st.expander("Ver Tabela Completa"):
    display_cols = ['Data', 'Local', 'Fundamentos', 'Quantidade correta', 'Quantidade errada', 'Total Calculated', 'Eficiencia']
    st.dataframe(
        filtered_df[display_cols].style.format({
            'Eficiencia': '{:.1%}',
            'Quantidade correta': '{:.0f}',
            'Quantidade errada': '{:.0f}',
            'Total Calculated': '{:.0f}'
        }),
        width='stretch'
    )
