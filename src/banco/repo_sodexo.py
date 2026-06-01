"""Repositório do modelo Sodexo guardado, agora POR EMPRESA (Opção C)."""
from __future__ import annotations
import base64
from typing import Optional
from src.banco.conexao import obter_conexao, transacao


def salvar_modelo(nome_arquivo: str, conteudo_bytes: bytes, total_benef: int, usuario,
                  empresa: str = "PISA") -> int:
    """Salva um novo modelo para a empresa e o torna o ativo dela."""
    b64 = base64.b64encode(conteudo_bytes).decode("ascii")
    with transacao() as conn:
        conn.execute("UPDATE sodexo_modelo SET ativo = 0 WHERE empresa = ?;", (empresa,))
        cur = conn.execute(
            "INSERT INTO sodexo_modelo (nome_arquivo, conteudo_base64, total_beneficiarios, empresa, ativo, "
            "enviado_por_id, enviado_por_nome) VALUES (?, ?, ?, ?, 1, ?, ?);",
            (nome_arquivo, b64, int(total_benef), empresa,
             getattr(usuario, "id", None), getattr(usuario, "nome", None)),
        )
        return cur.lastrowid


def modelo_ativo(empresa: str = "PISA") -> Optional[dict]:
    return obter_conexao().execute(
        "SELECT * FROM sodexo_modelo WHERE ativo = 1 AND empresa = ? ORDER BY id DESC LIMIT 1;",
        (empresa,)).fetchone()


def conteudo_do_modelo(modelo_id: int) -> Optional[bytes]:
    row = obter_conexao().execute(
        "SELECT conteudo_base64 FROM sodexo_modelo WHERE id = ?;", (modelo_id,)).fetchone()
    return base64.b64decode(row["conteudo_base64"]) if row else None


def conteudo_ativo(empresa: str = "PISA") -> Optional[bytes]:
    m = modelo_ativo(empresa)
    return conteudo_do_modelo(m["id"]) if m else None
