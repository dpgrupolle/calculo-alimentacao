"""Tela Processos — histórico dos fechamentos. Baixar conferência, reabrir, excluir (com senha).
   (A geração da planilha Sodexo fica no passo a passo, em ⚙️ Processar.)"""
from __future__ import annotations
import streamlit as st
from src.banco import repo_processo
from src.servicos import auditoria
from src.servicos.exportador_xlsx import gerar_xlsx_resultado
from src.utils.estilo import fmt_real, badge_status_processo
from src.utils.permissoes import pode_editar, pode_excluir
from src.utils.exclusao_com_senha import confirmar_exclusao_com_senha


def renderizar_processos(usuario):
    st.markdown("## 📁 Processos")
    st.caption("Histórico dos fechamentos. Para montar/gerar o do mês, use **⚙️ Processar**.")
    msg = st.session_state.pop("procs_msg", None)
    if msg:
        {"sucesso": st.success, "erro": st.error, "aviso": st.warning}.get(msg["tipo"], st.info)(msg["texto"])

    procs = repo_processo.listar_processos()
    if not procs:
        st.info("Nenhum processo ainda. Crie um em **⚙️ Processar benefício**.")
        return
    pode_e, pode_x = pode_editar(usuario), pode_excluir(usuario)
    for p in procs:
        _card(usuario, p, pode_e, pode_x)


def _card(usuario, p, pode_e, pode_x):
    pid = p["id"]
    titulo = f"[{p['empresa']}] " + p["mes_referencia"] + (f" · {p['descricao']}" if p["descricao"] else "")
    with st.expander(f"📦 {titulo}", expanded=False):
        st.markdown(badge_status_processo(p["status"]), unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Funcionários", p["total_funcionarios"])
        c2.metric("Prêmio cheio", fmt_real(p["valor_total_premios"]))
        c3.metric("Descontado", fmt_real(p["valor_total_descontos"]))
        c4.metric("Líquido", fmt_real(p["valor_total_liquido"]))

        if repo_processo.tem_resultados(pid):
            res = [dict(r) for r in repo_processo.listar_resultados(pid)]
            try:
                st.download_button("⬇️ Baixar conferência (.xlsx)", data=gerar_xlsx_resultado(dict(p), res),
                                   file_name=f"conferencia_{p['mes_referencia']}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dl_{pid}")
            except Exception as e:
                st.caption(f"(conferência indisponível: {e})")
        else:
            st.caption("Sem resultado calculado.")

        if pode_e and p["status"] == "FINALIZADO":
            if st.button("↩️ Reabrir", key=f"reab_{pid}"):
                repo_processo.reabrir(pid)
                auditoria.registrar(usuario, "FINALIZAR_PROCESSO", entidade_id=pid, detalhes="reabriu")
                st.rerun()
        if pode_x:
            st.markdown("---")
            confirmar_exclusao_com_senha(usuario, f"del_proc_{pid}", f"processo {titulo}",
                                         lambda i=pid: _excluir(usuario, i), "🗑 Excluir processo")


def _excluir(usuario, pid):
    repo_processo.excluir_processo(pid)
    auditoria.registrar(usuario, "EXCLUIR_PROCESSO", entidade_id=pid)
