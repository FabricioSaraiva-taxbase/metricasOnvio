import streamlit as st
import requests
import json
import os
import hashlib
import time
import base64

# --- ARQUIVOS DE DADOS (BANCO DE DADOS JSON) ---
DB_SISTEMAS = "sistemas_taxbase.json"
DB_USUARIOS = "usuarios_taxbase.json"
DB_FUNCOES = "funcoes_taxbase.json"

# --- CREDENCIAIS PADRÃO DO ADM MASTER ---
ADM_EMAIL = "admin@taxbase.com.br"
ADM_SENHA_PADRAO = "Taxbase2025"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Taxbase Hub", page_icon="🔷", layout="wide")

# --- CSS ULTRA PREMIUM - DESIGN OUSADO ---
st.markdown("""
    <style>
    /* ============================================
       FONTES PROFISSIONAIS
    ============================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&display=swap');
    
    /* ============================================
       ANIMAÇÕES AVANÇADAS
    ============================================ */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 5px rgba(0, 155, 214, 0.5), 0 0 10px rgba(0, 155, 214, 0.3); }
        50% { box-shadow: 0 0 20px rgba(0, 155, 214, 0.8), 0 0 30px rgba(0, 155, 214, 0.4); }
    }
    
    @keyframes pulseOnline {
        0%, 100% { 
            transform: scale(1);
            box-shadow: 0 0 0 0 rgba(39, 174, 96, 0.7);
        }
        50% { 
            transform: scale(1.05);
            box-shadow: 0 0 0 10px rgba(39, 174, 96, 0);
        }
    }
    
    @keyframes pulseOffline {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    @keyframes pulseMaintenance {
        0%, 100% { 
            background-position: 0% 50%;
        }
        50% { 
            background-position: 100% 50%;
        }
    }
    
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    
    @keyframes borderGlow {
        0%, 100% { border-color: rgba(0, 155, 214, 0.3); }
        50% { border-color: rgba(0, 155, 214, 0.8); }
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* ============================================
       REMOVER ELEMENTOS PADRÃO DO STREAMLIT
    ============================================ */
    div[data-testid="stToolbar"] {visibility: hidden; height: 0%; position: fixed;}
    div[data-testid="stDecoration"] {visibility: hidden; height: 0%; position: fixed;}
    div[data-testid="stStatusWidget"] {visibility: hidden; height: 0%; position: fixed;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    [data-testid="stSidebar"] {display: none;}
    section[data-testid="stSidebarContent"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}

    /* ============================================
       VARIÁVEIS DE CORES - PALETA TAXBASE
    ============================================ */
    :root { 
        --taxbase-blue: #009BD6;
        --taxbase-blue-dark: #007CA3;
        --taxbase-blue-light: #E8F6FC;
        --taxbase-blue-glow: rgba(0, 155, 214, 0.4);
        --taxbase-dark: #2C3E50;
        --taxbase-darker: #1a252f;
        --taxbase-gray: #7F8C8D;
        --taxbase-light-gray: #BDC3C7;
        --bg-gradient: linear-gradient(135deg, #f5f7fa 0%, #e4e9f0 50%, #f0f4f8 100%);
        --border-color: rgba(0, 155, 214, 0.15);
        --success: #27AE60;
        --success-glow: rgba(39, 174, 96, 0.4);
        --warning: #F39C12;
        --warning-glow: rgba(243, 156, 18, 0.4);
        --danger: #E74C3C;
        --danger-glow: rgba(231, 76, 60, 0.4);
    }

    /* ============================================
       FUNDO DA APLICAÇÃO - MESH GRADIENT
    ============================================ */
    .stApp { 
        background: 
            radial-gradient(ellipse at 20% 0%, rgba(0, 155, 214, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 100%, rgba(0, 155, 214, 0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 40% 80%, rgba(39, 174, 96, 0.04) 0%, transparent 40%),
            linear-gradient(180deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%);
        color: var(--taxbase-dark);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        min-height: 100vh;
    }
    
    p, label, h1, h2, h3, h4, h5, li, span {
        color: var(--taxbase-dark);
        font-family: 'Inter', sans-serif;
    }

    /* ============================================
       LAYOUT GLOBAL
    ============================================ */
    .stMainBlockContainer {
        padding-top: 1rem !important;
    }
    
    hr {
        margin: 1.5rem 0 !important;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--taxbase-blue), transparent);
        opacity: 0.3;
    }

    /* ============================================
       BOTÕES - ESTILO NEON PREMIUM
    ============================================ */
    div.stButton > button {
        background: linear-gradient(135deg, var(--taxbase-blue) 0%, var(--taxbase-blue-dark) 100%);
        color: white !important; 
        border-radius: 14px; 
        border: none;
        white-space: pre-wrap !important; 
        min-height: 52px; 
        line-height: 1.4 !important;
        width: 100%;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 
            0 4px 15px rgba(0, 155, 214, 0.35),
            0 0 0 0 rgba(0, 155, 214, 0);
        position: relative;
        overflow: hidden;
    }
    
    div.stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.5s;
    }
    
    div.stButton > button:hover { 
        background: linear-gradient(135deg, var(--taxbase-blue-dark) 0%, #005f7a 100%);
        transform: translateY(-4px) scale(1.02);
        box-shadow: 
            0 8px 25px rgba(0, 155, 214, 0.45),
            0 0 30px rgba(0, 155, 214, 0.2);
    }
    
    div.stButton > button:hover::before {
        left: 100%;
    }

    /* ============================================
       CARDS DE SISTEMA - GLASSMORPHISM AVANÇADO
    ============================================ */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        padding: 1.8rem; 
        border-radius: 20px;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.08),
            0 0 0 1px rgba(255, 255, 255, 0.8) inset;
        border: 1px solid rgba(0, 155, 214, 0.1);
        transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        animation: fadeInUp 0.6s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--taxbase-blue), #00d4ff, var(--taxbase-blue));
        background-size: 200% 100%;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"]:hover {
        box-shadow: 
            0 20px 60px rgba(0, 155, 214, 0.15),
            0 0 0 1px rgba(0, 155, 214, 0.3) inset,
            0 0 40px rgba(0, 155, 214, 0.1);
        transform: translateY(-8px) scale(1.01);
        border-color: rgba(0, 155, 214, 0.4);
    }
    
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"]:hover::before {
        opacity: 1;
        animation: gradientShift 2s ease infinite;
    }

    /* ============================================
       INPUTS - ESTILO MODERNO
    ============================================ */
    input, textarea, select {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: var(--taxbase-dark) !important;
        caret-color: var(--taxbase-blue) !important;
        font-family: 'Inter', sans-serif !important;
        border-radius: 12px !important;
        font-size: 0.95rem !important;
    }

    div[data-baseweb="base-input"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 12px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    div[data-baseweb="base-input"]:focus-within {
        border-color: var(--taxbase-blue) !important;
        box-shadow: 
            0 0 0 4px rgba(0, 155, 214, 0.15),
            0 4px 20px rgba(0, 155, 214, 0.1) !important;
        background-color: white !important;
    }

    /* ============================================
       CENTRALIZAR IMAGENS
    ============================================ */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }
    
    /* ============================================
       BADGES DE FUNÇÃO - STYLE CHIPS
    ============================================ */
    .funcao-badge {
        background: linear-gradient(135deg, var(--taxbase-blue) 0%, var(--taxbase-blue-dark) 100%);
        color: white;
        padding: 8px 20px;
        border-radius: 30px;
        font-size: 0.75rem;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        letter-spacing: 1px;
        text-transform: uppercase;
        box-shadow: 
            0 4px 15px rgba(0, 155, 214, 0.4),
            0 0 20px rgba(0, 155, 214, 0.2);
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    
    .funcao-badge.usuario {
        background: linear-gradient(135deg, var(--success) 0%, #1d8348 100%);
        box-shadow: 
            0 4px 15px var(--success-glow),
            0 0 20px rgba(39, 174, 96, 0.2);
    }
    
    .funcao-badge.admin {
        background: linear-gradient(135deg, var(--danger) 0%, #c0392b 100%);
        box-shadow: 
            0 4px 15px var(--danger-glow),
            0 0 20px rgba(231, 76, 60, 0.2);
    }

    /* ============================================
       SISTEMA DE STATUS - DESIGN PREMIUM
    ============================================ */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 30px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.75rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        transition: all 0.3s ease;
    }
    
    .status-badge.online {
        background: linear-gradient(135deg, rgba(39, 174, 96, 0.15) 0%, rgba(39, 174, 96, 0.05) 100%);
        color: #1d8348;
        border: 2px solid rgba(39, 174, 96, 0.4);
        animation: pulseOnline 2s ease-in-out infinite;
    }
    
    .status-badge.online .status-dot {
        width: 10px;
        height: 10px;
        background: var(--success);
        border-radius: 50%;
        box-shadow: 0 0 10px var(--success), 0 0 20px var(--success-glow);
    }
    
    .status-badge.offline {
        background: linear-gradient(135deg, rgba(231, 76, 60, 0.15) 0%, rgba(231, 76, 60, 0.05) 100%);
        color: #c0392b;
        border: 2px solid rgba(231, 76, 60, 0.4);
    }
    
    .status-badge.offline .status-dot {
        width: 10px;
        height: 10px;
        background: var(--danger);
        border-radius: 50%;
        animation: pulseOffline 1.5s ease-in-out infinite;
    }
    
    .status-badge.manutencao {
        background: linear-gradient(90deg, rgba(243, 156, 18, 0.2) 0%, rgba(243, 156, 18, 0.1) 50%, rgba(243, 156, 18, 0.2) 100%);
        background-size: 200% 100%;
        color: #d68910;
        border: 2px solid rgba(243, 156, 18, 0.5);
        animation: pulseMaintenance 2s ease-in-out infinite;
    }
    
    .status-badge.manutencao .status-dot {
        width: 10px;
        height: 10px;
        background: linear-gradient(135deg, var(--warning), #e67e22);
        border-radius: 50%;
        box-shadow: 0 0 10px var(--warning);
    }

    /* ============================================
       HEADER DA PÁGINA PRINCIPAL
    ============================================ */
    .header-premium {
        background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,250,252,0.9) 100%);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 1.5rem 2rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(0, 155, 214, 0.1);
        box-shadow: 
            0 10px 40px rgba(0, 0, 0, 0.06),
            0 0 0 1px rgba(255,255,255,0.8) inset;
    }

    /* ============================================
       BARRA DE BUSCA - STYLE COMMAND
    ============================================ */
    div[data-testid="stTextInput"] > div {
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: 16px !important;
        box-shadow: 
            0 4px 20px rgba(0, 0, 0, 0.06),
            0 0 0 2px rgba(0, 155, 214, 0.1);
        border: none !important;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stTextInput"] > div:focus-within {
        box-shadow: 
            0 8px 30px rgba(0, 155, 214, 0.15),
            0 0 0 3px rgba(0, 155, 214, 0.3);
    }

    /* ============================================
       FOOTER PREMIUM
    ============================================ */
    .footer-modern {
        text-align: center;
        padding: 2rem;
        color: var(--taxbase-gray);
        font-size: 0.85rem;
        font-family: 'Inter', sans-serif;
        border-top: 2px solid rgba(0, 155, 214, 0.1);
        margin-top: 3rem;
        background: linear-gradient(180deg, transparent 0%, rgba(0, 155, 214, 0.03) 100%);
    }
    
    .footer-modern span {
        font-weight: 700;
        background: linear-gradient(135deg, var(--taxbase-blue), var(--taxbase-blue-dark));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* ============================================
       LINK BUTTONS
    ============================================ */
    a[data-testid="stBaseLinkButton"] {
        background: linear-gradient(135deg, var(--taxbase-blue) 0%, var(--taxbase-blue-dark) 100%) !important;
        border-radius: 14px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 4px 15px rgba(0, 155, 214, 0.35) !important;
    }
    
    a[data-testid="stBaseLinkButton"]:hover {
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 
            0 8px 25px rgba(0, 155, 214, 0.45),
            0 0 30px rgba(0, 155, 214, 0.2) !important;
    }

    /* ============================================
       EXPANDERS E CONTAINERS
    ============================================ */
    div[data-testid="stExpander"] {
        border-radius: 16px;
        border: 1px solid rgba(0, 155, 214, 0.15);
        overflow: hidden;
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
    }
    
    div[data-testid="stExpander"] summary {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        padding: 1rem;
    }

    /* ============================================
       CATEGORIA TAG
    ============================================ */
    .categoria-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        background: linear-gradient(135deg, var(--taxbase-blue-light) 0%, rgba(0, 155, 214, 0.1) 100%);
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--taxbase-blue-dark);
        font-family: 'Inter', sans-serif;
        border: 1px solid rgba(0, 155, 214, 0.2);
    }

    /* ============================================
       CARD HEADER COM INDICADOR
    ============================================ */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
    }
    
    .card-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: var(--taxbase-dark);
        font-family: 'Inter', sans-serif;
        margin: 0;
        line-height: 1.3;
    }

    /* ============================================
       DESCRIÇÃO DO SISTEMA
    ============================================ */
    .sistema-desc {
        color: var(--taxbase-gray);
        font-size: 0.9rem;
        line-height: 1.5;
        margin: 12px 0 16px 0;
        font-family: 'Inter', sans-serif;
    }

    /* ============================================
       CONTAINER DE BORDA DO STREAMLIT
    ============================================ */
    div[data-testid="stBorderContainer"] {
        border-radius: 20px !important;
        border: 1px solid rgba(0, 155, 214, 0.15) !important;
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06) !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    div[data-testid="stBorderContainer"]:hover {
        box-shadow: 
            0 20px 50px rgba(0, 155, 214, 0.12),
            0 0 40px rgba(0, 155, 214, 0.05) !important;
        transform: translateY(-6px);
        border-color: rgba(0, 155, 214, 0.35) !important;
    }
    </style>
    """, unsafe_allow_html=True)


