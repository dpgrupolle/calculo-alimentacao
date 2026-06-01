"""Tradutor central de códigos internos pra nomes amigáveis."""
from __future__ import annotations


PERFIS = {
    "GESTAO_RH": "Gestão de RH",
    "ANALISTA_RH": "Analista de RH",
    "DIRETORIA": "Diretoria",
}

STATUS_PROCESSO = {
    "EM_ANDAMENTO": "Em andamento",
    "FINALIZADO": "Finalizado",
}

PASSOS = {
    1: "1 — Funcionários",
    2: "2 — Ponto",
    3: "3 — Planilha da operadora",
}

TIPO_OCORRENCIA = {
    "FALTA": "Falta",
    "ATRASO": "Atraso",
    "ATESTADO": "Atestado",
    "SAIDA_ANTECIPADA": "Saída antecipada",
    "FALTA_JUSTIFICADA": "Falta justificada",
    "SUSPENSAO": "Suspensão",
    "OUTRO": "Outro",
}

ACOES = {
    "LOGIN": "Fez login",
    "CRIAR_USUARIO": "Cadastrou usuário",
    "APROVAR_USUARIO": "Aprovou usuário",
    "RECUSAR_USUARIO": "Recusou usuário",
    "INATIVAR_USUARIO": "Inativou usuário",
    "REATIVAR_USUARIO": "Reativou usuário",
    "ALTERAR_PERFIL_USUARIO": "Alterou cargo do usuário",
    "REDEFINIR_SENHA_USUARIO": "Redefiniu senha de usuário",
    "TROCAR_PROPRIA_SENHA": "Alterou a própria senha",
    "EDITAR_TABELA": "Editou tabela de prêmio",
    "EDITAR_REGRA": "Editou regra de desconto",
    "UPLOAD_FUNCIONARIOS": "Subiu planilha de funcionários",
    "UPLOAD_PONTO": "Subiu planilha de ponto",
    "PROCESSAR": "Processou o benefício",
    "FINALIZAR_PROCESSO": "Finalizou processo",
    "GERAR_PLANILHA_SAIDA": "Gerou planilha da operadora",
    "EXCLUIR_PROCESSO": "Excluiu processo",
    "EXCLUIR_UPLOAD": "Excluiu envio de planilha",
    "IMPORTAR_FUNCIONARIOS": "Importou funcionários",
}


def traduzir_perfil(codigo: str) -> str:
    return PERFIS.get(codigo, _humanizar(codigo))


def traduzir_status_processo(codigo: str) -> str:
    return STATUS_PROCESSO.get(codigo, _humanizar(codigo))


def traduzir_passo(codigo: int) -> str:
    return PASSOS.get(int(codigo), str(codigo))


def traduzir_tipo_ocorrencia(codigo: str) -> str:
    return TIPO_OCORRENCIA.get(codigo, _humanizar(codigo))


def traduzir_acao(codigo: str) -> str:
    return ACOES.get(codigo, _humanizar(codigo))


def _humanizar(codigo: str) -> str:
    if not codigo:
        return ""
    palavras = str(codigo).replace("_", " ").lower().split()
    return " ".join(p.capitalize() for p in palavras)
