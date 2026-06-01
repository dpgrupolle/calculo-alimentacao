"""
Serviço de auditoria: registra ações dos usuários no log_auditoria.

Uso:
    from src.servicos import auditoria
    auditoria.registrar(usuario, "PROCESSAR", entidade="processo",
                        entidade_id=pid, detalhes="Mês 2026-05")
"""
from __future__ import annotations

from typing import Optional

from src.banco.conexao import transacao, obter_conexao


def registrar(usuario, acao: str, entidade: Optional[str] = None,
              entidade_id: Optional[int] = None, detalhes: str = "") -> None:
    """Grava uma linha no log. Nunca levanta exceção (não pode quebrar a ação)."""
    try:
        with transacao() as conn:
            conn.execute(
                "INSERT INTO log_auditoria "
                "(usuario_id, usuario_nome_snapshot, acao, entidade, entidade_id, detalhes) "
                "VALUES (?, ?, ?, ?, ?, ?);",
                (
                    getattr(usuario, "id", None),
                    getattr(usuario, "nome", None),
                    acao,
                    entidade,
                    entidade_id,
                    detalhes,
                ),
            )
    except Exception:
        pass


def listar_recentes(limite: int = 50) -> list:
    """Lista as ações mais recentes (para a tela de usuários/auditoria)."""
    try:
        cur = obter_conexao().execute(
            "SELECT * FROM log_auditoria ORDER BY id DESC LIMIT ?;", (limite,)
        )
        return cur.fetchall()
    except Exception:
        return []


def listar_auditoria(limite: int = 200, acao: str = "", busca: str = "") -> list:
    """Lista ações para a tela de Auditoria, com filtro opcional por ação e por texto."""
    try:
        sql = "SELECT * FROM log_auditoria WHERE 1=1"
        params: list = []
        if acao:
            sql += " AND acao = ?"; params.append(acao)
        if busca:
            sql += " AND (LOWER(COALESCE(usuario_nome_snapshot,'')) LIKE ? OR LOWER(COALESCE(detalhes,'')) LIKE ?)"
            t = f"%{busca.lower()}%"; params += [t, t]
        sql += " ORDER BY id DESC LIMIT ?;"
        params.append(int(limite))
        return obter_conexao().execute(sql, params).fetchall()
    except Exception:
        return []


def acoes_distintas() -> list:
    try:
        rows = obter_conexao().execute(
            "SELECT DISTINCT acao FROM log_auditoria ORDER BY acao;").fetchall()
        return [r["acao"] for r in rows]
    except Exception:
        return []