# --- FUNÇÕES DE SEGURANÇA E ARQUIVOS ---
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def carregar_json(arquivo):
    if not os.path.exists(arquivo): return []
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


# --- FUNÇÕES DE PERMISSÕES ---
def carregar_funcoes():
    """Carrega todas as funções disponíveis"""
    return carregar_json(DB_FUNCOES)


def obter_funcao_por_id(funcao_id):
    """Retorna os dados completos de uma função pelo ID"""
    funcoes = carregar_funcoes()
    for funcao in funcoes:
        if funcao['id'] == funcao_id:
            return funcao
    return None


def obter_funcao_usuario(email):
    """Retorna a função completa de um usuário pelo email"""
    usuarios = carregar_json(DB_USUARIOS)
    for u in usuarios:
        if u['email'] == email:
            funcao_id = u.get('funcao_id', 'admin_master' if email == ADM_EMAIL else None)
            if funcao_id:
                return obter_funcao_por_id(funcao_id)
    return None


def usuario_tem_acesso_sistema(funcao, sistema_id):
    """Verifica se a função tem acesso a um sistema específico"""
    if not funcao:
        return False
    sistemas_permitidos = funcao.get('sistemas', [])
    return '*' in sistemas_permitidos or sistema_id in sistemas_permitidos


def filtrar_sistemas_por_funcao(sistemas, funcao):
    """Filtra sistemas baseado na função do usuário"""
    if not funcao:
        return []
    sistemas_permitidos = funcao.get('sistemas', [])
    if '*' in sistemas_permitidos:
        return sistemas
    return [s for s in sistemas if s.get('sistema_id') in sistemas_permitidos]


