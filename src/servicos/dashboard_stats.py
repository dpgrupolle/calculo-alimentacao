"""Estatísticas do dashboard, com escopo por empresa (GERAL / PISA / KING)."""
from __future__ import annotations
from typing import Optional, List
from src.banco.conexao import obter_conexao

FAIXAS = [
    (100, 100, "100% (integral)"), (75, 99.99, "75–99%"), (50, 74.99, "50–74%"),
    (25, 49.99, "25–49%"), (0.01, 24.99, "1–24%"), (0, 0, "0% (zerado)"),
]


def _filtro_emp(empresa):
    return (" AND empresa = ?", [empresa]) if empresa else ("", [])


def _in(pids):
    """Monta cláusula 'processo_id IN (?,?,..)' + params. pids vazio → impossível (1=0)."""
    if not pids:
        return "1=0", []
    return f"processo_id IN ({','.join('?' for _ in pids)})", list(pids)


def empresas_com_dados() -> List[str]:
    rows = obter_conexao().execute(
        "SELECT DISTINCT empresa FROM processo WHERE empresa IS NOT NULL AND empresa<>'' ORDER BY empresa;").fetchall()
    return [r["empresa"] for r in rows]


def escopo(empresa: str = "") -> dict:
    """
    Define o escopo do dashboard para a empresa (vazio = GERAL):
    mês atual e anterior + os processos (pids) de cada um.
    """
    conn = obter_conexao(); fe, pe = _filtro_emp(empresa)
    meses = [r["mes_referencia"] for r in conn.execute(
        f"SELECT DISTINCT mes_referencia FROM processo WHERE 1=1{fe} "
        "ORDER BY mes_referencia DESC LIMIT 2;", pe).fetchall()]
    def pids(mes):
        if mes is None: return []
        return [r["id"] for r in conn.execute(
            f"SELECT id FROM processo WHERE mes_referencia=?{fe};", [mes] + pe).fetchall()]
    mes_a = meses[0] if meses else None
    mes_b = meses[1] if len(meses) > 1 else None
    return {"mes_atual": mes_a, "mes_anterior": mes_b,
            "pids_atual": pids(mes_a), "pids_anterior": pids(mes_b)}


def kpis(pids: list) -> dict:
    cl, pr = _in(pids)
    r = obter_conexao().execute(
        "SELECT COUNT(*) n, COALESCE(SUM(valor_base),0) premios, "
        "COALESCE(SUM(valor_base-valor_final),0) descontos, COALESCE(SUM(valor_final),0) liquido, "
        "COALESCE(AVG(pct_recebido),0) pmedio, "
        "COALESCE(SUM(CASE WHEN pct_recebido>=100 THEN 1 ELSE 0 END),0) integrais, "
        "COALESCE(SUM(CASE WHEN valor_final<=0 AND valor_base>0 THEN 1 ELSE 0 END),0) zerados "
        f"FROM resultado_beneficio WHERE {cl};", pr).fetchone()
    return {"total_funcionarios": int(r["n"]), "valor_premios": float(r["premios"]),
            "valor_descontos": float(r["descontos"]), "valor_liquido": float(r["liquido"]),
            "pct_medio": float(r["pmedio"]), "integrais": int(r["integrais"]), "zerados": int(r["zerados"])}


def distribuicao_faixas(pids: list) -> dict:
    cl, pr = _in(pids)
    rows = obter_conexao().execute(
        f"SELECT pct_recebido FROM resultado_beneficio WHERE {cl};", pr).fetchall()
    out = {rot: 0 for _, _, rot in FAIXAS}
    for row in rows:
        p = float(row["pct_recebido"])
        for lo, hi, rot in FAIXAS:
            if lo <= p <= hi:
                out[rot] += 1; break
    return out


def valor_por_faixa(pids: list) -> list:
    cl, pr = _in(pids)
    rows = obter_conexao().execute(
        "SELECT faixa_alim, COUNT(*) n, COALESCE(SUM(valor_final),0) v FROM resultado_beneficio "
        f"WHERE {cl} GROUP BY faixa_alim ORDER BY faixa_alim;", pr).fetchall()
    return [{"faixa": r["faixa_alim"], "n": int(r["n"]), "valor": float(r["v"])} for r in rows]


def indicador_por_departamento(pids: list) -> list:
    cl, pr = _in(pids)
    rows = obter_conexao().execute(
        "SELECT COALESCE(NULLIF(departamento,''),'(sem departamento)') dep, COUNT(*) n, "
        "COALESCE(SUM(valor_final),0) liquido, COALESCE(SUM(valor_base),0) base "
        f"FROM resultado_beneficio WHERE {cl} GROUP BY dep ORDER BY liquido DESC;", pr).fetchall()
    return [{"departamento": r["dep"], "n": int(r["n"]), "liquido": float(r["liquido"]),
             "base": float(r["base"])} for r in rows]


