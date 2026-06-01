"""
Gestão de Benefícios — DP/RH (Grupo LLE). App principal Streamlit.

Fluxo de acesso:
  1. Usuário se cadastra (nome, e-mail, senha). Senha NUNCA é compartilhada.
  2. Sistema gera uma "chave de aprovação" única (ex: K7P4-N2X9-B5M1).
  3. Usuário manda essa chave pra Gestão de RH por outro canal (WhatsApp/e-mail).
  4. A Gestão libera de duas formas:
       a) Aprovando direto na tela "Usuários"; OU
       b) Colando a chave em [usuarios_aprovados].chaves nos Streamlit Secrets.
  5. No próximo carregamento o sistema sincroniza e libera o login.

Primeiro usuário cadastrado vira GESTAO_RH e é auto-aprovado (bootstrap).

Rodar localmente:
    streamlit run app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from src.banco import repo_usuario
from src.banco.schema import inicializar_banco
from src.modelos.tipos import PerfilUsuario
from src.utils.estilo import aplicar_css_lle
from src.utils.marca import AZUL_ESCURO, AMARELO, NOME_SISTEMA, NOME_SETOR


st.set_page_config(
    page_title="Benefícios DP/RH",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "banco_inicializado" not in st.session_state:
    inicializar_banco()
    st.session_state["banco_inicializado"] = True

try:
    repo_usuario.sincronizar_aprovacoes_com_secrets()
except Exception:
    pass

aplicar_css_lle()


# ============================================================
# CSS — login (sem sidebar) e logado (sidebar fixa)
# ============================================================

def _esconder_navegacao():
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] { display: none !important; }
            [data-testid="stSidebarNav"] { display: none !important; }
            button[kind="header"] { display: none !important; }
            button[data-testid="collapsedControl"] { display: none !important; }
            header[data-testid="stHeader"] { display: none !important; }
            div[data-testid="stToolbar"] { display: none !important; }
            .block-container { padding-top: 3rem !important; max-width: 600px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _mostrar_navegacao_fixa():
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {
                display: block !important;
                min-width: 260px !important; max-width: 260px !important;
                width: 260px !important; transform: translateX(0px) !important;
                visibility: visible !important; margin-left: 0 !important;
            }
            section[data-testid="stSidebar"] button[kind="header"],
            section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
            button[data-testid="collapsedControl"],
            button[data-testid="stSidebarCollapseButton"] {
                display: none !important; visibility: hidden !important;
                pointer-events: none !important; width: 0 !important;
                height: 0 !important; opacity: 0 !important;
            }
            [data-testid="stSidebarNav"] { display: none !important; }
            header[data-testid="stHeader"] { background: transparent; display: none !important; }
            .main .block-container { padding-left: 2rem !important; padding-right: 2rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SESSION HELPERS
# ============================================================

def usuario_logado():
    return st.session_state.get("usuario_atual")


def logar(usuario):
    st.session_state["usuario_atual"] = usuario


def deslogar():
    for k in list(st.session_state.keys()):
        if k not in ("banco_inicializado",):
            del st.session_state[k]


# ============================================================
# TELA: LOGIN
# ============================================================

def tela_login():
    LOGO = Path(__file__).parent / "assets" / "logo_lle.png"
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.write("")
        if LOGO.exists():
            st.image(str(LOGO), use_container_width=True)
        st.markdown(
            f"""
            <div style="text-align:center; margin-top: -20px; margin-bottom: 24px;">
                <h2 style="color:{AZUL_ESCURO}; margin-bottom: 4px;">{NOME_SISTEMA}</h2>
                <p style="color: #666;">{NOME_SETOR} — acesso restrito à equipe</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.get("usuario_trocando_senha"):
            _tela_troca_senha_forcada()
            return
        if st.session_state.get("chave_recem_gerada"):
            _mostrar_chave_gerada()
            return

        tab_login, tab_cadastro = st.tabs(["🔑 Entrar", "📝 Cadastrar"])
        with tab_login:
            _form_login()
        with tab_cadastro:
            _form_cadastro()


def _form_login():
    with st.form("login", clear_on_submit=False):
        email = st.text_input("E-mail", placeholder="seu.email@grupolle.com.br",
                              autocomplete="username")
        senha = st.text_input("Senha", type="password", autocomplete="current-password")
        entrar = st.form_submit_button("Entrar", use_container_width=True, type="primary")
        if entrar:
            usuario = repo_usuario.autenticar(email.strip(), senha)
            if usuario is None:
                st.error("❌ E-mail ou senha inválidos.")
                return
            if not usuario.ativo:
                st.error("❌ Usuário inativado. Procure a Gestão de RH.")
                return
            if not usuario.aprovado:
                _mostrar_acesso_pendente(usuario)
                return
            if usuario.deve_trocar_senha:
                st.session_state["usuario_trocando_senha"] = usuario
                st.rerun()
                return
            logar(usuario)
            st.success(f"Olá, {usuario.nome}!")
            st.rerun()