# --- VERIFICAÇÃO INICIAL (CRIAR ADMIN SE NÃO EXISTIR) ---
if not os.path.exists(DB_USUARIOS) or not carregar_json(DB_USUARIOS):
    usuarios_iniciais = [{
        "email": ADM_EMAIL,
        "nome": "Administrador",
        "funcao_id": "admin_master",
        "senha": hash_senha(ADM_SENHA_PADRAO)
    }]
    salvar_json(DB_USUARIOS, usuarios_iniciais)


# --- FUNÇÕES DE LÓGICA ---
def verificar_login(email, senha):
    usuarios = carregar_json(DB_USUARIOS)
    senha_hash = hash_senha(senha)
    for u in usuarios:
        if u['email'] == email and u['senha'] == senha_hash:
            return u
    return None


def criar_novo_usuario(email, nome, funcao_id, senha):
    usuarios = carregar_json(DB_USUARIOS)
    if any(u['email'] == email for u in usuarios):
        return False, "E-mail já cadastrado."
    usuarios.append({
        "email": email,
        "nome": nome,
        "funcao_id": funcao_id,
        "senha": hash_senha(senha)
    })
    salvar_json(DB_USUARIOS, usuarios)
    return True, "Usuário criado com sucesso!"


@st.cache_data(ttl=60)
def check_ping(url):
    try:
        r = requests.get(url, timeout=2)
        return True if r.status_code == 200 else False
    except:
        return False


