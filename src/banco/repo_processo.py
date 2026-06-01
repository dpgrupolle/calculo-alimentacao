"""Repositório de Processos: processo, uploads, falta_item, atestado_item, resultados."""
from __future__ import annotations
from typing import List, Optional
from src.banco.conexao import obter_conexao, transacao


# ---------- PROCESSO ----------
def criar_processo(mes_referencia: str, descricao: str, usuario, empresa: str = "PISA") -> int:
    mes = (mes_referencia or "").strip()
    if not mes:
        raise ValueError("Mês de referência é obrigatório (ex: 2026-05).")
    with transacao() as conn:
        cur = conn.execute(
            "INSERT INTO processo (mes_referencia, descricao, empresa, usuario_id, usuario_nome_snapshot) "
            "VALUES (?, ?, ?, ?, ?);",
            (mes, (descricao or "").strip(), empresa or "PISA",
             getattr(usuario, "id", None), getattr(usuario, "nome", None)),
        )
        return cur.lastrowid


def buscar_processo(pid: int) -> Optional[dict]:
    return obter_conexao().execute("SELECT * FROM processo WHERE id = ?;", (pid,)).fetchone()


def listar_processos(status: Optional[str] = None, empresa: str = "") -> List[dict]:
    sql = "SELECT * FROM processo WHERE 1=1"
    params = []
    if status:
        sql += " AND status = ?"; params.append(status)
    if empresa:
        sql += " AND empresa = ?"; params.append(empresa)
    sql += " ORDER BY criado_em DESC, id DESC;"
    return obter_conexao().execute(sql, params).fetchall()


def finalizar(pid: int) -> None:
    with transacao() as conn:
        conn.execute("UPDATE processo SET status='FINALIZADO', finalizado_em=datetime('now') WHERE id=?;", (pid,))


def reabrir(pid: int) -> None:
    with transacao() as conn:
        conn.execute("UPDATE processo SET status='EM_ANDAMENTO', finalizado_em=NULL WHERE id=?;", (pid,))


def atualizar_totais(pid: int, total, premios, descontos, liquido) -> None:
    with transacao() as conn:
        conn.execute(
            "UPDATE processo SET total_funcionarios=?, valor_total_premios=?, "
            "valor_total_descontos=?, valor_total_liquido=? WHERE id=?;",
            (int(total), float(premios), float(descontos), float(liquido), pid),
        )


def excluir_processo(pid: int) -> None:
    with transacao() as conn:
        for t in ("resultado_beneficio", "falta_item", "atestado_item", "ferias_item", "upload_planilha"):
            conn.execute(f"DELETE FROM {t} WHERE processo_id = ?;", (pid,))
        conn.execute("DELETE FROM processo WHERE id = ?;", (pid,))


# ---------- UPLOADS ----------
def registrar_upload(pid: int, tipo: str, nome_arquivo: str, hash_arq: str, total: int, usuario) -> None:
    with transacao() as conn:
        conn.execute("DELETE FROM upload_planilha WHERE processo_id=? AND tipo=?;", (pid, tipo))
        conn.execute(
            "INSERT INTO upload_planilha (processo_id, tipo, nome_arquivo, hash_arquivo, total_linhas, usuario_id) "
            "VALUES (?, ?, ?, ?, ?, ?);",
            (pid, tipo, nome_arquivo, hash_arq, int(total), getattr(usuario, "id", None)),
        )


def listar_uploads(pid: int) -> List[dict]:
    return obter_conexao().execute("SELECT * FROM upload_planilha WHERE processo_id=? ORDER BY tipo;", (pid,)).fetchall()


def buscar_upload(pid: int, tipo: str) -> Optional[dict]:
    return obter_conexao().execute("SELECT * FROM upload_planilha WHERE processo_id=? AND tipo=?;", (pid, tipo)).fetchone()


def excluir_upload(pid: int, tipo: str) -> None:
    with transacao() as conn:
        conn.execute("DELETE FROM upload_planilha WHERE processo_id=? AND tipo=?;", (pid, tipo))
        if tipo == "FALTAS":
            conn.execute("DELETE FROM falta_item WHERE processo_id=?;", (pid,))
        elif tipo == "ATESTADOS":
            conn.execute("DELETE FROM atestado_item WHERE processo_id=?;", (pid,))
        elif tipo == "FERIAS":
            conn.execute("DELETE FROM ferias_item WHERE processo_id=?;", (pid,))


# ---------- FALTAS (com seleção manual) ----------
def substituir_faltas(pid: int, itens: List[dict]) -> int:
    dados = [(pid, it.get("codigo"), it.get("cpf"), it.get("nome"),
              float(it.get("atraso_min", 0)), float(it.get("faltas_dias", 0))) for it in itens]
    with transacao() as conn:
        conn.execute("DELETE FROM falta_item WHERE processo_id=?;", (pid,))
        if dados:
            conn.executemany(
                "INSERT INTO falta_item (processo_id, codigo, cpf, nome, atraso_min, faltas_dias, incluir) "
                "VALUES (?, ?, ?, ?, ?, ?, 1);", dados)
    return len(itens)


