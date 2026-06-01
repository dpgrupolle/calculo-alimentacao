"""
Motor de cálculo do benefício — regras definidas pelo Erick.

valor_base = valor da faixa de alimentação (1–13) do funcionário.

Faltas (só contam se a pessoa estiver INCLUÍDA na revisão de faltas):
  faltas_dias = dias de falta cheia (planilha de faltas) + dias de atestado.
  (atestado conta como falta; todos os tipos contam.)
Atraso (idem, só se incluída):
  atraso_min = soma dos minutos de atraso no período.

Desconto = o PIOR (maior) entre o nível das faltas e o nível do atraso:
  faltas: 1→50% | 2→75% | 3+→100%
  atraso: 30min→50% | 60min→75% | 90min+→100%
valor_final = valor_base × (1 − desconto/100).

Exceção (diretoria/sócios): tratada no exportador_sodexo — se o valor que está
na planilha não é um valor de faixa, mantém como está (não recalcula/desconta).
"""
from __future__ import annotations
from typing import Optional


def nivel_por_faltas(faltas_dias: float) -> int:
    if faltas_dias >= 3: return 100
    if faltas_dias >= 2: return 75
    if faltas_dias >= 1: return 50
    return 0


def nivel_por_atraso(atraso_min: float) -> int:
    if atraso_min >= 90: return 100
    if atraso_min >= 60: return 75
    if atraso_min >= 30: return 50
    return 0


def calcular_funcionario(codigo, nome, cargo, faixa_alim, valor_base, departamento="", empresa="PISA",
                         faltas_dias_planilha=0, atraso_min=0, incluir_faltas=True,
                         atestado_dias=0, atestado_indeterminado=False, cpf="",
                         em_ferias=False, tem_atestado=False) -> dict:
    valor_base = float(valor_base or 0)
    faltas_planilha = float(faltas_dias_planilha or 0) if incluir_faltas else 0.0
    atraso = float(atraso_min or 0) if incluir_faltas else 0.0
    atestado = float(atestado_dias or 0)  # só informativo (qtd de dias, quando há)
    # Tem atestado se houver dias OU se vier marcado (inclui os indeterminados, sem dias)
    tem_atestado = bool(tem_atestado or atestado > 0 or atestado_indeterminado)

    nivel_f = nivel_por_faltas(faltas_planilha)
    nivel_a = nivel_por_atraso(atraso)
    pct_desconto = max(nivel_f, nivel_a)
    # Atestado e Férias ZERAM o mês (qualquer atestado, com ou sem nº de dias).
    if tem_atestado or em_ferias:
        pct_desconto = 100
    valor_desconto = round(valor_base * pct_desconto / 100.0, 2)
    valor_final = round(valor_base - valor_desconto, 2)
    zerado_por_ferias = bool(em_ferias)
    # Férias tem prioridade na anotação; senão, qualquer atestado marca "Atestado".
    zerado_por_atestado = bool(tem_atestado and not em_ferias)

    motivos = []
    if em_ferias: motivos.append("Férias (zera)")
    if tem_atestado:
        if atestado > 0:
            motivos.append(f"Atestado {atestado:g} dia(s) (zera)")
        else:
            motivos.append("Atestado sem nº de dias (zera)")
    if faltas_planilha: motivos.append(f"{faltas_planilha:g} falta(s)")
    if atraso:
        motivos.append(f"atraso {int(atraso//60)}h{int(atraso%60):02d}")

    return {
        "codigo": codigo, "cpf": cpf, "nome": nome, "cargo": cargo, "departamento": departamento, "empresa": empresa,
        "faixa_alim": faixa_alim, "valor_base": valor_base,
        "faltas_dias": faltas_planilha, "faltas_planilha": faltas_planilha,
        "atestado_dias": atestado, "atraso_min": atraso,
        "pct_desconto": pct_desconto, "valor_desconto": valor_desconto,
        "valor_final": valor_final, "pct_recebido": round(100 - pct_desconto, 2),
        "zerado_por_atestado": zerado_por_atestado,
        "zerado_por_ferias": zerado_por_ferias,
        "atestado_indeterminado": atestado_indeterminado,
        "motivo": "; ".join(motivos) if motivos else "Integral (sem ocorrência)",
    }


def calcular_processo(funcionarios, faltas_por_codigo, atestados_por_codigo,
                      faixa_valor, incluidos=None, ferias_incluidos=None) -> dict:
    resultados = []
    avisos = []
    for f in funcionarios:
        cod = str(f.get("codigo"))
        faixa = f.get("faixa_alim")
        valor_base = faixa_valor.get(int(faixa)) if faixa is not None else None
        if valor_base is None:
            valor_base = 0.0
            if faixa is not None:
                avisos.append(f"{f.get('nome')} (cód {cod}): faixa {faixa} sem valor cadastrado.")
        falta = faltas_por_codigo.get(cod, {})
        atest = atestados_por_codigo.get(cod, {})
        incluir = True if incluidos is None else (cod in incluidos)
        em_ferias = (ferias_incluidos is not None and cod in ferias_incluidos)
        tem_atestado = cod in atestados_por_codigo
        res = calcular_funcionario(
            codigo=cod, nome=f.get("nome", ""), cargo=f.get("cargo"),
            departamento=f.get("departamento", ""), empresa=f.get("empresa") or "PISA",
            faixa_alim=faixa, valor_base=valor_base,
            faltas_dias_planilha=falta.get("faltas_dias", 0),
            atraso_min=falta.get("atraso_min", 0), incluir_faltas=incluir,
            atestado_dias=atest.get("dias", 0),
            atestado_indeterminado=atest.get("indeterminado", False),
            cpf=f.get("cpf", ""), em_ferias=em_ferias, tem_atestado=tem_atestado,
        )
        resultados.append(res)

    totais = {
        "total_funcionarios": len(resultados),
        "valor_premios": round(sum(r["valor_base"] for r in resultados), 2),
        "valor_descontos": round(sum(r["valor_desconto"] for r in resultados), 2),
        "valor_liquido": round(sum(r["valor_final"] for r in resultados), 2),
        "zerados": sum(1 for r in resultados if r["valor_final"] == 0 and r["valor_base"] > 0),
        "integrais": sum(1 for r in resultados if r["pct_desconto"] == 0),
        "ferias": sum(1 for r in resultados if r.get("zerado_por_ferias")),
    }
    return {"resultados": resultados, "totais": totais, "avisos": avisos}