def obter_status_sistema(sistema):
    modo = sistema.get("status_manual", "Automático")
    if modo == "Manutenção":
        return "🟠 Manutenção", "orange"
    elif modo == "Forçar Offline":
        return "🔴 Offline", "red"
    elif modo == "Forçar Online":
        return "🟢 Online", "green"
    else:
        online = check_ping(sistema['url'])
        return ("🟢 Online", "green") if online else ("🔴 Offline", "red")


# --- CONTROLE DE SESSÃO ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario_atual' not in st.session_state: st.session_state['usuario_atual'] = ""
if 'usuario_nome' not in st.session_state: st.session_state['usuario_nome'] = ""
if 'usuario_funcao' not in st.session_state: st.session_state['usuario_funcao'] = None
if 'permissao' not in st.session_state: st.session_state['permissao'] = "usuario"

# ==============================================================================
# 1. TELA DE LOGIN
# ==============================================================================
if not st.session_state['logado']:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.write("")
        st.write("")
        st.write("")
        with st.container(border=True):

            # --- ÁREA DE LOGO LOGIN ---
            l_vazio_esq, l_meio_conteudo, l_vazio_dir = st.columns([0.5, 4, 0.5])

            with l_meio_conteudo:
                nome_arquivo_logo = "logo_taxbase.png"
                if os.path.exists(nome_arquivo_logo):
                    st.image(nome_arquivo_logo, width=300)
                else:
                    st.markdown("## 🔷 Taxbase Hub")
                    st.caption("Sem logo")
            # --------------------

            email_login = st.text_input("E-mail corporativo")
            senha_login = st.text_input("Senha", type="password")

            if st.button("Entrar no Hub", use_container_width=True):
                usuario = verificar_login(email_login, senha_login)
                if usuario:
                    funcao = obter_funcao_usuario(email_login)
                    st.session_state['logado'] = True
                    st.session_state['usuario_atual'] = email_login
                    st.session_state['usuario_nome'] = usuario.get('nome', email_login)
                    st.session_state['usuario_funcao'] = funcao
                    st.session_state['permissao'] = funcao.get('permissao', 'usuario') if funcao else 'usuario'
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
    st.stop()

