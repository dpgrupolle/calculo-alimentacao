"""
Tela Processar — passo a passo do fechamento mensal, TUDO numa página só:
  1) Processo do mês  2) Planilhas (faltas/atestados/férias)
  3) Revisar faltas   4) Revisar férias   5) Calcular
  6) Gerar planilha Sodexo (com as 3 datas)   7) Finalizar
"""
from __future__ import annotations
import hashlib
from datetime import date
import pandas as pd
import streamlit as st

from src.banco import repo_processo, repo_funcionario, repo_tabela, repo_sodexo
from src.servicos import auditoria
from src.servicos.parser_faltas import ler_planilha_faltas
from src.servicos.parser_atestados import ler_planilha_atestados
from src.servicos.parser_ferias import ler_planilha_ferias
from src.servicos.matching import IndiceCadastro
from src.servicos.calculo_beneficio import calcular_processo
from src.servicos.exportador_sodexo import preencher_sodexo
from src.servicos.exportador_xlsx import gerar_xlsx_resultado
from src.utils.estilo import fmt_real, fmt_pct
from src.utils.marca import EMPRESAS, COR_EMPRESA
from src.utils.permissoes import pode_excluir
from src.utils.exclusao_com_senha import confirmar_exclusao_com_senha


def _msg(tipo, texto, erro=None):
    st.session_state["proc_msg"] = {"tipo": tipo, "texto": texto}
    if erro:
        st.session_state["proc_erro"] = erro


def _indice_cadastro(empresa: str = ""):
    idx = IndiceCadastro()
    for f in repo_funcionario.todos_para_calculo(empresa):
        idx.adicionar(f)
    return idx


def _status(ok: bool) -> str:
    return "✅" if ok else "⬜"


