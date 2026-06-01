"""
Parser da PLANILHA DE FALTAS (relatório diário do Pontotel).

Layout real:
  - Cabeçalho na 1ª linha (índice 0); dados a partir da 2ª.
  - Uma linha por funcionário POR DIA. Colunas usadas:
      Código (col 0)   -> matrícula Pontotel (liga ao cadastro tirando o '1')
      CPF (col 1)
      Funcionário (col 2)
      H. Atraso (col 11)  -> hh:mm de atraso no dia
      H. Falta (col 12)   -> hh:mm de falta no dia (jornada cheia = 1 dia de falta)

Consolida POR FUNCIONÁRIO:
  - atraso_min  = soma dos minutos de H. Atraso no período
  - faltas_dias = nº de dias em que houve H. Falta > 0 (cada dia cheio = 1 falta)

Regra: usa arquivo.getvalue() (nunca .read()).
"""
from __future__ import annotations

import io
import pandas as pd

from src.utils.formatadores import normalizar_busca
from src.servicos.matching import so_digitos

AP_CODIGO = {"codigo", "código"}
AP_CPF = {"cpf"}
AP_NOME = {"funcionario", "funcionário", "nome"}
AP_ATRASO = {"h. atraso", "h atraso", "hatraso", "atraso"}
AP_FALTA = {"h. falta", "h falta", "hfalta", "falta"}


def _acha(colmap, apelidos):
    for idx, nome in colmap.items():
        if nome in apelidos:
            return idx
    return None


def _hhmm_para_min(valor) -> int:
    s = str(valor).strip()
    if not s or s.lower() == "nan" or ":" not in s:
        return 0
    try:
        partes = s.split(":")
        h = int(partes[0]); m = int(partes[1])
        return h * 60 + m
    except (ValueError, IndexError):
        return 0


def ler_planilha_faltas(arquivo) -> dict:
    """
    Devolve {"pessoas": [ {codigo, cpf, nome, atraso_min, faltas_dias}, ... ],
             "avisos": [...], "total_linhas": n}
    Uma entrada por funcionário (já consolidado).
    """
    conteudo = arquivo.getvalue()
    nome_arq = getattr(arquivo, "name", "faltas.xls").lower()
    try:
        if nome_arq.endswith(".csv"):
            raw = pd.read_csv(io.BytesIO(conteudo), header=None, dtype=str)
        else:
            raw = pd.read_excel(io.BytesIO(conteudo), header=None, dtype=str)
    except Exception as e:
        raise ValueError(f"Não consegui abrir a planilha de faltas: {e}")

    if raw.empty:
        raise ValueError("A planilha de faltas está vazia.")

    cab = raw.iloc[0]
    colmap = {j: normalizar_busca(str(v)) for j, v in enumerate(cab)}
    c_cod = _acha(colmap, AP_CODIGO)
    c_cpf = _acha(colmap, AP_CPF)
    c_nome = _acha(colmap, AP_NOME)
    c_atraso = _acha(colmap, AP_ATRASO)
    c_falta = _acha(colmap, AP_FALTA)

    if c_cod is None and c_cpf is None:
        raise ValueError("Planilha de faltas: não achei a coluna Código nem CPF.")
    if c_atraso is None and c_falta is None:
        raise ValueError("Planilha de faltas: não achei H. Atraso nem H. Falta.")

    dados = raw.iloc[1:].reset_index(drop=True)
    consol: dict[str, dict] = {}
    for _, linha in dados.iterrows():
        cod = str(linha.get(c_cod) or "").strip() if c_cod is not None else ""
        cpf = so_digitos(linha.get(c_cpf)) if c_cpf is not None else ""
        nome = str(linha.get(c_nome) or "").strip() if c_nome is not None else ""
        if (not cod or cod.lower() == "nan") and not cpf:
            continue
        chave = cod or cpf
        if chave not in consol:
            consol[chave] = {"codigo": cod, "cpf": cpf, "nome": nome,
                             "atraso_min": 0, "faltas_dias": 0}
        if c_atraso is not None:
            consol[chave]["atraso_min"] += _hhmm_para_min(linha.get(c_atraso))
        if c_falta is not None and _hhmm_para_min(linha.get(c_falta)) > 0:
            consol[chave]["faltas_dias"] += 1

    pessoas = list(consol.values())
    # mantém só quem tem alguma falta ou atraso (a tela mostra "os faltosos")
    pessoas = [p for p in pessoas if p["atraso_min"] > 0 or p["faltas_dias"] > 0]
    return {"pessoas": pessoas, "avisos": [], "total_linhas": len(dados)}
