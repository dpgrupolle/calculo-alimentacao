"""
Parser da PLANILHA DE FÉRIAS (PDF "Gozo de Férias no Mês" — Sankhya/JasperReports).

Layout (texto): Código | Nome | Departamento | Cargo | Período Aquisitivo |
                Período de Gozo | Dias de Férias | Abono Pecuniário

Decisão Erick: quem está de férias (e marcado) ZERA o benefício do mês.
A ligação ao cadastro é pelo Código (com a mesma lógica das outras planilhas:
código direto / tira o "1" / tira zero à esquerda; nome como reserva).

Lê PDF com pdfplumber. Usa arquivo.getvalue() (nunca .read()).
"""
from __future__ import annotations

import io
import re

import pdfplumber

# Tokens que marcam o início do "Departamento" (para separar o nome)
_DEPTOS = ["DEPÓSITO", "DEPOSITO", "VENDAS", "DIRETORIA", "TRANSPORTES", "TI ",
           "CRÉDITO", "CREDITO", "TESOURARIA", "SETOR", "COMPRAS", "ADM",
           "DEPARTAMENTO", "FINANC", "LOGISTICA", "MATURANA", "PISA"]

_LINHA = re.compile(
    r"^(\d{3,6})\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})\s+"
    r"(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})\s+(\d+)\s+(\d+)\s*$"
)


def _extrai_nome(resto: str) -> str:
    """Pega o nome (palavras iniciais) antes do departamento."""
    up = resto.upper()
    corte = len(resto)
    for tok in _DEPTOS:
        i = up.find(tok)
        if i > 0:
            corte = min(corte, i)
    nome = resto[:corte].strip()
    return nome or resto.strip()


def ler_planilha_ferias(arquivo) -> dict:
    """
    Devolve {"pessoas": [{codigo, nome, periodo_gozo, dias}], "avisos": [...], "total": n}.
    """
    conteudo = arquivo.getvalue()
    try:
        with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
            texto = "\n".join((pg.extract_text() or "") for pg in pdf.pages)
    except Exception as e:
        raise ValueError(f"Não consegui ler o PDF de férias: {e}")

    pessoas = []
    for linha in texto.split("\n"):
        m = _LINHA.match(linha.strip())
        if not m:
            continue
        codigo, resto, _aq1, _aq2, gz1, gz2, dias, _abono = m.groups()
        pessoas.append({
            "codigo": codigo.strip(),
            "nome": _extrai_nome(resto),
            "periodo_gozo": f"{gz1} a {gz2}",
            "dias": int(dias),
        })

    if not pessoas:
        raise ValueError(
            "Não encontrei registros de férias no PDF. Confira se é o relatório "
            "'Gozo de Férias no Mês' do Sankhya."
        )
    return {"pessoas": pessoas, "avisos": [], "total": len(pessoas)}
