"""
Helpers centralizados de permissões — Gestão de Benefícios DP/RH.

Regras (decisão Erick):
- GESTAO_RH: pode TUDO (operacional + gerenciar usuários + exclusões).
- ANALISTA_RH: operacional completo (uploads, processar, gerar, excluir c/ senha).
- DIRETORIA: só visualiza.

Centralizar aqui evita espalhar checagens. Se uma regra mudar, muda só num lugar.
"""
from __future__ import annotations

from src.modelos.tipos import PerfilUsuario


def eh_gestao(usuario) -> bool:
    """Apenas a Gestão de RH (equivalente ao 'admin' do esqueleto)."""
    return usuario.perfil == PerfilUsuario.GESTAO_RH


def eh_apenas_visualizacao(usuario) -> bool:
    """Diretoria só observa."""
    return usuario.perfil == PerfilUsuario.DIRETORIA


def pode_editar(usuario) -> bool:
    """
    Pode operar o sistema: subir planilhas, processar, gerar e excluir.
    Gestão e Analista podem. Diretoria não.
    """
    return usuario.perfil in (PerfilUsuario.GESTAO_RH, PerfilUsuario.ANALISTA_RH)


def pode_excluir(usuario) -> bool:
    """
    Excluir envios/processos. Sempre exige senha (ver exclusao_com_senha).
    Gestão e Analista podem.
    """
    return usuario.perfil in (PerfilUsuario.GESTAO_RH, PerfilUsuario.ANALISTA_RH)


def pode_gerenciar_usuarios(usuario) -> bool:
    """
    Cadastrar, aprovar, recusar, inativar, redefinir senha, mudar cargo.
    Restrito à GESTAO_RH (evita que um analista bloqueie outro).
    """
    return usuario.perfil == PerfilUsuario.GESTAO_RH


def pode_visualizar_admin(usuario) -> bool:
    """Acesso à área administrativa de visualização (lista de usuários)."""
    return usuario.perfil in (PerfilUsuario.GESTAO_RH, PerfilUsuario.DIRETORIA)


def pode_alterar_parametros(usuario) -> bool:
    """Editar tabelas de prêmio e regras de desconto."""
    return usuario.perfil in (PerfilUsuario.GESTAO_RH, PerfilUsuario.ANALISTA_RH)
