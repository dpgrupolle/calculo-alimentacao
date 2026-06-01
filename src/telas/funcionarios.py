"""Tela Funcionários — importa o cadastro (planilha do Sankhya) e lista."""
from __future__ import annotations
import hashlib
import pandas as pd
import streamlit as st
from src.banco import repo_funcionario
from src.servicos import auditoria
from src.servicos.parser_funcionarios import ler_planilha_funcionarios
from src.utils.permissoes import pode_editar


def renderizar_funcionarios(usuario):
    st.markdown("## 👥 Funcionários")
    st.caption("Cadastro do Sankhya: matrícula, nome, cargo, faixa de alimentação e carga horária.")
    pode = pode_editar(usuario)

    msg = st.session_state.pop("func_msg", None)
    if msg:
        {"sucesso": st.success, "erro": st.error, "aviso": st.warning}.get(msg["tipo"], st.info)(msg["texto"])

    if pode:
        with st.expander("📥 Importar planilha de funcionários (Sankhya)", expanded=repo_funcionario.contar() == 0):
            st.caption("O sistema lê o cabeçalho na 3ª linha e usa Código, Nome, Cargo, CPF, "
                       "‘Informe tab faixa ticket alim’ (faixa) e Carga Horária.")
            arq = st.file_uploader("Planilha de funcionários", type=["xlsx", "xls", "csv"], key="upl_cad")
            if arq is not None and st.button("📥 Importar", type="primary"):
                try:
                    h = hashlib.md5(arq.getvalue()).hexdigest()
                    if st.session_state.get("hash_cad") == h:
                        st.session_state["func_msg"] = {"tipo": "aviso", "texto": "ℹ️ Essa planilha já foi importada nesta sessão."}
                        st.rerun(); return
                    with st.spinner("Importando o cadastro… (pode levar alguns segundos)"):
                        res = ler_planilha_funcionarios(arq)
                        r = repo_funcionario.upsert_em_lote(res["funcionarios"])
                    st.session_state["hash_cad"] = h
                    auditoria.registrar(usuario, "IMPORTAR_FUNCIONARIOS", detalhes=f"{r['inseridos']} novos, {r['atualizados']} atualizados")
                    txt = f"✅ {r['inseridos']} novo(s), {r['atualizados']} atualizado(s) (de {res['total']} lidos)."
                    if res["avisos"]:
                        txt += "\n\n⚠️ " + "\n⚠️ ".join(res["avisos"][:8])
                    st.session_state["func_msg"] = {"tipo": "sucesso", "texto": txt}
                except ValueError as e:
                    st.session_state["func_msg"] = {"tipo": "erro", "texto": f"❌ {e}"}
                except Exception as e:
                    import traceback; st.session_state["func_msg"] = {"tipo": "erro", "texto": f"❌ {type(e).__name__}: {e}"}
                    st.session_state["func_erros"] = traceback.format_exc()
                st.rerun()
    erro = st.session_state.pop("func_erros", None)
    if erro:
        with st.expander("Ver detalhes do erro"):
            st.code(erro)

    busca = st.text_input("🔍 Buscar (nome, código ou CPF)", "")
    funcs = repo_funcionario.listar(busca=busca)
    st.caption(f"{len(funcs)} funcionário(s) cadastrado(s).")
    if funcs:
        df = pd.DataFrame([{
            "Código": f["codigo"], "Nome": f["nome"], "Empresa": f["empresa"] if "empresa" in f.keys() else "—",
            "Cargo": f["cargo"] or "—",
            "Faixa alim.": f["faixa_alim"] if f["faixa_alim"] is not None else "—",
            "Carga horária": f["carga_horaria"] or "—",
            "CPF": f["cpf"] or "—",
        } for f in funcs])
        st.dataframe(df, use_container_width=True, hide_index=True)
