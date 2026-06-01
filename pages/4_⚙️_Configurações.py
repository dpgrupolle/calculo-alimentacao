"""Página: Configurações (Funcionários, Faixas, Modelo Sodexo)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.utils.estilo import aplicar_css_lle
from src.utils.auth_guard import exigir_login_ou_parar
from src.utils.permissoes import pode_editar

st.set_page_config(page_title="Configurações", page_icon="⚙️", layout="wide")
aplicar_css_lle()
usuario = exigir_login_ou_parar()

if not pode_editar(usuario):
    st.error("🔒 Configurações são acessíveis a Gestão de RH e Analista de RH.")
    st.stop()

from src.telas.configuracoes import renderizar_configuracoes
renderizar_configuracoes(usuario)
