"""Página: Usuários (Gestão de RH gerencia; Diretoria visualiza)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.utils.estilo import aplicar_css_lle
from src.utils.auth_guard import exigir_login_ou_parar
from src.utils.permissoes import pode_visualizar_admin

st.set_page_config(page_title="Usuários", page_icon="🛡️", layout="wide")
aplicar_css_lle()
usuario = exigir_login_ou_parar()

if not pode_visualizar_admin(usuario):
    st.error("🔒 Acesso restrito à Gestão de RH e Diretoria.")
    st.stop()

from src.telas.admin_usuarios import renderizar_admin_usuarios, renderizar_auditoria

aba_users, aba_audit = st.tabs(["👥 Usuários", "📋 Auditoria"])
with aba_users:
    renderizar_admin_usuarios(usuario)
with aba_audit:
    renderizar_auditoria(usuario)
