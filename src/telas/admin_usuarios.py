"""
Tela Usuários.
- Gestão de RH: gerencia (aprova, recusa, muda cargo, inativa, redefine senha).
- Diretoria: apenas visualiza a lista.
"""
from __future__ import annotations

import secrets as _secrets

import streamlit as st

from src.banco import repo_usuario
from src.modelos.tipos import PerfilUsuario
from src.servicos import auditoria
from src.utils.permissoes import pode_gerenciar_usuarios
from src.utils.traducoes import traduzir_perfil


def renderizar_admin_usuarios(usuario):
    st.markdown("## 🛡️ Usuários")

    msg = st.session_state.pop("usuarios_msg", None)
    if msg:
        {"sucesso": st.success, "erro": st.error, "aviso": st.warning}.get(
            msg["tipo"], st.info)(msg["texto"])

    pode_gerir = pode_gerenciar_usuarios(usuario)
    if not pode_gerir:
        st.info("👁️ Você tem acesso somente de visualização desta área.")

    usuarios = repo_usuario.listar_todos()

    # ─── Pendentes de aprovação ─────────────────────────────
    pendentes = [u for u in usuarios if not u.aprovado and u.ativo]
    if pendentes and pode_gerir:
        st.markdown("### ⏳ Aguardando aprovação")
        for u in pendentes:
            with st.container():
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(
                    f"**{u.nome}** · {u.email}  \n"
                    f"<small>Chave: <code>{u.chave_aprovacao or '—'}</code></small>",
                    unsafe_allow_html=True,
                )
                if c2.button("✅ Aprovar", key=f"aprovar_{u.id}", type="primary"):
                    try:
                        repo_usuario.aprovar_usuario(u.id)
                        auditoria.registrar(usuario, "APROVAR_USUARIO",
                                            entidade="usuario", entidade_id=u.id,
                                            detalhes=u.email)
                        st.session_state["usuarios_msg"] = {
                            "tipo": "sucesso", "texto": f"✅ {u.nome} aprovado(a)."}
                    except Exception as e:
                        st.session_state["usuarios_msg"] = {"tipo": "erro", "texto": f"❌ {e}"}
                    st.rerun()
                if c3.button("🚫 Recusar", key=f"recusar_{u.id}"):
                    try:
                        repo_usuario.recusar_usuario(u.id)
                        auditoria.registrar(usuario, "RECUSAR_USUARIO",
                                            entidade="usuario", entidade_id=u.id,
                                            detalhes=u.email)
                        st.session_state["usuarios_msg"] = {
                            "tipo": "aviso", "texto": f"🚫 {u.nome} recusado(a)."}
                    except Exception as e:
                        st.session_state["usuarios_msg"] = {"tipo": "erro", "texto": f"❌ {e}"}
                    st.rerun()
        st.markdown("---")

    # ─── Lista de usuários ──────────────────────────────────
    st.markdown("### Equipe")
    ativos = [u for u in usuarios if u.aprovado and u.ativo]
    inativos = [u for u in usuarios if not u.ativo]

    for u in ativos:
        _linha_usuario(usuario, u, pode_gerir)

    if inativos:
        with st.expander(f"Inativos ({len(inativos)})"):
            for u in inativos:
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"~~{u.nome}~~ · {u.email} · {traduzir_perfil(u.perfil.value)}")
                if pode_gerir and c2.button("Reativar", key=f"reativar_{u.id}"):
                    try:
                        repo_usuario.reativar_usuario(u.id)
                        auditoria.registrar(usuario, "REATIVAR_USUARIO",
                                            entidade="usuario", entidade_id=u.id)
                        st.session_state["usuarios_msg"] = {
                            "tipo": "sucesso", "texto": f"✅ {u.nome} reativado(a)."}
                    except Exception as e:
                        st.session_state["usuarios_msg"] = {"tipo": "erro", "texto": f"❌ {e}"}
                    st.rerun()


