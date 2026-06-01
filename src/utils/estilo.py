"""
Aplicação do CSS LLE no Streamlit + helpers de dashboard.
Carrega Montserrat do Google Fonts + variáveis de cor + overrides nos componentes.
"""
from __future__ import annotations

import streamlit as st

from src.utils.marca import (
    AZUL_ESCURO, AMARELO, VERDE, AZUL_VIVO, BRANCO,
    FUNDO_ATRASO, TEXTO_ATRASO, FUNDO_PAGO, TEXTO_PAGO,
    FUNDO_PARCIAL, TEXTO_PARCIAL, LINHA_ALTERNADA, BORDA_FINA,
    CINZA_CLARO, CINZA_MEDIO,
)


def aplicar_css_lle():
    """Injeta CSS global. Chamar uma vez por página."""
    st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    /* Esconde a navegação automática de páginas do Streamlit (usamos o menu próprio) */
    [data-testid="stSidebarNav"],
    div[data-testid="stSidebarNav"],
    ul[data-testid="stSidebarNavItems"],
    [data-testid="stSidebarNavSeparator"] {{ display: none !important; }}

    :root {{
        --lle-azul-escuro: {AZUL_ESCURO};
        --lle-amarelo: {AMARELO};
        --lle-verde: {VERDE};
        --lle-azul-vivo: {AZUL_VIVO};
        --lle-branco: {BRANCO};
        --lle-fundo-atraso: {FUNDO_ATRASO};
        --lle-texto-atraso: {TEXTO_ATRASO};
        --lle-fundo-pago: {FUNDO_PAGO};
        --lle-texto-pago: {TEXTO_PAGO};
        --lle-fundo-parcial: {FUNDO_PARCIAL};
        --lle-texto-parcial: {TEXTO_PARCIAL};
        --lle-linha-alt: {LINHA_ALTERNADA};
        --lle-borda: {BORDA_FINA};
        --lle-cinza-claro: {CINZA_CLARO};
        --lle-cinza-medio: {CINZA_MEDIO};
    }}

    /* Fonte global */
    html, body, [class*="css"], [class*="st-"], button, input, select, textarea {{
        font-family: 'Montserrat', Calibri, Arial, sans-serif !important;
    }}

    /* Títulos */
    h1, h2, h3, h4, h5 {{
        color: var(--lle-azul-escuro) !important;
        font-weight: 700 !important;
    }}

    /* Botões primários */
    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"],
    button[data-testid="baseButton-primary"] {{
        background-color: var(--lle-azul-escuro) !important;
        color: var(--lle-branco) !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color: var(--lle-azul-vivo) !important;
    }}

    /* Botões secundários */
    .stButton > button[kind="secondary"] {{
        border: 1.5px solid var(--lle-azul-escuro) !important;
        color: var(--lle-azul-escuro) !important;
        font-weight: 600 !important;
        background-color: var(--lle-branco) !important;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: var(--lle-azul-escuro) !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: var(--lle-branco) !important;
    }}
    section[data-testid="stSidebar"] .stButton > button {{
        background-color: rgba(255,255,255,0.08) !important;
        color: var(--lle-branco) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background-color: var(--lle-amarelo) !important;
        color: var(--lle-azul-escuro) !important;
        border-color: var(--lle-amarelo) !important;
    }}

    /* FIX: ícones Material quebrados aparecendo como texto cru */
    span[data-testid="stIconMaterial"],
    span.material-icons,
    span.material-symbols-outlined,
    span.material-symbols-rounded,
    span[class*="stIconMaterial"] {{
        font-family: 'Material Symbols Outlined', 'Material Symbols Rounded',
                     'Material Icons' !important;
        font-weight: normal !important;
        font-style: normal !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-block !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-feature-settings: 'liga' !important;
        -webkit-font-smoothing: antialiased !important;
    }}
    @supports not (font-variation-settings: normal) {{
        span[data-testid="stIconMaterial"],
        span.material-icons,
        span.material-symbols-outlined,
        span.material-symbols-rounded {{
            color: transparent !important;
            font-size: 0 !important;
        }}
    }}
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=block');

    /* Botão de toggle da sidebar */
    button[data-testid="collapsedControl"] {{
        background: var(--lle-azul-escuro) !important;
        border: 1px solid var(--lle-amarelo) !important;
        border-radius: 6px !important;
        color: var(--lle-amarelo) !important;
        padding: 6px 10px !important;
        font-size: 0 !important;
        min-width: 36px !important;
        min-height: 36px !important;
    }}
    button[data-testid="collapsedControl"] * {{
        font-size: 0 !important;
        color: transparent !important;
    }}
    button[data-testid="collapsedControl"]::before {{
        content: "☰" !important;
        font-size: 20px !important;
        color: var(--lle-amarelo) !important;
        display: inline-block !important;
        line-height: 1 !important;
    }}

    /* File uploader */
    section[data-testid="stFileUploaderDropzone"] {{
        border: 2px dashed var(--lle-azul-escuro) !important;
        border-radius: 8px !important;
        background-color: #F8F9FA !important;
        padding: 16px !important;
    }}
    section[data-testid="stFileUploaderDropzone"]:hover {{
        border-color: var(--lle-azul-vivo) !important;
        background-color: #EFF6FF !important;
    }}
    section[data-testid="stFileUploaderDropzone"] button {{
        background-color: var(--lle-azul-escuro) !important;
        color: var(--lle-branco) !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
    }}

    /* Cards de métrica */
    div[data-testid="stMetricValue"] {{
        color: var(--lle-azul-escuro) !important;
        font-weight: 700 !important;
    }}
    div[data-testid="stMetricLabel"] {{
        color: var(--lle-cinza-medio) !important;
        font-weight: 500 !important;
    }}

    /* Tabelas */
    .stDataFrame thead th {{
        background-color: var(--lle-azul-escuro) !important;
        color: var(--lle-branco) !important;
        font-weight: 600 !important;
    }}

    /* Inputs */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox select {{
        border-radius: 6px !important;
        border: 1.5px solid var(--lle-borda) !important;
    }}

    /* Badges */
    .lle-badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
    }}
    .lle-badge-integral {{ background: {FUNDO_PAGO}; color: {TEXTO_PAGO}; }}
    .lle-badge-parcial  {{ background: {FUNDO_PARCIAL}; color: {TEXTO_PARCIAL}; }}
    .lle-badge-zerado   {{ background: {FUNDO_ATRASO}; color: {TEXTO_ATRASO}; }}
    .lle-badge-andamento {{ background: {AMARELO}55; color: #856404; }}
    .lle-badge-finalizado {{ background: {VERDE}; color: white; }}

    /* Card simples */
    .lle-card {{
        background: white;
        border: 1px solid var(--lle-borda);
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
        transition: box-shadow 0.2s;
    }}
    .lle-card:hover {{
        box-shadow: 0 2px 8px rgba(4,23,71,0.1);
        border-color: var(--lle-azul-vivo);
    }}

    /* Padding do app */
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px;
    }}

    header[data-testid="stHeader"] {{ background: transparent; }}
    footer {{ visibility: hidden; }}
