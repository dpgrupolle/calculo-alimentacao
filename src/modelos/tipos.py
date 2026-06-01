"""Tipos centrais do sistema Gestão de Benefícios — DP/RH."""
from __future__ import annotations
from enum import Enum


class PerfilUsuario(str, Enum):
    """
    Perfis de acesso (decisão Erick):
    - GESTAO_RH: tudo (operacional + gerência de usuários + exclusões).
    - ANALISTA_RH: operacional completo (uploads, processar, gerar, excluir c/ senha).
    - DIRETORIA: só visualiza.
    A gestão de usuários fica restrita à GESTAO_RH; o resto é igual para os dois.
    """
    GESTAO_RH = "GESTAO_RH"
    ANALISTA_RH = "ANALISTA_RH"
    DIRETORIA = "DIRETORIA"


class StatusProcesso(str, Enum):
    EM_ANDAMENTO = "EM_ANDAMENTO"
    FINALIZADO = "FINALIZADO"
