"""Tela Configurações — junta Funcionários, Faixas e Regras e Modelo Sodexo em abas."""
from __future__ import annotations
import streamlit as st
from src.telas.funcionarios import renderizar_funcionarios
from src.telas.tabelas_regras import renderizar_tabelas_regras
from src.telas.modelo_sodexo import renderizar_modelo_sodexo


def renderizar_configuracoes(usuario):
    st.markdown("## ⚙️ Configurações")
    st.caption("Cadastro de funcionários, faixas/regras e a planilha-base da Sodexo — tudo num lugar só.")
    aba_func, aba_faixa, aba_sodexo = st.tabs(["👥 Funcionários", "📐 Faixas e Regras", "📤 Modelo Sodexo"])
    with aba_func:
        renderizar_funcionarios(usuario)
    with aba_faixa:
        renderizar_tabelas_regras(usuario)
    with aba_sodexo:
        renderizar_modelo_sodexo(usuario)