def _tela_troca_senha_forcada():
    usuario = st.session_state.get("usuario_trocando_senha")
    if not usuario:
        return
    st.markdown(
        f"""
        <div style="background:#FFF3CD; border-left:4px solid {AMARELO};
                    padding:16px; margin:16px 0; border-radius:6px;">
            <div style="font-weight:700; color:{AZUL_ESCURO}; margin-bottom:8px;">
                🔐 Você precisa definir uma nova senha
            </div>
            <div style="color:#444; font-size:14px;">
                A Gestão de RH redefiniu seu acesso com uma senha temporária.
                Crie agora a sua senha pessoal. Ninguém mais saberá ela.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("trocar_senha_forcada"):
        nova = st.text_input("Nova senha (mín. 8 caracteres)", type="password")
        confirma = st.text_input("Confirme a nova senha", type="password")
        salvar = st.form_submit_button("✓ Salvar e entrar", type="primary",
                                       use_container_width=True)
        if salvar:
            if nova != confirma:
                st.error("❌ As senhas não conferem.")
                return
            try:
                repo_usuario.alterar_senha(usuario.id, nova,
                                           deve_trocar_no_proximo_login=False)
                atualizado = repo_usuario.buscar_por_id(usuario.id)
                del st.session_state["usuario_trocando_senha"]
                logar(atualizado)
                st.success("✓ Senha alterada com sucesso!")
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {e}")


def _form_cadastro():
    st.caption(
        "📝 Preencha seus dados pra criar uma conta. Após o cadastro você recebe "
        "uma **chave de liberação** que deve ser enviada à Gestão de RH. "
        "Ela libera seu acesso e você pode entrar."
    )
    with st.form("cadastro", clear_on_submit=False):
        nome = st.text_input("Nome completo *", placeholder="Ex: Maria Souza",
                             help="Seu nome completo. NÃO use e-mail aqui.")
        email = st.text_input("E-mail *", placeholder="seu.email@grupolle.com.br")
        senha = st.text_input("Senha (mín. 8 caracteres) *", type="password",
                             help="A senha NÃO é compartilhada com ninguém.")
        senha_conf = st.text_input("Confirme a senha *", type="password")
        submitted = st.form_submit_button("Criar conta", use_container_width=True,
                                          type="primary")
        if submitted:
            if not nome or not email or not senha:
                st.error("❌ Preencha todos os campos obrigatórios.")
                return
            if "@" in nome:
                st.error("❌ O campo 'Nome completo' deve ter seu nome, não e-mail.")
                return
            if senha != senha_conf:
                st.error("❌ As senhas não conferem.")
                return
            try:
                perfil_pedido = (
                    PerfilUsuario.GESTAO_RH
                    if not repo_usuario.existe_algum_usuario()
                    else PerfilUsuario.ANALISTA_RH
                )
                novo = repo_usuario.criar_usuario(
                    nome=nome.strip(), email=email.strip(),
                    senha=senha, perfil=perfil_pedido,
                )
                st.session_state["chave_recem_gerada"] = novo.chave_aprovacao
                st.session_state["nome_recem_cadastrado"] = novo.nome
                st.session_state["aprovado_auto"] = novo.aprovado
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {e}")


def _mostrar_chave_gerada():
    chave = st.session_state.get("chave_recem_gerada")
    nome = st.session_state.get("nome_recem_cadastrado", "")
    aprovado_auto = st.session_state.get("aprovado_auto", False)

    st.success(f"✅ Cadastro realizado, {nome.split()[0] if nome else ''}!")
    if aprovado_auto:
        st.info(
            "🎉 **Você é o primeiro usuário** — virou Gestão de RH automaticamente "
            "e já tem acesso liberado. Faça login abaixo."
        )
    else:
        st.markdown(
            f"""
            <div style="background: #FFF3CD; border-left: 4px solid {AMARELO};
                        padding: 16px; margin: 16px 0; border-radius: 6px;">
                <div style="font-weight: 700; color: {AZUL_ESCURO}; margin-bottom: 8px;">
                    ⏳ Seu acesso está PENDENTE de aprovação.
                </div>
                <div style="color: #444; font-size: 14px;">
                    Envie a chave abaixo para a Gestão de RH. Após aprovado, é só fazer login.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div style="background: {AZUL_ESCURO}; color: white; padding: 18px;
                        border-radius: 8px; text-align: center; margin: 16px 0;">
                <div style="font-size: 11px; letter-spacing: 1px; text-transform: uppercase;
                            opacity: 0.7; margin-bottom: 6px;">Chave de liberação</div>
                <div style="font-family: 'Courier New', monospace; font-size: 22px;
                            font-weight: 700; color: {AMARELO}; letter-spacing: 3px;">{chave}</div>
                <div style="font-size: 11px; opacity: 0.7; margin-top: 8px;">
                    Envie esta chave à Gestão de RH</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    if st.button("← Voltar para a tela de login", use_container_width=True, type="primary"):
        for k in ["chave_recem_gerada", "nome_recem_cadastrado", "aprovado_auto"]:
            st.session_state.pop(k, None)
        st.rerun()


def _mostrar_acesso_pendente(usuario):
    st.markdown(
        f"""
        <div style="background: #FFF3CD; border-left: 4px solid {AMARELO};
                    padding: 16px; margin: 16px 0; border-radius: 6px;">
            <div style="font-weight: 700; color: {AZUL_ESCURO}; margin-bottom: 8px;">
                ⏳ Seu acesso ainda está pendente de aprovação.
            </div>
            <div style="color: #444; font-size: 14px;">
                Avise a Gestão de RH que você se cadastrou. Após aprovado,
                recarregue a página e faça login normalmente.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SIDEBAR LOGADO
# ============================================================

def sidebar_logado(usuario):
    from src.utils.auth_guard import renderizar_menu_sidebar
    renderizar_menu_sidebar(usuario)


# ============================================================
# ROTEAMENTO
# ============================================================

def main():
    usuario = usuario_logado()
    if usuario is None:
        _esconder_navegacao()
        tela_login()
    else:
        _mostrar_navegacao_fixa()
        sidebar_logado(usuario)
        from src.telas.inicio import renderizar_inicio
        renderizar_inicio(usuario)


main()
