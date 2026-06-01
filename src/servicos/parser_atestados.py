"""
Parser da PLANILHA DE ATESTADOS (afastamentos do Pontotel).

Layout real — aba "Planilha de Afastamentos":
  - Cabeçalho na 1ª linha (índice 0); dados a partir da 2ª.
  - Colunas: FUNCIONARIO(0), MATRICULA(1)=Pontotel, LOCAL(2), TIPO(3),
             INICIO(4), FIM(5), DIAS(6)

Decisão Erick: TODOS os tipos contam como falta. Soma os DIAS por funcionário.
Quando vem "indeterminado"/"-" (auxílio-doença/INSS/acidente), não há nº de dias:
esses são marcados como `indeterminado=True` e sinalizados em avisos, para o RH
decidir — NÃO inventamos um número de dias.

Regra: usa arquivo.getvalue() (nunca .read()).
"""
from __future__ import annotations

import io
import pandas as pd

from src.utils.formatadores import normalizar_busca

AP_MATRICULA = {"matricula", "matrícula"}
AP_NOME = {"funcionario", "funcionário", "nome"}
AP_TIPO = {"tipo"}
AP_DIAS = {"dias"}
ABA_AFASTAMENTOS = "Planilha de Afastamentos"


def _acha(colmap, apelidos):
    for idx, nome in colmap.items():
        if nome in apelidos:
            return idx
    return None


def ler_planilha_atestados(arquivo) -> dict:
    """
    Devolve {"pessoas": [ {matricula, nome, dias, indeterminado, tipos:[...]} ],
             "avisos": [...], "total_linhas": n}
    Consolidado por funcionário (soma de dias; tipos juntados).
    """
    conteudo = arquivo.getvalue()
    nome_arq = getattr(arquivo, "name", "atestados.xlsx").lower()
    try:
        if nome_arq.endswith(".csv"):
            raw = pd.read_csv(io.BytesIO(conteudo), header=None, dtype=str)
        else:
            xl = pd.ExcelFile(io.BytesIO(conteudo))
            aba = ABA_AFASTAMENTOS if ABA_AFASTAMENTOS in xl.sheet_names else xl.sheet_names[0]
            raw = pd.read_excel(xl, sheet_name=aba, header=None, dtype=str)
    except Exception as e:
        raise ValueError(f"Não consegui abrir a planilha de atestados: {e}")

    if raw.empty:
        return {"pessoas": [], "avisos": ["Planilha de atestados vazia."], "total_linhas": 0}

    cab = raw.iloc[0]
    colmap = {j: normalizar_busca(str(v)) for j, v in enumerate(cab)}
    c_mat = _acha(colmap, AP_MATRICULA)
    c_nome = _acha(colmap, AP_NOME)
    c_tipo = _acha(colmap, AP_TIPO)
    c_dias = _acha(colmap, AP_DIAS)

    if c_mat is None:
        raise ValueError("Planilha de atestados: não achei a coluna MATRICULA.")

    dados = raw.iloc[1:].reset_index(drop=True)
    consol: dict[str, dict] = {}
    avisos = []
    for _, linha in dados.iterrows():
        mat = str(linha.get(c_mat) or "").strip()
        if not mat or mat.lower() == "nan":
            continue
        nome = str(linha.get(c_nome) or "").strip() if c_nome is not None else ""
        tipo = str(linha.get(c_tipo) or "").strip() if c_tipo is not None else ""
        tipo = tipo.split(" - ")[0].strip()
        dias_raw = str(linha.get(c_dias) or "").strip() if c_dias is not None else ""
        if mat not in consol:
            consol[mat] = {"matricula": mat, "nome": nome, "dias": 0,
                           "indeterminado": False, "tipos": []}
        if tipo:
            consol[mat]["tipos"].append(tipo)
        try:
            dias = int(float(dias_raw))
            consol[mat]["dias"] += dias
        except (ValueError, TypeError):
            # "-" / "indeterminado" — sem nº de dias
            consol[mat]["indeterminado"] = True
            avisos.append(
                f"{nome or mat}: atestado '{tipo}' sem nº de dias (indeterminado) — "
                f"zera o mês mesmo assim (atestado zera)."
            )

    return {"pessoas": list(consol.values()), "avisos": avisos,
            "total_linhas": len(dados)}
