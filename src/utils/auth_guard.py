"""
Proteção de páginas. Chamar NO TOPO de cada página em pages/.
Se não houver usuário logado, esconde a navegação, mostra aviso e para a execução.
"""
from __future__ import annotations

import streamlit as st


CSS_SIDEBAR_FIXA = """
<style>
    section[data-testid="stSidebar"] {
        min-width: 260px !important;
        max-width: 260px !important;
        width: 260px !important;
        transform: translateX(0px) !important;
        visibility: visible !important;
        margin-left: 0 !important;
    }
    section[data-testid="stSidebar"] button[kind="header"],
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseControl"],
    button[data-testid="collapsedControl"],
    button[data-testid="stSidebarCollapseButton"] {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
        width: 0 !important;
        height: 0 !important;
        opacity: 0 !important;
    }
    [data-testid="stSidebarNav"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .main .block-container {
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
</style>
"""


def exigir_login_ou_parar():
    """
    Sem usuário logado: esconde a sidebar, mostra aviso e para a página.
    Com usuário logado: aplica CSS de sidebar fixa, renderiza o menu e retorna o usuário.
    """
    usuario = st.session_state.get("usuario_atual")
    if usuario is None:
        st.markdown(
            """
            <style>
                section[data-testid="stSidebar"] { display: none !important; }
                [data-testid="stSidebarNav"] { display: none !important; }
                button[kind="header"] { display: none !important; }
                button[data-testid="collapsedControl"] { display: none !important; }
                header[data-testid="stHeader"] { display: none !important; }
                div[data-testid="stToolbar"] { display: none !important; }
                .block-container {
                    padding-top: 4rem !important;
                    max-width: 600px !important;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.warning("🔒 **Acesso restrito.** Faça login para acessar essa página.")
        st.page_link("app.py", label="← Ir para o login", icon="🏠")
        st.stop()

    st.markdown(CSS_SIDEBAR_FIXA, unsafe_allow_html=True)
    renderizar_menu_sidebar(usuario)
    return usuario


def renderizar_menu_sidebar(usuario):
    """Menu manual na sidebar (chamado em todas as páginas)."""
    from pathlib import Path
    from src.utils.permissoes import (
        pode_editar, pode_visualizar_admin, pode_gerenciar_usuarios,
    )
    from src.utils.traducoes import traduzir_perfil
    from src.utils.marca import VERSAO

    LOGO_BRANCO = Path(__file__).parent.parent.parent / "assets" / "logo_lle_branco.png"
    LOGO_COR = Path(__file__).parent.parent.parent / "assets" / "logo_lle.png"
    logo_a_usar = LOGO_BRANCO if LOGO_BRANCO.exists() else LOGO_COR

    with st.sidebar:
        if logo_a_usar.exists():
            st.image(str(logo_a_usar), use_container_width=True)
        st.markdown("---")
        st.markdown(f"👤 **{usuario.nome}**")
        st.caption(f"Perfil: {traduzir_perfil(usuario.perfil.value)}")
        st.page_link("pages/0_👤_Meu_Perfil.py", label="👤 Meu Perfil")
        st.markdown("---")

        st.markdown("**Menu**")
        st.page_link("pages/1_🏠_Início.py", label="🏠 Início")
        if pode_editar(usuario):
            st.page_link("pages/2_⚙️_Processar.py", label="⚙️ Processar benefício")
        st.page_link("pages/3_📁_Processos.py", label="📁 Processos")
        if pode_editar(usuario):
            st.page_link("pages/4_⚙️_Configurações.py", label="⚙️ Configurações")

        # Administração
        if pode_visualizar_admin(usuario):
            st.markdown("---")
            st.markdown("**Administração**")
            st.page_link("pages/5_🛡️_Usuários.py", label="🛡️ Usuários")

        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True, key=f"sair_sidebar_{usuario.id}"):
            for k in list(st.session_state.keys()):
                if k not in ("banco_inicializado",):
                    del st.session_state[k]
            st.rerun()
        st.caption(f"versão {VERSAO}")
