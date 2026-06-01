"""
Identidade visual do Grupo LLE.
Cores e fonte oficiais conforme Manual da Marca (fev/2026).
NUNCA use cores que não estejam aqui.
"""
from __future__ import annotations

# ============================================================
# CORES OFICIAIS GRUPO LLE
# ============================================================

# Cor primária - azul-marinho institucional
AZUL_ESCURO = "#041747"

# Cor de destaque - amarelo/dourado
AMARELO = "#FAC318"

# Cor de sucesso / valores positivos
VERDE = "#0F8C3B"

# Cor de links / botões secundários
AZUL_VIVO = "#0071FE"

# Neutros
BRANCO = "#FFFFFF"
PRETO = "#000000"

# ============================================================
# CORES DERIVADAS (estados)
# ============================================================

# Erro / desconto total (prêmio zerado)
FUNDO_ATRASO = "#F8D7DA"
TEXTO_ATRASO = "#721C24"

# Sucesso / prêmio integral (100%)
FUNDO_PAGO = "#D4EDDA"
TEXTO_PAGO = "#155724"

# Aviso / prêmio parcial (desconto aplicado)
FUNDO_PARCIAL = "#FFF3CD"
TEXTO_PARCIAL = "#856404"

# Linhas alternadas em tabelas
LINHA_ALTERNADA = "#F2F2F2"

# Bordas finas
BORDA_FINA = "#D9D9D9"

# Cinzas
CINZA_CLARO = "#F8F9FA"
CINZA_MEDIO = "#6C757D"

# ============================================================
# TIPOGRAFIA
# ============================================================

FONTE_PRINCIPAL = "Montserrat"
FONTE_FALLBACK = "Calibri, Arial, sans-serif"

# ============================================================
# IDENTIDADE
# ============================================================

NOME_EMPRESA = "Grupo LLE"
NOME_OPERACAO = "LLE Ferragens"
NOME_SISTEMA = "Gestão de Benefícios"
NOME_SETOR = "DP / RH"
VERSAO = "2026.06.01 · multi-empresa + auditoria"


# ============================================================
# EMPRESAS (Grupo LLE) — separação PISA / KING
# ============================================================

EMPRESAS = ["PISA", "KING"]          # empresas suportadas na separação
EMPRESA_PADRAO = "PISA"

# Cores distintas por empresa (para os gráficos)
COR_EMPRESA = {
    "PISA": AZUL_VIVO,   # azul vivo
    "KING": AMARELO,     # amarelo/dourado
}


def normalizar_empresa(valor) -> str:
    """
    Converte o 'Nome Fantasia (Empresa)' do cadastro (ex.: 'LLE PISA', 'LLE KING')
    na sigla da empresa. Reconhece PISA e KING; senão devolve o texto limpo.
    """
    s = str(valor or "").strip().upper()
    if not s or s == "NAN":
        return EMPRESA_PADRAO
    if "KING" in s:
        return "KING"
    if "PISA" in s:
        return "PISA"
    return s