def por_empresa(pids: list) -> list:
    """Resumo por empresa (para a visão GERAL): líquido e nº por empresa."""
    cl, pr = _in(pids)
    rows = obter_conexao().execute(
        "SELECT empresa, COUNT(*) n, COALESCE(SUM(valor_final),0) liquido "
        f"FROM resultado_beneficio WHERE {cl} GROUP BY empresa ORDER BY liquido DESC;", pr).fetchall()
    return [{"empresa": r["empresa"] or "—", "n": int(r["n"]), "liquido": float(r["liquido"])} for r in rows]


def _delta(atual, anterior):
    d = atual - anterior
    pct = (d / anterior * 100) if anterior else (100.0 if atual else 0.0)
    return {"valor": round(d, 2), "pct": round(pct, 1),
            "direcao": "alta" if d > 0.005 else ("baixa" if d < -0.005 else "igual")}


def comparativo_mes_a_mes(esc: dict) -> Optional[dict]:
    if not esc["pids_atual"]:
        return None
    ka = kpis(esc["pids_atual"])
    out = {"mes_atual": esc["mes_atual"], "kpis_atual": ka,
           "tem_anterior": bool(esc["pids_anterior"])}
    if esc["pids_anterior"]:
        kb = kpis(esc["pids_anterior"])
        out.update({"mes_anterior": esc["mes_anterior"], "kpis_anterior": kb,
                    "delta_liquido": _delta(ka["valor_liquido"], kb["valor_liquido"]),
                    "delta_func": _delta(ka["total_funcionarios"], kb["total_funcionarios"]),
                    "delta_zerados": _delta(ka["zerados"], kb["zerados"]),
                    "delta_descontos": _delta(ka["valor_descontos"], kb["valor_descontos"])})
    return out


def evolucao_por_departamento(esc: dict) -> Optional[list]:
    if not (esc["pids_atual"] and esc["pids_anterior"]):
        return None
    a = {d["departamento"]: d["liquido"] for d in indicador_por_departamento(esc["pids_atual"])}
    b = {d["departamento"]: d["liquido"] for d in indicador_por_departamento(esc["pids_anterior"])}
    out = [{"departamento": dep, "atual": a.get(dep, 0.0), "anterior": b.get(dep, 0.0),
            **_delta(a.get(dep, 0.0), b.get(dep, 0.0))} for dep in sorted(set(a) | set(b))]
    out.sort(key=lambda x: abs(x["valor"]), reverse=True)
    return out


def comparativo_por_funcionario(esc: dict) -> Optional[dict]:
    if not (esc["pids_atual"] and esc["pids_anterior"]):
        return None
    conn = obter_conexao()
    def mapa(pids):
        cl, pr = _in(pids)
        rows = conn.execute("SELECT codigo, nome, departamento, empresa, "
                            f"COALESCE(SUM(valor_final),0) v FROM resultado_beneficio WHERE {cl} "
                            "GROUP BY codigo, nome, departamento, empresa;", pr).fetchall()
        return {str(r["codigo"]): r for r in rows}
    atual, anterior = mapa(esc["pids_atual"]), mapa(esc["pids_anterior"])
    linhas = []
    for cod in set(atual) | set(anterior):
        ra, rb = atual.get(cod), anterior.get(cod)
        va = float(ra["v"]) if ra else None
        vb = float(rb["v"]) if rb else None
        base = ra or rb
        if ra and not rb: status, delta = "novo", (va or 0)
        elif rb and not ra: status, delta = "saiu", -(vb or 0)
        else:
            delta = round(va - vb, 2)
            status = "alta" if delta > 0.005 else ("baixa" if delta < -0.005 else "igual")
        linhas.append({"codigo": cod, "nome": base["nome"], "departamento": base["departamento"] or "—",
                       "empresa": base["empresa"] or "—", "anterior": vb, "atual": va,
                       "delta": delta, "status": status})
    linhas.sort(key=lambda x: abs(x["delta"] or 0), reverse=True)
    resumo = {s: sum(1 for l in linhas if l["status"] == s) for s in ("alta", "baixa", "igual", "novo", "saiu")}
    return {"mes_atual": esc["mes_atual"], "mes_anterior": esc["mes_anterior"],
            "linhas": linhas, "resumo": resumo}


def tendencia_mensal(empresa: str = "", limite: int = 6) -> list:
    fe, pe = _filtro_emp(empresa)
    rows = obter_conexao().execute(
        f"SELECT mes_referencia, COALESCE(SUM(valor_total_liquido),0) liq FROM processo "
        f"WHERE status='FINALIZADO'{fe} GROUP BY mes_referencia "
        "ORDER BY mes_referencia DESC LIMIT ?;", pe + [limite]).fetchall()
    dados = [{"mes": r["mes_referencia"], "liquido": float(r["liq"])} for r in rows]
    return list(reversed(dados))


def contar_processos(empresa: str = "") -> dict:
    fe, pe = _filtro_emp(empresa)
    r = obter_conexao().execute(
        "SELECT COUNT(*) total, COALESCE(SUM(CASE WHEN status='FINALIZADO' THEN 1 ELSE 0 END),0) fin "
        f"FROM processo WHERE 1=1{fe};", pe).fetchone()
    return {"total": int(r["total"]), "finalizados": int(r["fin"])}
