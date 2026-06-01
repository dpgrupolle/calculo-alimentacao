"""Dashboard — Gestão de Benefícios DP/RH, com escopo por empresa (GERAL/PISA/KING)."""
from __future__ import annotations
import streamlit as st
from src.utils.marca import AZUL_ESCURO, COR_EMPRESA
from src.utils.estilo import (card_kpi, fmt_real, fmt_pct,
                              COR_AZUL, COR_VERDE, COR_LARANJA, COR_VERMELHO, COR_CINZA, COR_AMARELO)
from src.servicos import dashboard_stats as stats


def _plotly():
    try:
        import plotly.graph_objects as go
        return go
    except Exception:
        return None


def renderizar_inicio(usuario):
    nome = usuario.nome.split()[0] if usuario.nome else "usuário"
    st.markdown(f"<h1 style='color:{AZUL_ESCURO};margin-bottom:2px;'>Olá, {nome}! 👋</h1>", unsafe_allow_html=True)
    st.caption("Painel — Vale Alimentação (prêmio por assiduidade) · DP/RH")

    # Seletor de empresa (GERAL + empresas com dados)
    empresas = stats.empresas_com_dados()
    opcoes = ["GERAL"] + empresas
    escolha = st.radio("Empresa", opcoes, horizontal=True, key="dash_emp") if len(opcoes) > 1 else "GERAL"
    empresa = "" if escolha == "GERAL" else escolha

    esc = stats.escopo(empresa)
    if not esc["pids_atual"]:
        st.info("👋 Ainda não há processos calculados para este escopo. Comece em **⚙️ Processar benefício**.")
        return

    rotulo = "Geral (todas as empresas)" if not empresa else f"Empresa: {empresa}"
    st.markdown(f"<div style='color:#666;margin:6px 0;'>Mês: <b>{esc['mes_atual']}</b> · {rotulo}</div>",
                unsafe_allow_html=True)

    go = _plotly()
    k = stats.kpis(esc["pids_atual"])
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(card_kpi("Funcionários", str(k["total_funcionarios"]),
                f"{k['integrais']} integrais · {k['zerados']} zerados", COR_AZUL, "👥"), unsafe_allow_html=True)
    c2.markdown(card_kpi("Prêmio cheio", fmt_real(k["valor_premios"]), "Soma das faixas", COR_CINZA, "🎯"), unsafe_allow_html=True)
    c3.markdown(card_kpi("Descontado", fmt_real(k["valor_descontos"]), "Faltas/atestados/férias", COR_LARANJA, "✂️"), unsafe_allow_html=True)
    c4.markdown(card_kpi("Líquido a creditar", fmt_real(k["valor_liquido"]),
                f"% médio: {fmt_pct(k['pct_medio'])}", COR_VERDE, "💳"), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Visão GERAL: comparação entre empresas (cores por empresa)
    if not empresa:
        pe = stats.por_empresa(esc["pids_atual"])
        if len(pe) > 1:
            st.markdown("##### 🏢 Comparativo entre empresas")
            ce, cd = st.columns([2, 3])
            with ce:
                for e in pe:
                    cor = COR_EMPRESA.get(e["empresa"], COR_AZUL)
                    st.markdown(card_kpi(e["empresa"], fmt_real(e["liquido"]),
                                f"{e['n']} funcionários", cor, "🏢"), unsafe_allow_html=True)
            with cd:
                if go:
                    fig = go.Figure(go.Bar(
                        x=[e["empresa"] for e in pe], y=[e["liquido"] for e in pe],
                        marker_color=[COR_EMPRESA.get(e["empresa"], COR_AZUL) for e in pe],
                        text=[fmt_real(e["liquido"]) for e in pe], textposition="auto"))
                    fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10),
                                      yaxis_title="Líquido (R$)", plot_bgcolor="white")
                    st.plotly_chart(fig, use_container_width=True)
            st.markdown("---")

    ce, cd = st.columns(2)
    with ce:
        st.markdown("##### 📊 Distribuição do prêmio recebido")
        dist = stats.distribuicao_faixas(esc["pids_atual"])
        if sum(dist.values()) == 0:
            st.caption("Sem resultados.")
        elif go:
            cores = [COR_VERDE, "#5BA85B", COR_AMARELO, COR_LARANJA, "#E8743B", COR_VERMELHO]
            rot = list(dist.keys()); val = list(dist.values())
            fig = go.Figure(go.Bar(x=val, y=rot, orientation="h", marker_color=cores[:len(rot)],
                                   text=val, textposition="auto"))
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                              xaxis_title="Funcionários", yaxis=dict(autorange="reversed"), plot_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(dist)
    with cd:
        st.markdown("##### 💰 Líquido por faixa")
        vpf = stats.valor_por_faixa(esc["pids_atual"])
        if not vpf:
            st.caption("Sem resultados.")
        elif go:
            rot = [f"Faixa {v['faixa']}" for v in vpf]; val = [v["valor"] for v in vpf]
            fig = go.Figure(go.Bar(x=rot, y=val, marker_color=COR_AZUL,
                                   text=[fmt_real(v) for v in val], textposition="auto"))
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="R$", plot_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart({f"Faixa {v['faixa']}": v["valor"] for v in vpf})

    # Comparativo mês a mês
    comp = stats.comparativo_mes_a_mes(esc)
    if comp and comp.get("tem_anterior"):
        st.markdown("---")
        st.markdown(f"##### 📅 Comparativo mês a mês — {comp['mes_atual']} vs {comp['mes_anterior']}")
        ka = comp["kpis_atual"]; dl = comp["delta_liquido"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Líquido", fmt_real(ka["valor_liquido"]), f"{fmt_real(dl['valor'])} ({dl['pct']:+.1f}%)")
        m2.metric("Funcionários", ka["total_funcionarios"], f"{comp['delta_func']['valor']:+.0f}")
        m3.metric("Zerados", ka["zerados"], f"{comp['delta_zerados']['valor']:+.0f}", delta_color="inverse")
        m4.metric("Descontado", fmt_real(ka["valor_descontos"]), fmt_real(comp['delta_descontos']['valor']), delta_color="inverse")

    # Por departamento
    st.markdown("---")
    st.markdown("##### 🏢 Por departamento")
    deps = stats.indicador_por_departamento(esc["pids_atual"])
    if not deps:
        st.caption("Sem resultados.")
    else:
        cesq, cdir = st.columns([3, 2])
        with cesq:
            if go:
                top = deps[:15]
                fig = go.Figure(go.Bar(x=[d["liquido"] for d in top], y=[d["departamento"] for d in top],
                                       orientation="h", marker_color=COR_AZUL,
                                       text=[fmt_real(d["liquido"]) for d in top], textposition="auto"))
                fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10),
                                  xaxis_title="Líquido (R$)", yaxis=dict(autorange="reversed"), plot_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.bar_chart({d["departamento"]: d["liquido"] for d in deps})
        with cdir:
            evol = stats.evolucao_por_departamento(esc)
            if not evol:
                st.caption("A evolução aparece quando houver mês anterior.")
            else:
                import pandas as pd
                seta = {"alta": "🔺", "baixa": "🔻", "igual": "➖"}
                df = pd.DataFrame([{"Departamento": e["departamento"], "Mês ant.": fmt_real(e["anterior"]),
                                    "Mês atual": fmt_real(e["atual"]),
                                    "Variação": f"{seta[e['direcao']]} {fmt_real(e['valor'])}"} for e in evol[:12]])
                st.dataframe(df, use_container_width=True, hide_index=True)

    # Evolução por funcionário
    cf = stats.comparativo_por_funcionario(esc)
    if cf:
        st.markdown("---")
        st.markdown(f"##### 👤 Evolução por funcionário — {cf['mes_atual']} vs {cf['mes_anterior']}")
        r = cf["resumo"]
        cols = st.columns(5)
        cols[0].markdown(card_kpi("Subiram", str(r["alta"]), "recebem mais", COR_VERDE, "🔺"), unsafe_allow_html=True)
        cols[1].markdown(card_kpi("Caíram", str(r["baixa"]), "recebem menos", COR_VERMELHO, "🔻"), unsafe_allow_html=True)
        cols[2].markdown(card_kpi("Iguais", str(r["igual"]), "sem mudança", COR_CINZA, "➖"), unsafe_allow_html=True)
        cols[3].markdown(card_kpi("Novos", str(r["novo"]), "entraram", COR_AZUL, "✨"), unsafe_allow_html=True)
        cols[4].markdown(card_kpi("Saíram", str(r["saiu"]), "fora do mês", COR_LARANJA, "👋"), unsafe_allow_html=True)
        movers = [l for l in cf["linhas"] if l["status"] in ("alta", "baixa", "novo", "saiu")]
        if movers:
            import pandas as pd
            seta = {"alta": "🔺", "baixa": "🔻", "novo": "✨", "saiu": "👋", "igual": "➖"}
            with st.expander(f"Ver quem mudou ({len(movers)})", expanded=False):
                df = pd.DataFrame([{"Funcionário": l["nome"], "Empresa": l["empresa"], "Depto": l["departamento"],
                                    "Mês ant.": fmt_real(l["anterior"]) if l["anterior"] is not None else "—",
                                    "Mês atual": fmt_real(l["atual"]) if l["atual"] is not None else "—",
                                    "Variação": f"{seta[l['status']]} {fmt_real(l['delta'])}"} for l in movers])
                st.dataframe(df, use_container_width=True, hide_index=True)

    # Tendência mensal
    st.markdown("##### 📈 Tendência mensal (líquido creditado)")
    tend = stats.tendencia_mensal(empresa)
    if not tend:
        st.caption("Finalize processos para ver a evolução.")
    elif go:
        cor = COR_EMPRESA.get(empresa, COR_VERDE) if empresa else COR_VERDE
        fig = go.Figure(go.Scatter(x=[t["mes"] for t in tend], y=[t["liquido"] for t in tend],
                                   mode="lines+markers", line=dict(color=cor, width=3), fill="tozeroy"))
        fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="R$", plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.line_chart({t["mes"]: t["liquido"] for t in tend})
