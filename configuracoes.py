# Configurações globais da aplicação (Estilos, Cores e Textos)

# Estilos CSS
ESTILOS_CSS = """
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
        /* Estilo da Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1a1c24;
        }
        /* Tags do Multiselect */
        .stMultiSelect span[data-baseweb="tag"] {
            background-color: #262730 !important;
            border: 1px solid #4a4d5a;
        }
    </style>
"""

# Mapa de Cores por Categoria
CORES_CATEGORIAS = {
    'Ataque': '#e74c3c',       # Vermelho
    'Levantamento': '#f1c40f', # Amarelo
    'Recepção': '#3498db',     # Azul
    'Saque': '#2ecc71',        # Verde
    'Outros': '#95a5a6'        # Cinza
}

# Texto de ajuda para cada fundamento (Tooltip)
# Indentação removida para garantir renderização correta do Markdown no Streamlit
CRITERIOS_AVALIACAO = {
    'Recepção': """**✅ Certa:**
Sempre na zona de levantamento, próximo à rede e bola na frente.

**❌ Errada:**
Bola fora da zona de levantamento.""",
    
    'Ataque': """**✅ Certa:**
Ponto direto.

**❌ Errada:**
Bola fora, bloqueio direto, defesa adversária.""",
    
    'Levantamento': """**✅ Certa:**
Altura adequada; Ataque possível; Atacante equilibrado.

**❌ Errada:**
Dois toques; Condução; Bola não permite ataque.""",
    
    'Saque': """**✅ Certa:**
Bola dentro da quadra adversária.

**❌ Errada:**
Bola fora, bola na rede."""
}