</style>
    """, unsafe_allow_html=True)


# ============================================================
# CORES PADRÃO PRA KPIs
# ============================================================
COR_AZUL = "#0071FE"
COR_VERDE = "#0F8C3B"
COR_LARANJA = "#FF8C00"
COR_VERMELHO = "#DC3545"
COR_CINZA = "#6C757D"
COR_AMARELO = "#FAC318"
COR_AZUL_ESCURO = AZUL_ESCURO


# ============================================================
# HELPERS DE DASHBOARD
# ============================================================

def card_kpi(titulo: str, valor: str, sublabel: str = "", cor: str = COR_AZUL,
             icone: str = "") -> str:
    """
    Card de KPI. Use com st.markdown(card_kpi(...), unsafe_allow_html=True).
    """
    return f"""
    <div style="background:#FFF; border-left:5px solid {cor};
                padding:14px 18px; border-radius:8px;
                box-shadow:0 1px 4px rgba(0,0,0,0.08); height:105px;
                margin-bottom:8px;">
        <div style="font-size:12px; color:#666; font-weight:600; margin-bottom:6px;">
            {icone} {titulo}
        </div>
        <div style="font-size:22px; font-weight:800; color:{cor}; line-height:1.1;">
            {valor}
        </div>
        <div style="font-size:11px; color:#999; margin-top:4px;">{sublabel}</div>
    </div>
    """


def badge_faixa(pct_recebido: float) -> str:
    """Badge colorido conforme o quanto do prêmio o funcionário recebeu."""
    p = float(pct_recebido)
    if p >= 100:
        return '<span class="lle-badge lle-badge-integral">✓ 100% integral</span>'
    if p <= 0:
        return '<span class="lle-badge lle-badge-zerado">✕ Zerado</span>'
    return f'<span class="lle-badge lle-badge-parcial">● {p:.0f}%</span>'


def badge_status_processo(status: str) -> str:
    if status == "FINALIZADO":
        return '<span class="lle-badge lle-badge-finalizado">✓ Finalizado</span>'
    return '<span class="lle-badge lle-badge-andamento">● Em andamento</span>'


# ============================================================
# FORMATAÇÃO BRASILEIRA DE NÚMEROS
# ============================================================

def fmt_real(valor) -> str:
    """
    Formata um valor numérico como Real brasileiro.
    Exemplo: 1500.5 → 'R$ 1.500,50' | 0 → 'R$ 0,00' | None → 'R$ 0,00'
    """
    if valor is None:
        valor = 0.0
    try:
        v = float(valor)
    except (TypeError, ValueError):
        v = 0.0
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(valor) -> str:
    """Formata percentual: 8,5 → '8,5%'."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        v = 0.0
    return f"{v:.1f}".replace(".", ",") + "%"
