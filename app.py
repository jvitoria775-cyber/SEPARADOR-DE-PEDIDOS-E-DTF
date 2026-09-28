"""Sistema de Gestão de Pedidos e Produção DTF
Aplicação principal Streamlit.
"""
import streamlit as st
import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import init_db

# Inicializar banco de dados
init_db()

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Gratitude Têxtil - Gestão DTF",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS CUSTOMIZADO
# ============================================================
st.markdown("""
<style>
    /* Header principal */
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f1f1f;
        margin-bottom: 0.5rem;
    }
    
    /* Cards com borda */
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #fafafa;
    }
    
    /* Botões */
    .stButton > button {
        border-radius: 8px;
    }
    
    /* Métricas */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR - NAVEGAÇÃO
# ============================================================
with st.sidebar:
    st.image("assets/logo.png", width=120)
    st.caption("Sistema de Pedidos & Produção DTF")
    st.divider()

    pagina = st.radio(
        "Navegação",
        options=[
            "📦 Importar Pedidos",
            "📋 Cadastro de Produtos",
            "🔗 Associação De/Para",
            "📝 Lista de Separação",
            "🖨️ Produção DTF"
        ],
        index=0,
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("v1.0 — Gratitude Têxtil")
    st.caption("Sistema Interno de Gestão")

# ============================================================
# ROTEAMENTO DE PÁGINAS
# ============================================================
if pagina == "📦 Importar Pedidos":
    from modules.importacao import render
    render()

elif pagina == "📋 Cadastro de Produtos":
    from modules.cadastro import render
    render()

elif pagina == "🔗 Associação De/Para":
    from modules.associacao import render
    render()

elif pagina == "📝 Lista de Separação":
    from modules.separacao import render
    render()

elif pagina == "🖨️ Produção DTF":
    from modules.dtf_producao import render
    render()
