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
@st.cache_data
def get_data():
    file_path = 'Autoavaliação vôlei de praia (1).xlsx'
    return load_data(file_path)

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
min_date = df['Data'].min()
max_date = df['Data'].max()
start_date, end_date = st.sidebar.date_input(
    "Período",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

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
for idx, row in cat_group.iterrows():
    eff = row['Eficiencia']
    color = get_color(eff)
    status = get_status(eff)
    
    with cols[idx % len(cols)]:
        st.markdown(f"""
            <div class="metric-card" style="border-left: 5px solid {color};">
                <h3 style="margin:0">{row['Categoria']}</h3>
                <h2 style="margin:0; color: {color}">{eff:.1%}</h2>
                <p style="margin:0; font-size: 0.9em; opacity: 0.8">{status}</p>
                <p style="margin:0; font-size: 0.8em; opacity: 0.6">{int(row['Total Calculated'])}/{int(row['Quantidade correta'])} acertos</p>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# --- DETAILED ANALYSIS ---
st.subheader("Eficiência Detalhada por Variação")

# Clean Data for Chart
# User request: Keep Attack variations detailed, but aggregate Levantamento.
# Since "Levantamento" exists as a row, we just hide the "Levantamento - ..." specific ones
# which are mostly error descriptions or redundancy.

fundament_group = filtered_df.groupby('Fundamentos').agg({
    'Quantidade correta': 'sum',
    'Total Calculated': 'sum'
}).reset_index()

# Filter: Exclude "Levantamento -" rows. Keep "Levantamento" exact match.
fundament_group = fundament_group[~fundament_group['Fundamentos'].str.contains('Levantamento -')]

fundament_group['Eficiencia'] = fundament_group['Quantidade correta'] / fundament_group['Total Calculated']
fundament_group = fundament_group.sort_values('Eficiencia', ascending=True)

# Apply colors to chart bars based on threshold
colors = [get_color(e) for e in fundament_group['Eficiencia']]

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    x=fundament_group['Eficiencia'],
    y=fundament_group['Fundamentos'],
    orientation='h',
    text=fundament_group['Eficiencia'].apply(lambda x: f'{x:.1%}'),
    textposition='auto',
    marker_color=colors
))

fig_bar.update_layout(
    title="Eficiência por Variação Específica",
    xaxis_tickformat='.0%', 
    xaxis_title="Eficiência",
    yaxis_title="",
    height=max(400, len(fundament_group)*40) # Adjust height based on items
)
st.plotly_chart(fig_bar, use_container_width=True)

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
st.plotly_chart(fig_line_general, use_container_width=True)

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
st.plotly_chart(fig_line, use_container_width=True)

# Table below the chart
st.markdown("##### Tabela de Eficiência Diária")
# Pivot for better reading: Dates as rows, Categories as columns
pivot_table = time_cat_group.pivot(index='Data', columns='Categoria', values='Eficiencia')
st.dataframe(
    pivot_table.style.format('{:.1%}'),
    use_container_width=True
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
        use_container_width=True
    )
