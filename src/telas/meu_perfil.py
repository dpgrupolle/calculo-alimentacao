"""Tela Meu Perfil — o usuário vê seus dados e troca nome/senha."""
from __future__ import annotations

import streamlit as st

from src.banco import repo_usuario
from src.servicos import auditoria
from src.utils.traducoes import traduzir_perfil


def renderizar_meu_perfil(usuario):
    st.markdown("## 👤 Meu Perfil")

    # Mensagem persistente (Regra 2)
    msg = st.session_state.pop("perfil_msg", None)
    if msg:
        {"sucesso": st.success, "erro": st.error, "aviso": st.warning}.get(
            msg["tipo"], st.info)(msg["texto"])

    st.markdown(
        f"**Nome:** {usuario.nome}  \n"
        f"**E-mail:** {usuario.email}  \n"
        f"**Cargo:** {traduzir_perfil(usuario.perfil.value)}"
    )
    st.markdown("---")

    # ─── Alterar nome ───────────────────────────────────────
    st.markdown("### Alterar nome")
    with st.form("form_nome"):
        novo_nome = st.text_input("Nome completo", value=usuario.nome)
        salvar_nome = st.form_submit_button("Salvar nome", type="primary")
        if salvar_nome:
            try:
                repo_usuario.alterar_nome(usuario.id, novo_nome)
                atualizado = repo_usuario.buscar_por_id(usuario.id)
                st.session_state["usuario_atual"] = atualizado
                auditoria.registrar(usuario, "TROCAR_PROPRIA_SENHA",
                                    entidade="usuario", entidade_id=usuario.id,
                                    detalhes="Alterou o próprio nome")
                st.session_state["perfil_msg"] = {"tipo": "sucesso", "texto": "✅ Nome atualizado!"}
            except ValueError as e:
                st.session_state["perfil_msg"] = {"tipo": "erro", "texto": f"❌ {e}"}
            except Exception as e:
                st.session_state["perfil_msg"] = {"tipo": "erro", "texto": f"❌ Erro: {e}"}
            st.rerun()

    st.markdown("---")

    # ─── Alterar senha ──────────────────────────────────────
    st.markdown("### Alterar senha")
    with st.form("form_senha"):
        atual = st.text_input("Senha atual", type="password")
        nova = st.text_input("Nova senha (mín. 8 caracteres)", type="password")
        conf = st.text_input("Confirme a nova senha", type="password")
        salvar_senha = st.form_submit_button("Salvar nova senha", type="primary")
        if salvar_senha:
            try:
                if repo_usuario.autenticar(usuario.email, atual) is None:
                    raise ValueError("Senha atual incorreta.")
                if nova != conf:
                    raise ValueError("A nova senha e a confirmação não conferem.")
                repo_usuario.alterar_senha(usuario.id, nova)
                auditoria.registrar(usuario, "TROCAR_PROPRIA_SENHA",
                                    entidade="usuario", entidade_id=usuario.id)
                st.session_state["perfil_msg"] = {"tipo": "sucesso",
                                                  "texto": "✅ Senha alterada com sucesso!"}
            except ValueError as e:
                st.session_state["perfil_msg"] = {"tipo": "erro", "texto": f"❌ {e}"}
            except Exception as e:
                st.session_state["perfil_msg"] = {"tipo": "erro", "texto": f"❌ Erro: {e}"}
            st.rerun()
