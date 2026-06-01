"""
Ligação entre as planilhas (decisão Erick):

  Matrícula do Pontotel (Código nas faltas / Matrícula nos atestados)
      = "1" + Código do cadastro (Sankhya)

  Então: tirar o "1" da frente → bate no campo "Código" do cadastro.
  Confirmação/reserva: CPF (presente no cadastro e nas faltas).

Testado com os arquivos reais: faltas 157/157, atestados 14/14.
"""
from __future__ import annotations

from typing import Optional


def so_digitos(valor) -> str:
    return "".join(ch for ch in str(valor) if ch.isdigit())


def tira_um(codigo_pontotel) -> str:
    """Remove o '1' da frente da matrícula do Pontotel → código do cadastro."""
    c = str(codigo_pontotel).strip()
    if c.startswith("1") and len(c) > 1:
        return c[1:]
    return c


def _norm_nome(valor) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", str(valor or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.upper().split())


def normaliza_codigo(valor) -> str:
    """Normaliza um código de cadastro (remove zeros à esquerda? não — mantém)."""
    return str(valor).strip()


class IndiceCadastro:
    """
    Índice para localizar um funcionário do cadastro a partir das chaves que
    aparecem nas planilhas de ponto (Pontotel) ou por CPF.
    """

    def __init__(self):
        self._por_codigo: dict[str, dict] = {}
        self._por_cpf: dict[str, dict] = {}
        self._por_nome: dict[str, dict] = {}

    def adicionar(self, func: dict) -> None:
        cod = normaliza_codigo(func.get("codigo"))
        if cod:
            self._por_codigo[cod] = func
        cpf = so_digitos(func.get("cpf"))
        if cpf:
            self._por_cpf[cpf] = func
        nome = _norm_nome(func.get("nome"))
        if nome:
            self._por_nome[nome] = func

    def localizar(self, matricula_pontotel=None, cpf=None) -> Optional[dict]:
        """
        Tenta achar o funcionário:
          1) tira o '1' da matrícula Pontotel e bate no Código do cadastro
          2) tenta a matrícula como veio (sem tirar o 1)
          3) cai pro CPF
        """
        if matricula_pontotel is not None:
            base = tira_um(matricula_pontotel)
            if base in self._por_codigo:
                return self._por_codigo[base]
            bruto = normaliza_codigo(matricula_pontotel)
            if bruto in self._por_codigo:
                return self._por_codigo[bruto]
        if cpf:
            c = so_digitos(cpf)
            if c in self._por_cpf:
                return self._por_cpf[c]
        return None

    def localizar_por_nome(self, nome):
        return self._por_nome.get(_norm_nome(nome))
