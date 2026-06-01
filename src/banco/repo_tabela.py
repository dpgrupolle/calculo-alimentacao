"""Repositório das faixas de alimentação (tabela_beneficio)."""
from __future__ import annotations
from typing import List, Optional
from src.banco.conexao import obter_conexao, transacao


def listar_faixas(apenas_ativas: bool = False) -> List[dict]:
    sql = "SELECT * FROM tabela_beneficio"
    if apenas_ativas:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY numero;"
    return obter_conexao().execute(sql).fetchall()


def buscar_faixa(numero: int) -> Optional[dict]:
    cur = obter_conexao().execute("SELECT * FROM tabela_beneficio WHERE numero = ?;", (numero,))
    return cur.fetchone()


def mapa_valor_por_faixa(apenas_ativas: bool = False) -> dict:
    """{numero_faixa: valor_premio} — usado pelo motor de cálculo."""
    return {int(r["numero"]): float(r["valor_premio"]) for r in listar_faixas(apenas_ativas)}


def criar_faixa(numero: int, nome: str, valor: float) -> int:
    if buscar_faixa(numero) is not None:
        raise ValueError(f"Já existe a faixa {numero}.")
    with transacao() as conn:
        cur = conn.execute(
            "INSERT INTO tabela_beneficio (numero, nome, valor_premio) VALUES (?, ?, ?);",
            (int(numero), (nome or "").strip() or f"Faixa {numero}", float(valor)),
        )
        return cur.lastrowid


def atualizar_faixa(faixa_id: int, nome: str, valor: float, ativo: bool = True) -> None:
    with transacao() as conn:
        conn.execute(
            "UPDATE tabela_beneficio SET nome=?, valor_premio=?, ativo=?, "
            "atualizado_em=datetime('now') WHERE id=?;",
            ((nome or "").strip(), float(valor), 1 if ativo else 0, faixa_id),
        )


def excluir_faixa(faixa_id: int) -> None:
    with transacao() as conn:
        conn.execute("DELETE FROM tabela_beneficio WHERE id=?;", (faixa_id,))
