"""Tela Faixas e Regras — valores das 13 faixas + regra de desconto (fixa, informativa)."""
from __future__ import annotations
import pandas as pd
import streamlit as st
from src.banco import repo_tabela
from src.servicos import auditoria
from src.utils.estilo import fmt_real
from src.utils.permissoes import pode_alterar_parametros


def renderizar_tabelas_regras(usuario):
    st.markdown("## 📐 Faixas e Regras")
    pode = pode_alterar_parametros(usuario)

    msg = st.session_state.pop("tr_msg", None)
    if msg:
        {"sucesso": st.success, "erro": st.error, "aviso": st.warning}.get(msg["tipo"], st.info)(msg["texto"])

    st.markdown("### 💰 Faixas de alimentação")
    st.caption("Valor cheio (100%) do prêmio por faixa. A faixa 13 = R$ 0 (sem direito).")
    faixas = repo_tabela.listar_faixas()
    df = pd.DataFrame([{"Faixa": f["numero"], "Nome": f["nome"], "Valor": fmt_real(f["valor_premio"]),
                        "Ativa": "Sim" if f["ativo"] else "Não"} for f in faixas])
    st.dataframe(df, use_container_width=True, hide_index=True)

    if pode:
        st.markdown("#### Editar valor de uma faixa")
        nums = [f["numero"] for f in faixas]
        sel = st.selectbox("Faixa", nums, format_func=lambda n: f"Faixa {n}")
        atual = next((f for f in faixas if f["numero"] == sel), None)
        if atual:
            with st.form(f"edit_faixa_{sel}"):
                nome = st.text_input("Nome", value=atual["nome"])
                valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0, value=float(atual["valor_premio"]), format="%.2f")
                if st.form_submit_button("💾 Salvar", type="primary"):
                    try:
                        repo_tabela.atualizar_faixa(atual["id"], nome, valor, True)
                        auditoria.registrar(usuario, "EDITAR_TABELA", entidade_id=atual["id"], detalhes=f"Faixa {sel}")
                        st.session_state["tr_msg"] = {"tipo": "sucesso", "texto": "✅ Faixa atualizada."}
                    except Exception as e:
                        st.session_state["tr_msg"] = {"tipo": "erro", "texto": f"❌ {e}"}
                    st.rerun()

    st.markdown("---")
    st.markdown("### ✂️ Regra de desconto (fixa)")
    st.info("O desconto é o **pior caso** entre faltas e atraso acumulado no período:\n\n"
            "| Situação | Perde |\n|---|---|\n"
            "| 1 falta **ou** 30 min de atraso | 50% |\n"
            "| 2 faltas **ou** 1 hora | 75% |\n"
            "| 3 faltas **ou** 1h30 | 100% (zera) |\n\n"
            "Atestado conta como falta (todos os tipos). A falta cheia da jornada = 1 dia de falta. "
            "Exceções (valor fora das faixas, ex. diretoria/sócios) mantêm o valor, sem desconto.")
