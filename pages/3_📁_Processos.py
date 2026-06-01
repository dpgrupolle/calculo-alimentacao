"""Página: Processos (pasta de processos finalizados/andamento)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.utils.estilo import aplicar_css_lle
from src.utils.auth_guard import exigir_login_ou_parar

st.set_page_config(page_title="Processos", page_icon="📁", layout="wide")
aplicar_css_lle()
usuario = exigir_login_ou_parar()

from src.telas.processos import renderizar_processos
renderizar_processos(usuario)