def renderizar_processar(usuario):
    st.markdown("## ⚙️ Processar benefício")
    st.caption("Siga os passos de cima para baixo. Tudo do mês acontece nesta página.")

    msg = st.session_state.pop("proc_msg", None)
    if msg:
        {"sucesso": st.success, "erro": st.error, "aviso": st.warning}.get(msg["tipo"], st.info)(msg["texto"])
    erro = st.session_state.pop("proc_erro", None)
    if erro:
        with st.expander("Ver detalhes do erro"):
            st.code(erro)

    if repo_funcionario.contar() == 0:
        st.warning("⚠️ Nenhum funcionário cadastrado. Importe o cadastro em **👥 Funcionários** antes de começar.")

    # ===== PASSO 1: processo =====
    st.markdown("### 1️⃣ Processo do mês")
    andamento = repo_processo.listar_processos(status="EM_ANDAMENTO")
    opcoes = {f"[{p['empresa']}] {p['mes_referencia']} · {p['descricao'] or 'sem descrição'} (#{p['id']})": p["id"] for p in andamento}
    col1, col2 = st.columns([3, 1])
    with col1:
        escolha = st.selectbox("Selecione um processo em andamento", ["— selecione —"] + list(opcoes.keys())) \
            if opcoes else st.selectbox("Processo", ["— nenhum aberto —"], disabled=True)
        pid = opcoes.get(escolha)
    with col2:
        with st.popover("➕ Novo"):
            with st.form("novo_proc", clear_on_submit=True):
                hoje = date.today()
                empresa_nova = st.selectbox("Empresa", EMPRESAS, key="nova_emp")
                mes = st.text_input("Mês de referência (AAAA-MM)", value=f"{hoje.year}-{hoje.month:02d}")
                desc = st.text_input("Descrição (opcional)")
                if st.form_submit_button("Criar processo", type="primary"):
                    try:
                        npid = repo_processo.criar_processo(mes, desc, usuario, empresa_nova)
                        auditoria.registrar(usuario, "PROCESSAR", entidade_id=npid, detalhes=f"Criou {mes}")
                        _msg("sucesso", f"✅ Processo {mes} criado. Selecione-o acima para continuar.")
                    except Exception as e:
                        _msg("erro", f"❌ {e}")
                    st.rerun()

    if not pid:
        st.info("Selecione (ou crie) um processo para continuar o passo a passo.")
        return

    processo = repo_processo.buscar_processo(pid)
    emp = processo["empresa"]
    st.success(f"🏢 Empresa deste processo: **{emp}** · mês {processo['mes_referencia']}")
    uploads = {u["tipo"]: u for u in repo_processo.listar_uploads(pid)}
    faltas = repo_processo.listar_faltas(pid)
    ferias = repo_processo.listar_ferias(pid)

    # ===== PASSO 2: planilhas =====
    st.divider()
    st.markdown(f"### 2️⃣ Enviar planilhas {_status('FALTAS' in uploads or 'ATESTADOS' in uploads)}")
    cfa, cat, cfe = st.columns(3)
    with cfa:
        st.markdown(f"**Faltas** {_status('FALTAS' in uploads)}")
        if "FALTAS" in uploads:
            st.caption(f"{len(faltas)} c/ falta ou atraso")
        af = st.file_uploader("Faltas (Pontotel)", type=["xls", "xlsx", "csv"], key=f"af_{pid}", label_visibility="collapsed")
        if af is not None and st.button("📥 Enviar faltas", key=f"baf_{pid}"):
            with st.spinner("Lendo e gravando faltas…"):
                _processar_faltas(usuario, pid, af, emp)
            st.rerun()
    with cat:
        st.markdown(f"**Atestados** {_status('ATESTADOS' in uploads)}")
        if "ATESTADOS" in uploads:
            st.caption(f"{len(repo_processo.listar_atestados(pid))} pessoa(s)")
        at = st.file_uploader("Atestados", type=["xlsx", "xls", "csv"], key=f"at_{pid}", label_visibility="collapsed")
        if at is not None and st.button("📥 Enviar atestados", key=f"bat_{pid}"):
            with st.spinner("Lendo e gravando atestados…"):
                _processar_atestados(usuario, pid, at, emp)
            st.rerun()
    with cfe:
        st.markdown(f"**Férias (PDF)** {_status('FERIAS' in uploads)}")
        if "FERIAS" in uploads:
            st.caption(f"{len(ferias)} pessoa(s)")
        fe = st.file_uploader("Férias (PDF)", type=["pdf"], key=f"fe_{pid}", label_visibility="collapsed")
        if fe is not None and st.button("📥 Enviar férias", key=f"bfe_{pid}"):
            with st.spinner("Lendo o PDF e gravando férias…"):
                _processar_ferias(usuario, pid, fe, emp)
            st.rerun()

    # ===== PASSO 3: revisar faltas =====
    st.divider()
    st.markdown(f"### 3️⃣ Revisar faltas {_status(bool(faltas))}")
    # Mostra só quem realmente pode ser descontado: atraso >= 30 min OU falta de dia.
    # Atrasos menores que 30 min não geram desconto, então não precisam de revisão.
    faltas_rev = [f for f in faltas if f["atraso_min"] >= 30 or f["faltas_dias"] > 0]
    ocultos = len(faltas) - len(faltas_rev)
    if not faltas:
        st.caption("Envie a planilha de faltas no passo 2 para revisar aqui.")
    elif not faltas_rev:
        st.caption(f"Ninguém com 30 min de atraso ou falta de dia. "
                   f"({ocultos} com atraso menor que 30 min — não descontam, ocultados.)")
    else:
        incl = sum(1 for f in faltas_rev if f["incluir"])
        legenda = f"Marcar/desmarcar quem entra no cálculo ({incl} de {len(faltas_rev)} marcados)"
        with st.expander(legenda, expanded=False):
            st.caption("Mostrando só quem tem **30 min de atraso ou mais** (ou falta de dia). "
                       "Desmarcado = recebe **integral**. Atestados entram automaticamente."
                       + (f" {ocultos} pessoa(s) com atraso < 30 min foram ocultadas." if ocultos else ""))
            ca, cb = st.columns(2)
            if ca.button("✓ Marcar todos", key=f"mt_{pid}"):
                repo_processo.definir_inclusao_lote(pid, {f["codigo"]: True for f in faltas_rev}); st.rerun()
            if cb.button("✗ Desmarcar todos", key=f"dt_{pid}"):
                repo_processo.definir_inclusao_lote(pid, {f["codigo"]: False for f in faltas_rev}); st.rerun()
            with st.form(f"rev_{pid}"):
                marc = {}
                for f in faltas_rev:
                    h = int(f["atraso_min"] // 60); m = int(f["atraso_min"] % 60)
                    marc[f["codigo"]] = st.checkbox(
                        f"{f['nome']} — {f['faltas_dias']:g} falta(s), atraso {h}h{m:02d}",
                        value=bool(f["incluir"]), key=f"chk_{pid}_{f['codigo']}")
                if st.form_submit_button("💾 Salvar seleção de faltas", type="primary"):
                    with st.spinner("Salvando seleção…"):
                        repo_processo.definir_inclusao_lote(pid, marc)
                    _msg("sucesso", "✅ Seleção de faltas salva."); st.rerun()

    # ===== PASSO 4: revisar férias =====
    st.divider()
    st.markdown(f"### 4️⃣ Revisar férias {_status(bool(ferias))}")
    if not ferias:
        st.caption("Envie o PDF de férias no passo 2 para revisar aqui.")
    else:
        incl = sum(1 for f in ferias if f["incluir"])
        with st.expander(f"Marcar/desmarcar quem está de férias ({incl} de {len(ferias)} marcados = zeram)", expanded=False):
            st.caption("Marcado = está de férias e **zera** o mês. Desmarque quem deve receber normalmente.")
            ca, cb = st.columns(2)
            if ca.button("✓ Marcar todos", key=f"mtf_{pid}"):
                repo_processo.definir_inclusao_ferias_lote(pid, {f["codigo"]: True for f in ferias}); st.rerun()
            if cb.button("✗ Desmarcar todos", key=f"dtf_{pid}"):
                repo_processo.definir_inclusao_ferias_lote(pid, {f["codigo"]: False for f in ferias}); st.rerun()
            with st.form(f"revf_{pid}"):
                marc = {}
                for f in ferias:
                    marc[f["codigo"]] = st.checkbox(
                        f"{f['nome']} — férias {f['periodo_gozo'] or ''} ({f['dias']:g} dias)",
                        value=bool(f["incluir"]), key=f"chkf_{pid}_{f['codigo']}")
                if st.form_submit_button("💾 Salvar seleção de férias", type="primary"):
                    with st.spinner("Salvando seleção…"):
                        repo_processo.definir_inclusao_ferias_lote(pid, marc)
                    _msg("sucesso", "✅ Seleção de férias salva."); st.rerun()

    # ===== PASSO 5: calcular =====
    st.divider()
    tem_result = repo_processo.tem_resultados(pid)
    st.markdown(f"### 5️⃣ Calcular {_status(tem_result)}")
    if st.button("🧮 Calcular resultado", type="primary", key=f"calc_{pid}"):
        with st.spinner("Calculando o benefício de todos os funcionários…"):
            _calcular(usuario, pid, emp)
        st.rerun()
    if tem_result:
        res = [dict(r) for r in repo_processo.listar_resultados(pid)]
        with st.expander("Ver prévia do resultado", expanded=False):
            df = pd.DataFrame([{"Código": r["codigo"], "Nome": r["nome"], "Faixa": r["faixa_alim"],
                                "Prêmio": fmt_real(r["valor_base"]), "% Desc.": fmt_pct(r["pct_desconto"]),
                                "Final": fmt_real(r["valor_final"])} for r in res])
            st.dataframe(df, use_container_width=True, hide_index=True)
        try:
            st.download_button("⬇️ Baixar conferência (.xlsx interno)", data=gerar_xlsx_resultado(dict(processo), res),
                               file_name=f"conferencia_{processo['mes_referencia']}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dlc_{pid}")
        except Exception as e:
            st.caption(f"(conferência indisponível: {e})")

    # ===== PASSO 6: gerar Sodexo =====
    st.divider()
    st.markdown(f"### 6️⃣ Gerar planilha da Sodexo {_status(bool(st.session_state.get(f'sodexo_bytes_{pid}')))}")
    if not tem_result:
        st.caption("Calcule o resultado (passo 5) para liberar a geração.")
    else:
        _gerar_sodexo(usuario, processo, [dict(r) for r in repo_processo.listar_resultados(pid)])

    # ===== PASSO 7: finalizar =====
    st.divider()
    st.markdown(f"### 7️⃣ Finalizar {_status(processo['status'] == 'FINALIZADO')}")
    if processo["status"] == "FINALIZADO":
        st.success("Processo finalizado. (Você pode reabrir em 📁 Processos.)")
    else:
        if st.button("✅ Finalizar processo", type="primary", key=f"fin_{pid}", disabled=not tem_result):
            repo_processo.finalizar(pid)
            auditoria.registrar(usuario, "FINALIZAR_PROCESSO", entidade_id=pid)
            _msg("sucesso", "✅ Processo finalizado."); st.rerun()
        if pode_excluir(usuario):
            with st.expander("🗑 Excluir este processo"):
                confirmar_exclusao_com_senha(usuario, f"del_{pid}", f"processo {processo['mes_referencia']}",
                                             lambda i=pid: _excluir(usuario, i), "Excluir processo")


def _gerar_sodexo(usuario, processo, resultados):
    pid = processo["id"]
    emp = processo["empresa"]
    modelo = repo_sodexo.modelo_ativo(emp)
    st.caption(f"Gerando a Sodexo da empresa **{emp}**.")
    fonte = st.radio("Planilha-base", ["Usar modelo guardado", "Subir uma agora"],
                     key=f"fonte_{pid}", horizontal=True)
    conteudo = None
    if fonte == "Usar modelo guardado":
        if modelo:
            st.caption(f"Modelo ({emp}): {modelo['nome_arquivo']} ({modelo['total_beneficiarios']} benef.)")
            conteudo = repo_sodexo.conteudo_ativo(emp)
        else:
            st.warning(f"Não há modelo guardado para **{emp}**. Suba um em **📤 Modelo Sodexo** ou escolha 'Subir uma agora'.")
    else:
        up = st.file_uploader("Planilha da Sodexo (.xlsx)", type=["xlsx"], key=f"sdx_up_{pid}")
        if up is not None:
            conteudo = up.getvalue()

    st.caption("Preencha as 3 datas antes de gerar:")
    c1, c2, c3 = st.columns(3)
    d_cred = c1.date_input("Data de crédito", value=date.today(), key=f"dc_{pid}", format="DD/MM/YYYY")
    d_ent = c2.date_input("Data de entrega", value=date.today(), key=f"de_{pid}", format="DD/MM/YYYY")
    d_mes = c3.date_input("Mês de referência", value=date.today().replace(day=1), key=f"dm_{pid}", format="DD/MM/YYYY")

    if st.button("📤 Gerar planilha Sodexo", type="primary", key=f"gsdx_{pid}", disabled=conteudo is None):
        try:
            with st.spinner("Preenchendo a planilha da Sodexo…"):
                r = preencher_sodexo(conteudo, resultados, repo_tabela.mapa_valor_por_faixa(), d_cred, d_ent, d_mes)
            auditoria.registrar(usuario, "GERAR_PLANILHA_SAIDA", entidade_id=pid,
                                detalhes=f"{r['preenchidos']} preench., {r['zerados']} zerados")
            st.session_state[f"sodexo_bytes_{pid}"] = r["bytes"]
            txt = (f"✅ Gerada: {r['preenchidos']} preenchido(s), {r['zerados']} zerado(s) em vermelho, "
                   f"{r['excecoes']} exceção(ões) mantida(s).")
            if r["avisos"]:
                txt += "\n\n⚠️ " + "\n⚠️ ".join(r["avisos"])
            _msg("sucesso", txt); st.rerun()
        except Exception as e:
            import traceback; _msg("erro", f"❌ {e}", traceback.format_exc()); st.rerun()

    if st.session_state.get(f"sodexo_bytes_{pid}"):
        st.download_button("⬇️ Baixar planilha Sodexo preenchida", data=st.session_state[f"sodexo_bytes_{pid}"],
                           file_name=f"sodexo_{processo['mes_referencia']}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key=f"dlsdx_{pid}", type="primary")


# ---------- processamento dos uploads ----------
def _processar_faltas(usuario, pid, arq, empresa=""):
    try:
        h = hashlib.md5(arq.getvalue()).hexdigest()
        res = ler_planilha_faltas(arq)
        idx = _indice_cadastro(empresa)
        itens, nao_lig = [], 0
        for p in res["pessoas"]:
            fu = idx.localizar(matricula_pontotel=p["codigo"], cpf=p["cpf"])
            if not fu:
                nao_lig += 1
            itens.append({"codigo": fu["codigo"] if fu else (p["codigo"] or p["cpf"]),
                          "cpf": p["cpf"], "nome": p["nome"],
                          "atraso_min": p["atraso_min"], "faltas_dias": p["faltas_dias"]})
        repo_processo.substituir_faltas(pid, itens)
        repo_processo.registrar_upload(pid, "FALTAS", arq.name, h, res["total_linhas"], usuario)
        auditoria.registrar(usuario, "UPLOAD_PONTO", entidade_id=pid, detalhes=f"{len(itens)} faltas")
        txt = f"✅ Faltas: {len(itens)} pessoa(s) com falta/atraso."
        if nao_lig:
            txt += f" ⚠️ {nao_lig} não ligaram ao cadastro."
        _msg("sucesso", txt)
    except ValueError as e:
        _msg("erro", f"❌ {e}")
    except Exception as e:
        import traceback; _msg("erro", f"❌ {type(e).__name__}: {e}", traceback.format_exc())


def _processar_atestados(usuario, pid, arq, empresa=""):
    try:
        h = hashlib.md5(arq.getvalue()).hexdigest()
        res = ler_planilha_atestados(arq)
        idx = _indice_cadastro(empresa)
        itens = []
        for p in res["pessoas"]:
            fu = idx.localizar(matricula_pontotel=p["matricula"])
            itens.append({"codigo": fu["codigo"] if fu else p["matricula"], "matricula": p["matricula"],
                          "nome": p["nome"], "dias": p["dias"], "indeterminado": p["indeterminado"], "tipos": p["tipos"]})
        repo_processo.substituir_atestados(pid, itens)
        repo_processo.registrar_upload(pid, "ATESTADOS", arq.name, h, res["total_linhas"], usuario)
        auditoria.registrar(usuario, "UPLOAD_PONTO", entidade_id=pid, detalhes=f"{len(itens)} atestados")
        txt = f"✅ Atestados: {len(itens)} pessoa(s)."
        if res["avisos"]:
            txt += "\n\n⚠️ " + "\n⚠️ ".join(res["avisos"][:6])
        _msg("sucesso", txt)
    except ValueError as e:
        _msg("erro", f"❌ {e}")
    except Exception as e:
        import traceback; _msg("erro", f"❌ {type(e).__name__}: {e}", traceback.format_exc())


def _processar_ferias(usuario, pid, arq, empresa=""):
    try:
        h = hashlib.md5(arq.getvalue()).hexdigest()
        res = ler_planilha_ferias(arq)
        idx = _indice_cadastro(empresa)
        itens, nao_lig = [], 0
        for p in res["pessoas"]:
            fu = idx.localizar(matricula_pontotel=p["codigo"]) or idx.localizar_por_nome(p["nome"])
            if not fu:
                nao_lig += 1
            itens.append({"codigo": fu["codigo"] if fu else p["codigo"],
                          "nome": fu["nome"] if fu else p["nome"],
                          "periodo_gozo": p["periodo_gozo"], "dias": p["dias"]})
        repo_processo.substituir_ferias(pid, itens)
        repo_processo.registrar_upload(pid, "FERIAS", arq.name, h, res["total"], usuario)
        auditoria.registrar(usuario, "UPLOAD_PONTO", entidade_id=pid, detalhes=f"{len(itens)} férias")
        txt = f"✅ Férias: {len(itens)} pessoa(s)."
        if nao_lig:
            txt += f" ⚠️ {nao_lig} não ligaram ao cadastro (ex.: admissão nova)."
        _msg("sucesso", txt)
    except ValueError as e:
        _msg("erro", f"❌ {e}")
    except Exception as e:
        import traceback; _msg("erro", f"❌ {type(e).__name__}: {e}", traceback.format_exc())


def _calcular(usuario, pid, empresa=""):
    try:
        funcs = repo_funcionario.todos_para_calculo(empresa)
        if not funcs:
            _msg("aviso", "⚠️ Importe o cadastro de funcionários primeiro."); return
        faltas = {str(f["codigo"]): {"atraso_min": f["atraso_min"], "faltas_dias": f["faltas_dias"]}
                  for f in repo_processo.listar_faltas(pid)}
        atest = {str(a["codigo"]): {"dias": a["dias"], "indeterminado": bool(a["indeterminado"])}
                 for a in repo_processo.listar_atestados(pid)}
        calc = calcular_processo(funcs, faltas, atest, repo_tabela.mapa_valor_por_faixa(),
                                 incluidos=repo_processo.codigos_incluidos(pid),
                                 ferias_incluidos=repo_processo.codigos_ferias_incluidos(pid))
        repo_processo.substituir_resultados(pid, calc["resultados"])
        t = calc["totais"]
        repo_processo.atualizar_totais(pid, t["total_funcionarios"], t["valor_premios"], t["valor_descontos"], t["valor_liquido"])
        auditoria.registrar(usuario, "PROCESSAR", entidade_id=pid, detalhes=f"{t['total_funcionarios']} func.")
        txt = (f"✅ Calculado: {t['total_funcionarios']} func., {t['integrais']} integrais, "
               f"{t['zerados']} zerados ({t.get('ferias',0)} por férias). Líquido {fmt_real(t['valor_liquido'])}.")
        if calc["avisos"]:
            txt += "\n\n⚠️ " + "\n⚠️ ".join(calc["avisos"][:6])
        _msg("sucesso", txt)
    except Exception as e:
        import traceback; _msg("erro", f"❌ {type(e).__name__}: {e}", traceback.format_exc())


def _excluir(usuario, pid):
    repo_processo.excluir_processo(pid)
    auditoria.registrar(usuario, "EXCLUIR_PROCESSO", entidade_id=pid)