def _linha_usuario(logado, u, pode_gerir):
    eh_voce = u.id == logado.id
    with st.container():
        c1, c2 = st.columns([3, 2])
        c1.markdown(
            f"**{u.nome}** {'(você)' if eh_voce else ''}  \n"
            f"<small>{u.email} · {traduzir_perfil(u.perfil.value)}</small>",
            unsafe_allow_html=True,
        )
        if not pode_gerir:
            return
        with c2:
            with st.expander("Gerenciar"):
                # Alterar cargo
                perfis = list(PerfilUsuario)
                idx = perfis.index(u.perfil)
                novo = st.selectbox(
                    "Cargo", perfis, index=idx,
                    format_func=lambda p: traduzir_perfil(p.value),
                    key=f"perfil_{u.id}",
                )
                if novo != u.perfil and st.button("Salvar cargo", key=f"savep_{u.id}"):
                    try:
                        repo_usuario.alterar_perfil(u.id, novo)
                        auditoria.registrar(logado, "ALTERAR_PERFIL_USUARIO",
                                            entidade="usuario", entidade_id=u.id,
                                            detalhes=f"{u.perfil.value} → {novo.value}")
                        st.session_state["usuarios_msg"] = {
                            "tipo": "sucesso", "texto": f"✅ Cargo de {u.nome} atualizado."}
                    except ValueError as e:
                        st.session_state["usuarios_msg"] = {"tipo": "erro", "texto": f"❌ {e}"}
                    st.rerun()

                # Redefinir senha
                if st.button("🔑 Redefinir senha", key=f"reset_{u.id}"):
                    try:
                        temp = _secrets.token_urlsafe(6)
                        repo_usuario.redefinir_senha_temporaria(u.id, temp)
                        auditoria.registrar(logado, "REDEFINIR_SENHA_USUARIO",
                                            entidade="usuario", entidade_id=u.id)
                        st.session_state["usuarios_msg"] = {
                            "tipo": "sucesso",
                            "texto": f"🔑 Senha temporária de {u.nome}: **{temp}** "
                                     f"(ele deverá trocá-la no próximo login)."}
                    except Exception as e:
                        st.session_state["usuarios_msg"] = {"tipo": "erro", "texto": f"❌ {e}"}
                    st.rerun()

                # Inativar
                if not eh_voce and st.button("🚫 Inativar", key=f"inativar_{u.id}"):
                    try:
                        repo_usuario.inativar_usuario(u.id)
                        auditoria.registrar(logado, "INATIVAR_USUARIO",
                                            entidade="usuario", entidade_id=u.id)
                        st.session_state["usuarios_msg"] = {
                            "tipo": "aviso", "texto": f"🚫 {u.nome} inativado(a)."}
                    except Exception as e:
                        st.session_state["usuarios_msg"] = {"tipo": "erro", "texto": f"❌ {e}"}
                    st.rerun()


def renderizar_auditoria(usuario):
    """Aba de Auditoria: histórico de ações registradas no sistema."""
    import pandas as pd
    from src.servicos.auditoria import listar_auditoria, acoes_distintas
    from src.utils.traducoes import traduzir_acao
    from src.utils.formatadores import formatar_data, formatar_hora

    st.markdown("### 📋 Auditoria")
    st.caption("Registro das ações feitas no sistema (quem fez, o quê e quando).")

    acoes = acoes_distintas()
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        busca = st.text_input("🔍 Buscar (usuário ou detalhe)", "", key="aud_busca")
    with c2:
        opes = ["Todas as ações"] + acoes
        sel = st.selectbox("Ação", opes, format_func=lambda a: a if a == "Todas as ações" else traduzir_acao(a), key="aud_acao")
        acao = "" if sel == "Todas as ações" else sel
    with c3:
        limite = st.selectbox("Mostrar", [50, 100, 200, 500], index=2, key="aud_lim")

    registros = listar_auditoria(limite=limite, acao=acao, busca=busca)
    if not registros:
        st.info("Nenhum registro de auditoria para os filtros selecionados.")
        return

    st.caption(f"{len(registros)} registro(s).")
    df = pd.DataFrame([{
        "Quando": f"{formatar_data(r['criado_em'])} {formatar_hora(r['criado_em'])}".strip(),
        "Usuário": r["usuario_nome_snapshot"] or "—",
        "Ação": traduzir_acao(r["acao"]),
        "Onde": (r["entidade"] or "") + (f" #{r['entidade_id']}" if r["entidade_id"] else ""),
        "Detalhes": r["detalhes"] or "",
    } for r in registros])
    st.dataframe(df, use_container_width=True, hide_index=True)
