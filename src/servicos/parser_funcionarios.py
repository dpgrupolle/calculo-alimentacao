"""
Parser da PLANILHA DE FUNCIONÁRIOS (cadastro do Sankhya).

Layout real (confirmado com o Erick):
  - Cabeçalho na 3ª linha (índice 2); dados a partir da 4ª.
  - Colunas usadas:
      Código (col 1)  -> chave de ligação (Pontotel = "1" + este código)
      Matrícula (col 2)
      Nome (col 3)
      Descrição (Cargos) (col 6)
      CPF (col 10)
      "Informe tab faixa ticket alim" (col 293) -> faixa de alimentação (1–13)
      "Carga Horária" (col 294)
  Demais colunas são ignoradas.

Regra: usa arquivo.getvalue() (nunca .read()).
"""
from __future__ import annotations

import io
import pandas as pd

from src.utils.formatadores import normalizar_busca
from src.servicos.matching import so_digitos
from src.utils.marca import normalizar_empresa

# Apelidos (normalizados) para localizar cada coluna pelo cabeçalho
AP_CODIGO = {"codigo", "código"}
AP_MATRICULA = {"matricula", "matrícula"}
AP_NOME = {"nome"}
AP_CARGO = {"descricao (cargos)", "descrição (cargos)", "cargo", "descricao cargos"}
AP_CPF = {"cpf"}
AP_DEPTO = {"descricao (departamentos)", "descrição (departamentos)", "departamento (descricao)", "depto"}
AP_EMPRESA = {"nome fantasia (empresa)"}
# A faixa de alimentação é a coluna "Informe tab faixa ticket alim" (decisão Erick).
# CUIDADO: existe outra coluna parecida ("Informe Faixa Tabela Refeição") que vem
# quase toda zerada — por isso usamos uma lista ORDENADA de preferência.
AP_FAIXA_PREFERENCIA = [
    "informe tab faixa ticket alim",
    "tab faixa ticket alim",
    "informe tab faixa ticket alimentacao",
    "faixa alimentacao", "faixa alimentação",
    "informe faixa tabela refeicao", "informe faixa tabela refeição",
    "faixa",
]
AP_CARGA = {"carga horaria", "carga horária"}


def _acha(colmap: dict, apelidos: set, default=None):
    for idx, nome in colmap.items():
        if nome in apelidos:
            return idx
    return default


def _acha_preferencia(colmap: dict, lista_ordenada: list, default=None):
    """Procura na ORDEM da lista — retorna o índice do primeiro apelido que existir."""
    for apelido in lista_ordenada:
        for idx, nome in colmap.items():
            if nome == apelido:
                return idx
    return default


def _localiza_linha_cabecalho(raw: pd.DataFrame) -> int:
    """Procura a linha que contém 'Matrícula' e 'Nome' (cabeçalho real)."""
    for i in range(min(10, len(raw))):
        linha = [normalizar_busca(str(v)) for v in raw.iloc[i]]
        if any(v in AP_MATRICULA for v in linha) and any(v in AP_NOME for v in linha):
            return i
    return 0


def ler_planilha_funcionarios(arquivo) -> dict:
    """
    Devolve {"funcionarios": [ {codigo, matricula, nome, cargo, cpf,
              faixa_alim, carga_horaria}, ... ], "avisos": [...], "total": n}
    """
    conteudo = arquivo.getvalue()
    nome_arq = getattr(arquivo, "name", "func.xlsx").lower()
    try:
        if nome_arq.endswith(".csv"):
            raw = pd.read_csv(io.BytesIO(conteudo), header=None, dtype=str)
        else:
            raw = pd.read_excel(io.BytesIO(conteudo), header=None, dtype=str)
    except Exception as e:
        raise ValueError(f"Não consegui abrir a planilha de funcionários: {e}")

    if raw.empty:
        raise ValueError("A planilha de funcionários está vazia.")

    ih = _localiza_linha_cabecalho(raw)
    cab = raw.iloc[ih]
    colmap = {j: normalizar_busca(str(v)) for j, v in enumerate(cab)}

    c_cod = _acha(colmap, AP_CODIGO)
    c_mat = _acha(colmap, AP_MATRICULA)
    c_nome = _acha(colmap, AP_NOME)
    c_cargo = _acha(colmap, AP_CARGO)
    c_cpf = _acha(colmap, AP_CPF)
    c_depto = _acha(colmap, AP_DEPTO)
    c_empresa = _acha(colmap, AP_EMPRESA)
    c_faixa = _acha_preferencia(colmap, AP_FAIXA_PREFERENCIA)
    c_carga = _acha(colmap, AP_CARGA)

    faltando = []
    if c_cod is None and c_mat is None:
        faltando.append("Código/Matrícula")
    if c_nome is None:
        faltando.append("Nome")
    if c_faixa is None:
        faltando.append("Faixa de alimentação (Informe tab faixa ticket alim)")
    if faltando:
        raise ValueError(
            "Não encontrei a(s) coluna(s): " + ", ".join(faltando) +
            ". Confira se é a planilha de funcionários do Sankhya."
        )

    # Se não houver Código, usa Matrícula como chave
    chave = c_cod if c_cod is not None else c_mat

    dados = raw.iloc[ih + 1:].reset_index(drop=True)
    funcionarios = []
    avisos = []
    for _, linha in dados.iterrows():
        codigo = str(linha.get(chave) or "").strip()
        nome = str(linha.get(c_nome) or "").strip()
        if not codigo or codigo.lower() == "nan" or not nome or nome.lower() == "nan":
            continue
        cpf = so_digitos(linha.get(c_cpf)) if c_cpf is not None else ""
        cargo = str(linha.get(c_cargo) or "").strip() if c_cargo is not None else ""
        depto = str(linha.get(c_depto) or "").strip() if c_depto is not None else ""
        if depto.lower() == "nan": depto = ""
        empresa = normalizar_empresa(linha.get(c_empresa)) if c_empresa is not None else "PISA"
        carga = str(linha.get(c_carga) or "").strip() if c_carga is not None else ""
        faixa_raw = str(linha.get(c_faixa) or "").strip()
        faixa = None
        if faixa_raw and faixa_raw.lower() != "nan":
            try:
                faixa = int(float(faixa_raw))
            except (ValueError, TypeError):
                avisos.append(f"Código {codigo}: faixa '{faixa_raw}' não é número.")
        matricula = str(linha.get(c_mat) or codigo).strip() if c_mat is not None else codigo
        funcionarios.append({
            "codigo": codigo,
            "matricula": matricula,
            "nome": nome,
            "cargo": cargo,
            "departamento": depto,
            "empresa": empresa,
            "cpf": cpf,
            "faixa_alim": faixa,
            "carga_horaria": carga,
        })

    if not funcionarios:
        raise ValueError("Nenhum funcionário válido encontrado na planilha.")

    return {"funcionarios": funcionarios, "avisos": avisos, "total": len(funcionarios)}