def listar_faltas(pid: int) -> List[dict]:
    return obter_conexao().execute(
        "SELECT * FROM falta_item WHERE processo_id=? ORDER BY nome;", (pid,)).fetchall()


def definir_inclusao(pid: int, codigo: str, incluir: bool) -> None:
    with transacao() as conn:
        conn.execute("UPDATE falta_item SET incluir=? WHERE processo_id=? AND codigo=?;",
                     (1 if incluir else 0, pid, str(codigo)))


def definir_inclusao_lote(pid: int, mapa_incluir: dict) -> None:
    dados = [(1 if inc else 0, pid, str(cod)) for cod, inc in mapa_incluir.items()]
    with transacao() as conn:
        if dados:
            conn.executemany("UPDATE falta_item SET incluir=? WHERE processo_id=? AND codigo=?;", dados)


def codigos_incluidos(pid: int) -> set:
    rows = obter_conexao().execute(
        "SELECT codigo FROM falta_item WHERE processo_id=? AND incluir=1;", (pid,)).fetchall()
    return set(str(r["codigo"]) for r in rows)


# ---------- ATESTADOS ----------
def substituir_atestados(pid: int, itens: List[dict]) -> int:
    dados = [(pid, it.get("codigo"), it.get("matricula"), it.get("nome"),
              float(it.get("dias", 0)), 1 if it.get("indeterminado") else 0,
              ", ".join(it.get("tipos", []))) for it in itens]
    with transacao() as conn:
        conn.execute("DELETE FROM atestado_item WHERE processo_id=?;", (pid,))
        if dados:
            conn.executemany(
                "INSERT INTO atestado_item (processo_id, codigo, matricula_pontotel, nome, dias, indeterminado, tipos) "
                "VALUES (?, ?, ?, ?, ?, ?, ?);", dados)
    return len(itens)


def listar_atestados(pid: int) -> List[dict]:
    return obter_conexao().execute(
        "SELECT * FROM atestado_item WHERE processo_id=? ORDER BY nome;", (pid,)).fetchall()


# ---------- FÉRIAS (com seleção manual) ----------
def substituir_ferias(pid: int, itens) -> int:
    dados = [(pid, it.get("codigo"), it.get("nome"), it.get("periodo_gozo"),
              float(it.get("dias", 0))) for it in itens]
    with transacao() as conn:
        conn.execute("DELETE FROM ferias_item WHERE processo_id=?;", (pid,))
        if dados:
            conn.executemany(
                "INSERT INTO ferias_item (processo_id, codigo, nome, periodo_gozo, dias, incluir) "
                "VALUES (?, ?, ?, ?, ?, 1);", dados)
    return len(itens)


def listar_ferias(pid: int):
    return obter_conexao().execute(
        "SELECT * FROM ferias_item WHERE processo_id=? ORDER BY nome;", (pid,)).fetchall()


def definir_inclusao_ferias_lote(pid: int, mapa) -> None:
    dados = [(1 if inc else 0, pid, str(cod)) for cod, inc in mapa.items()]
    with transacao() as conn:
        if dados:
            conn.executemany("UPDATE ferias_item SET incluir=? WHERE processo_id=? AND codigo=?;", dados)


def codigos_ferias_incluidos(pid: int) -> set:
    rows = obter_conexao().execute(
        "SELECT codigo FROM ferias_item WHERE processo_id=? AND incluir=1;", (pid,)).fetchall()
    return set(str(r["codigo"]) for r in rows)


# ---------- RESULTADOS ----------
def substituir_resultados(pid: int, resultados: List[dict]) -> int:
    dados = [(pid, r.get("codigo"), r.get("cpf"), r.get("nome"), r.get("cargo"), r.get("departamento"),
              r.get("empresa") or "PISA", r.get("faixa_alim"), float(r.get("valor_base", 0)),
              float(r.get("faltas_dias", 0)), float(r.get("atraso_min", 0)), float(r.get("pct_desconto", 0)),
              float(r.get("valor_final", 0)), float(r.get("pct_recebido", 100)),
              1 if r.get("zerado_por_atestado") else 0, 1 if r.get("zerado_por_ferias") else 0,
              r.get("motivo", "")) for r in resultados]
    with transacao() as conn:
        conn.execute("DELETE FROM resultado_beneficio WHERE processo_id=?;", (pid,))
        if dados:
            conn.executemany(
                "INSERT INTO resultado_beneficio (processo_id, codigo, cpf, nome, cargo, departamento, empresa, faixa_alim, "
                "valor_base, faltas_dias, atraso_min, pct_desconto, valor_final, pct_recebido, "
                "zerado_por_atestado, zerado_por_ferias, motivo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", dados)
    return len(resultados)


def listar_resultados(pid: int) -> List[dict]:
    return obter_conexao().execute(
        "SELECT * FROM resultado_beneficio WHERE processo_id=? ORDER BY nome;", (pid,)).fetchall()


def tem_resultados(pid: int) -> bool:
    return obter_conexao().execute(
        "SELECT 1 FROM resultado_beneficio WHERE processo_id=? LIMIT 1;", (pid,)).fetchone() is not None