# ==============================================================================
# 2. ÁREA LOGADA
# ==============================================================================
SISTEMAS = carregar_json(DB_SISTEMAS)
usuario_atual = st.session_state['usuario_atual']
usuario_nome = st.session_state['usuario_nome']
usuario_funcao = st.session_state['usuario_funcao']
permissao_atual = st.session_state['permissao']
is_admin_master = (usuario_atual == ADM_EMAIL)
is_admin = (permissao_atual == 'admin')

# Adicionar sistema_id aos sistemas existentes se não existir
for sis in SISTEMAS:
    if 'sistema_id' not in sis:
        # Gerar ID baseado no nome
        nome_upper = sis['nome'].upper().replace(' ', '_')
        sis['sistema_id'] = nome_upper

# Filtrar sistemas baseado na função
SISTEMAS_VISIVEIS = filtrar_sistemas_por_funcao(SISTEMAS, usuario_funcao)


# --- MODAL (POP-UP) ---
@st.dialog("⚙️ Painel de Gestão")
def abrir_painel_gestao():
    lista_abas = ["➕ Novo Sistema", "✏️ Editar/Excluir"]
    if is_admin:
        lista_abas.append("👤 Usuários")
    if is_admin_master:
        lista_abas.append("🎭 Funções")

    tabs = st.tabs(lista_abas)

    # ABA 1: ADICIONAR
    with tabs[0]:
        st.caption("Preencha para adicionar um novo atalho.")
        with st.form("form_novo_sys", clear_on_submit=True):
            f_nome = st.text_input("Nome do Sistema")
            f_id = st.text_input("ID do Sistema (Ex: AUDIT_FISCAL)")
            f_url = st.text_input("URL (Link Completo)")
            f_cat = st.text_input("Categoria (Ex: Fiscal, RH)")
            f_desc = st.text_input("Descrição Curta")

            if st.form_submit_button("Salvar Sistema"):
                if f_nome and f_url and f_id:
                    SISTEMAS.append({
                        "nome": f_nome, 
                        "sistema_id": f_id.upper(),
                        "url": f_url, 
                        "categoria": f_cat,
                        "desc": f_desc, 
                        "status_manual": "Automático"
                    })
                    salvar_json(DB_SISTEMAS, SISTEMAS)
                    st.success("Adicionado com sucesso!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Nome, ID e URL são obrigatórios.")

    # ABA 2: EDITAR / EXCLUIR
    with tabs[1]:
        if not SISTEMAS:
            st.info("Nenhum sistema cadastrado.")
        else:
            opcoes = [f"{i}: {s['nome']}" for i, s in enumerate(SISTEMAS)]
            sel = st.selectbox("Selecione para editar:", options=opcoes)

            if sel:
                idx = int(sel.split(":")[0])
                sis = SISTEMAS[idx]

                st.markdown(f"**Editando:** {sis['nome']}")
                st.caption("Controle de Status (TI)")
                st_atual = sis.get("status_manual", "Automático")
                l_st = ["Automático", "Manutenção", "Forçar Online", "Forçar Offline"]
                novo_st = st.selectbox("Status:", l_st, index=l_st.index(st_atual))

                c_salvar, c_del = st.columns(2)
                if c_salvar.button("💾 Atualizar Status"):
                    SISTEMAS[idx]["status_manual"] = novo_st
                    salvar_json(DB_SISTEMAS, SISTEMAS)
                    st.success("Atualizado!")
                    time.sleep(1)
                    st.rerun()

                if c_del.button("🗑️ Excluir Sistema", type="primary"):
                    SISTEMAS.pop(idx)
                    salvar_json(DB_SISTEMAS, SISTEMAS)
                    st.rerun()

    # ABA 3: USUÁRIOS (para admins)
    if is_admin and len(tabs) > 2:
        with tabs[2]:
            st.markdown("#### 👤 Gerenciar Usuários")
            
            # Listar usuários existentes
            usuarios = carregar_json(DB_USUARIOS)
            funcoes = carregar_funcoes()
            opcoes_funcao = {f['nome']: f['id'] for f in funcoes}
            
            # Lista de usuários com opções de editar/excluir
            for idx, u in enumerate(usuarios):
                funcao_user = obter_funcao_por_id(u.get('funcao_id', ''))
                nome_funcao = funcao_user['nome'] if funcao_user else 'Sem função'
                perm = funcao_user.get('permissao', 'usuario') if funcao_user else 'usuario'
                badge_class = 'admin' if perm == 'admin' else 'usuario'
                
                with st.expander(f"👤 {u.get('nome', u['email'])} - {nome_funcao}", expanded=False):
                    col_info, col_acoes = st.columns([2, 1])
                    
                    with col_info:
                        st.markdown(f"**Email:** {u['email']}")
                        st.markdown(f"**Função atual:** {nome_funcao}")
                    
                    with col_acoes:
                        # Editar função do usuário
                        nova_funcao = st.selectbox(
                            "Alterar função:", 
                            options=list(opcoes_funcao.keys()),
                            index=list(opcoes_funcao.values()).index(u.get('funcao_id', '')) if u.get('funcao_id', '') in opcoes_funcao.values() else 0,
                            key=f"edit_func_{idx}"
                        )
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("💾 Salvar", key=f"save_user_{idx}"):
                                usuarios[idx]['funcao_id'] = opcoes_funcao[nova_funcao]
                                salvar_json(DB_USUARIOS, usuarios)
                                st.success("Atualizado!")
                                time.sleep(1)
                                st.rerun()
                        
                        with c2:
                            # Não permitir excluir o admin master
                            if u['email'] != ADM_EMAIL:
                                if st.button("🗑️ Excluir", key=f"del_user_{idx}", type="secondary"):
                                    usuarios.pop(idx)
                                    salvar_json(DB_USUARIOS, usuarios)
                                    st.rerun()
                            else:
                                st.caption("Admin Master")
            
            st.markdown("---")
            st.markdown("#### ➕ Novo Usuário")
            with st.form("form_user", clear_on_submit=True):
                u_nome = st.text_input("Nome Completo")
                u_mail = st.text_input("E-mail")
                u_funcao = st.selectbox("Função", options=list(opcoes_funcao.keys()))
                u_pass = st.text_input("Senha Temporária", type="password")
                
                if st.form_submit_button("✅ Criar Usuário"):
                    if u_nome and u_mail and u_pass:
                        funcao_id = opcoes_funcao[u_funcao]
                        ok, msg = criar_novo_usuario(u_mail, u_nome, funcao_id, u_pass)
                        if ok:
                            st.success(msg)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Preencha todos os campos.")
    
    # ABA 4: FUNÇÕES (somente admin master)
    if is_admin_master and len(tabs) > 3:
        with tabs[3]:
            st.markdown("#### 🎭 Gerenciar Funções/Cargos")
            funcoes = carregar_funcoes()
            sistemas_disponiveis = [s.get('sistema_id', '') for s in SISTEMAS]
            
            # Listar funções com opções de editar/excluir
            for idx, f in enumerate(funcoes):
                perm = f.get('permissao', 'usuario')
                badge_class = 'admin' if perm == 'admin' else 'usuario'
                sistemas_txt = ', '.join(f.get('sistemas', []))
                
                with st.expander(f"🎭 {f['nome']} - {perm.upper()}", expanded=False):
                    col1, col2 = st.columns([1.5, 1])
                    
                    with col1:
                        st.markdown(f"**ID:** `{f['id']}`")
                        st.markdown(f"**Descrição:** {f.get('descricao', 'Sem descrição')}")
                        st.markdown(f"**Sistemas:** {sistemas_txt}")
                    
                    with col2:
                        # Editar permissão
                        nova_perm = st.selectbox(
                            "Nível de permissão:",
                            options=["usuario", "admin"],
                            index=0 if perm == "usuario" else 1,
                            key=f"perm_func_{idx}"
                        )
                        
                        # Editar descrição
                        nova_desc = st.text_input(
                            "Descrição:",
                            value=f.get('descricao', ''),
                            key=f"desc_func_{idx}"
                        )
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("💾 Salvar", key=f"save_func_{idx}"):
                                funcoes[idx]['permissao'] = nova_perm
                                funcoes[idx]['descricao'] = nova_desc
                                salvar_json(DB_FUNCOES, funcoes)
                                st.success("Atualizado!")
                                time.sleep(1)
                                st.rerun()
                        
                        with c2:
                            # Não permitir excluir admin_master
                            if f['id'] != 'admin_master':
                                if st.button("🗑️ Excluir", key=f"del_func_{idx}", type="secondary"):
                                    funcoes.pop(idx)
                                    salvar_json(DB_FUNCOES, funcoes)
                                    st.rerun()
                            else:
                                st.caption("Protegido")
            
            st.markdown("---")
            st.markdown("#### ➕ Nova Função/Cargo")
            with st.form("form_funcao", clear_on_submit=True):
                f_id = st.text_input("ID único (ex: gerente_vendas)")
                f_nome = st.text_input("Nome da Função")
                f_desc = st.text_input("Descrição")
                f_perm = st.selectbox("Nível de Permissão", options=["usuario", "admin"])
                f_sistemas = st.multiselect("Sistemas com acesso", options=sistemas_disponiveis + ["*"])
                
                if st.form_submit_button("✅ Criar Função"):
                    if f_id and f_nome:
                        # Verificar se ID já existe
                        if any(func['id'] == f_id for func in funcoes):
                            st.error("ID já existe. Escolha outro.")
                        else:
                            nova_funcao = {
                                "id": f_id.lower().replace(" ", "_"),
                                "nome": f_nome,
                                "sistemas": f_sistemas if f_sistemas else ["*"],
                                "permissao": f_perm,
                                "descricao": f_desc
                            }
                            funcoes.append(nova_funcao)
                            salvar_json(DB_FUNCOES, funcoes)
                            st.success(f"Função '{f_nome}' criada!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.warning("ID e Nome são obrigatórios.")


# ==============================================================================
# TELA PRINCIPAL (LOGADA) - COM AJUSTE FINO DE MARGENS
# ==============================================================================

# 1. LOGO GIGANTE CENTRALIZADA E COM MARGENS CONTROLADAS VIA HTML
if os.path.exists("logo_taxbase.png"):
    with open("logo_taxbase.png", "rb") as f:
        img_data = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; margin-top: -40px; margin-bottom: 10px;">
            <img src="data:image/png;base64,{img_data}" width="400" style="max-width: 90%;">
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.title("🟦 Taxbase")

# 2. BOTÕES E BOAS VINDAS ABAIXO DA LOGO
col_texto, col_botoes = st.columns([4, 1.5])

with col_texto:
    # Nome do usuário e função
    funcao_nome = usuario_funcao['nome'] if usuario_funcao else 'Sem função'
    perm_badge = 'admin' if permissao_atual == 'admin' else 'usuario'
    
    st.markdown("<h3 style='margin-bottom: 0px;'>Hub Corporativo</h3>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='display: flex; align-items: center; gap: 10px; margin-top: 5px;'>
            <span style='color: gray'>Bem-vindo, <strong>{usuario_nome}</strong></span>
            <span class='funcao-badge {perm_badge}'>{funcao_nome}</span>
        </div>
    """, unsafe_allow_html=True)

with col_botoes:
    b1, b2 = st.columns(2)
    with b1:
        if st.button("⚙️\nGestão", use_container_width=True):
            abrir_painel_gestao()
    with b2:
        if st.button("🚪\nSair", use_container_width=True):
            st.session_state['logado'] = False
            st.session_state['usuario_atual'] = ""
            st.session_state['usuario_nome'] = ""
            st.session_state['usuario_funcao'] = None
            st.session_state['permissao'] = "usuario"
            st.rerun()

st.divider()

# Mostrar info de sistemas disponíveis
if not is_admin_master:
    total_sistemas = len(SISTEMAS)
    sistemas_acessiveis = len(SISTEMAS_VISIVEIS)
    if sistemas_acessiveis < total_sistemas:
        st.info(f"🔐 Você tem acesso a {sistemas_acessiveis} de {total_sistemas} sistemas baseado na sua função.")

# --- FILTRO E LISTAGEM ---
busca = st.text_input("🔎", placeholder="Buscar sistema...", label_visibility="collapsed").lower()

sistemas_finais = [
    s for s in SISTEMAS_VISIVEIS
    if busca in s['nome'].lower() or busca in s['categoria'].lower() or busca in s['desc'].lower()
]

if not sistemas_finais:
    if not SISTEMAS_VISIVEIS:
        st.warning("🔒 Você não tem acesso a nenhum sistema. Entre em contato com o administrador.")
    else:
        st.info("Nenhum sistema encontrado para sua busca.")
else:
    cols = st.columns(3)
    for i, sis in enumerate(sistemas_finais):
        with cols[i % 3]:
            with st.container(border=True):
                txt_status, cor_status = obter_status_sistema(sis)
                
                # Determinar classe do badge de status
                if "Online" in txt_status:
                    status_class = "online"
                    status_icon = "✓"
                elif "Offline" in txt_status:
                    status_class = "offline"
                    status_icon = "✕"
                else:
                    status_class = "manutencao"
                    status_icon = "⚡"
                
                # Header com título e badge de status
                st.markdown(f"""
                    <div class='card-header'>
                        <h3 class='card-title'>{sis['nome']}</h3>
                        <div class='status-badge {status_class}'>
                            <span class='status-dot'></span>
                            {txt_status.split(' ', 1)[1] if ' ' in txt_status else txt_status}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Tag de categoria
                st.markdown(f"""
                    <div class='categoria-tag'>
                        📂 {sis['categoria']}
                    </div>
                """, unsafe_allow_html=True)
                
                # Descrição
                st.markdown(f"""
                    <p class='sistema-desc'>{sis['desc']}</p>
                """, unsafe_allow_html=True)
                
                # Mapeamento de sistemas internos para páginas
                PAGINAS_INTERNAS = {
                    "AUDIT_FISCAL": "pages/1_Auditor_Fiscal.py"
                }
                
                sistema_id = sis.get('sistema_id', '')
                if sistema_id in PAGINAS_INTERNAS:
                    # Sistema interno - usar navegação interna
                    if st.button("🚀  Acessar Sistema", key=f"btn_nav_{i}", use_container_width=True):
                        st.switch_page(PAGINAS_INTERNAS[sistema_id])
                else:
                    # Sistema externo - abrir em nova aba
                    st.link_button("🚀  Acessar Sistema", sis['url'], use_container_width=True)

st.markdown("""
    <div class='footer-modern'>
        <span style='color: #009BD6; font-weight: 600;'>TAXBASE</span> • Tecnologia para Contabilidade<br/>
        <small style='color: #AAA;'>© 2026 • Todos os direitos reservados</small>
    </div>
""", unsafe_allow_html=True)