import streamlit as st
import sys
import os

# Adicionar path do AUDIT_FISCAL
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AUDIT_FISCAL'))

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Auditor Fiscal - Taxbase", layout="wide", initial_sidebar_state="collapsed")

# --- VERIFICAÇÃO DE ACESSO ---
def verificar_acesso():
    """Verifica se o usuário está logado e tem permissão"""
    if 'logado' not in st.session_state or not st.session_state['logado']:
        st.error("🔒 Acesso negado. Faça login pelo Hub Taxbase.")
        st.markdown("[← Voltar ao Hub](../)")
        st.stop()
    
    # Verificar permissão para este sistema
    funcao = st.session_state.get('usuario_funcao', {})
    if not funcao:
        st.error("🔒 Função não encontrada. Entre em contato com o administrador.")
        st.stop()
    
    sistemas_permitidos = funcao.get('sistemas', [])
    if 'AUDIT_FISCAL' not in sistemas_permitidos and '*' not in sistemas_permitidos:
        st.error("🚫 Você não tem permissão para acessar o Auditor Fiscal.")
        st.markdown("[← Voltar ao Hub](../)")
        st.stop()
    
    return funcao.get('permissao', 'usuario')

# Verificar acesso e obter permissão
permissao_atual = verificar_acesso()
st.session_state['permissao_sistema'] = permissao_atual

# --- INFORMAÇÕES DO USUÁRIO ---
usuario_nome = st.session_state.get('usuario_nome', 'Usuário')
funcao = st.session_state.get('usuario_funcao', {})
funcao_nome = funcao.get('nome', 'Sem função')

# --- CSS PREMIUM MODERNIZADO ---
st.markdown("""
<style>
    /* ============================================
       IMPORTAÇÃO DE FONTE PROFISSIONAL
    ============================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* ============================================
       ANIMAÇÕES
    ============================================ */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes progressFill {
        from { width: 0; }
    }
    
    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 0 0 rgba(0, 153, 213, 0.4); }
        50% { box-shadow: 0 0 20px 5px rgba(0, 153, 213, 0.2); }
    }

    /* ============================================
       1. FORÇAR TEMA CLARO + BASE
    ============================================ */
    :root {
        --primary-color: #0099D5;
        --primary-dark: #007CA3;
        --primary-light: #E8F6FC;
        --background-color: #FFFFFF;
        --secondary-background-color: #F0F2F6;
        --text-color: #343A40;
        --text-muted: #7F8C8D;
        --border-color: #E0E6EB;
        --success-color: #27AE60;
        --warning-color: #F39C12;
        --danger-color: #E74C3C;
        --font: 'Inter', 'Segoe UI', sans-serif;
    }

    [data-testid="stAppViewContainer"] { 
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        color: var(--text-color);
        font-family: var(--font);
    }
    
    [data-testid="stHeader"] { background-color: #FFFFFF; }
    
    /* ESCONDER SIDEBAR */
    [data-testid="stSidebar"] {display: none;}
    section[data-testid="stSidebarContent"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}

    /* LIMPEZA DA INTERFACE */
    header[data-testid="stHeader"] { display: none; }
    div[data-testid="stToolbar"] { visibility: hidden; display: none; }
    footer { visibility: hidden; display: none; }
    .stApp { margin-top: -60px; }

    /* ============================================
       2. BADGE DE PERMISSÃO MODERNIZADO
    ============================================ */
    .perm-badge {
        background: linear-gradient(135deg, var(--success-color), #1E8449);
        color: white;
        padding: 6px 16px;
        border-radius: 25px;
        font-size: 0.8rem;
        font-weight: 600;
        font-family: var(--font);
        letter-spacing: 0.5px;
        text-transform: uppercase;
        box-shadow: 0 2px 8px rgba(39, 174, 96, 0.3);
        display: inline-block;
    }
    .perm-badge.admin {
        background: linear-gradient(135deg, var(--danger-color), #C0392B);
        box-shadow: 0 2px 8px rgba(231, 76, 60, 0.3);
    }

    /* ============================================
       3. BARRA DE INFORMAÇÕES PREMIUM
    ============================================ */
    .info-bar {
        background: linear-gradient(135deg, var(--primary-light) 0%, #FFFFFF 100%);
        border-radius: 16px;
        padding: 12px 24px;
        margin-bottom: 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(0, 153, 213, 0.15);
        color: var(--text-color);
        font-family: var(--font);
        font-size: 0.9rem;
        box-shadow: 0 4px 15px rgba(0, 153, 213, 0.08);
    }
    .info-item strong { 
        color: var(--primary-color); 
        font-weight: 700; 
    }

    /* ============================================
       4. BOTÕES ESTILIZADOS
    ============================================ */
    .stButton > button { 
        border: 1px solid var(--border-color);
        color: var(--text-color); 
        border-radius: 12px; 
        font-weight: 600;
        font-family: var(--font);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stButton > button:hover { 
        border-color: var(--primary-color) !important; 
        color: var(--primary-color) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 153, 213, 0.15);
    }
    .stButton > button:active { 
        background-color: var(--primary-color) !important; 
        color: white !important; 
        border-color: var(--primary-color) !important; 
    }

    /* Botão Primário (Azul) */
    .stButton > button[kind="primary"] { 
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%) !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0, 153, 213, 0.3);
    }
    .stButton > button[kind="primary"]:hover { 
        background: linear-gradient(135deg, var(--primary-dark) 0%, #006690 100%) !important;
        box-shadow: 0 6px 20px rgba(0, 153, 213, 0.4);
    }

    /* ============================================
       5. KPIs MODERNIZADOS
    ============================================ */
    .kpi-container { 
        display: flex; 
        gap: 20px; 
        margin-bottom: 25px; 
    }
    .kpi-card {
        flex: 1; 
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid var(--border-color); 
        border-radius: 16px;
        padding: 20px; 
        display: flex; 
        align-items: center; 
        justify-content: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04); 
        height: 85px; 
        font-family: var(--font);
        transition: all 0.3s ease;
        animation: fadeInUp 0.5s ease-out;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0, 153, 213, 0.12);
    }
    .kpi-card.blue { 
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
        color: white; 
        border: none;
        box-shadow: 0 6px 20px rgba(0, 153, 213, 0.3);
    }
    .kpi-value { 
        font-size: 1.6rem; 
        font-weight: 700; 
        margin-left: 12px; 
    }
    .kpi-label { 
        font-size: 1rem; 
        font-weight: 500; 
        display: flex; 
        align-items: center; 
    }
    .kpi-card .kpi-value { color: var(--text-color); }
    .kpi-card.blue .kpi-value { color: #FFFFFF; }

    /* ============================================
       6. CARDS DE EMPRESA PREMIUM
    ============================================ */
    div[data-testid="stBorderContainer"] {
        border-radius: 16px; 
        border: 1px solid var(--border-color); 
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        background: linear-gradient(145deg, #ffffff 0%, #fafbfc 100%);
        padding: 18px; 
        margin-bottom: 12px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    div[data-testid="stBorderContainer"]:hover {
        box-shadow: 0 8px 25px rgba(0, 153, 213, 0.1);
        border-color: rgba(0, 153, 213, 0.3);
        transform: translateY(-2px);
    }
    .company-title-box { display: flex; align-items: baseline; }
    .company-name { 
        font-weight: 700; 
        font-size: 1.15rem; 
        color: var(--text-color); 
        margin-right: 12px;
        font-family: var(--font);
    }
    .cnpj-text { 
        font-size: 0.85rem; 
        color: var(--text-muted);
        font-family: var(--font);
    }

    /* ============================================
       7. BARRA DE PROGRESSO ANIMADA
    ============================================ */
    .progress-wrapper {
        width: 100%; 
        background: linear-gradient(90deg, #eee, #f5f5f5);
        border-radius: 10px; 
        height: 10px;
        margin-top: -10px; 
        overflow: hidden; 
        position: relative;
    }
    .progress-fill { 
        height: 100%; 
        background: linear-gradient(90deg, var(--primary-color), var(--primary-dark));
        border-radius: 10px; 
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    .progress-fill::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    /* ============================================
       8. CENTRALIZAR IMAGENS
    ============================================ */
    div[data-testid="stImage"] > img { 
        display: block; 
        margin-left: auto; 
        margin-right: auto; 
    }

    /* ============================================
       9. EXPANDERS MODERNOS
    ============================================ */
    div[data-testid="stExpander"] {
        border-radius: 12px;
        border: 1px solid var(--border-color);
        overflow: hidden;
        background: white;
    }
    
    div[data-testid="stExpander"] summary {
        font-family: var(--font);
        font-weight: 600;
    }

    /* ============================================
       10. GRÁFICOS PLOTLY
    ============================================ */
    .js-plotly-plot {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    }
</style>
""", unsafe_allow_html=True)


# --- IMPORTAÇÕES DO AUDIT_FISCAL ---
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime, timedelta
import pytz

# Mudar para o diretório do AUDIT_FISCAL para carregar configs
original_dir = os.getcwd()
audit_fiscal_dir = os.path.join(os.path.dirname(__file__), '..', 'AUDIT_FISCAL')
os.chdir(audit_fiscal_dir)

try:
    from config import BQ_TABLE_ID, SPREADSHEET_ID
    from reference_data import ReferenceLoader
    from auditor_logic import AuditorClassifier
finally:
    os.chdir(original_dir)

# --- CONFIGURAÇÕES DE CONEXÃO ---
BQ_TABLE_IGNORED = "auditor-processos.auditoria_fiscal.controle_ignorados"
BQ_TABLE_DISCARDED = "auditor-processos.auditoria_fiscal.controle_descartados"
KEY_FILE = os.path.join(audit_fiscal_dir, 'credentials.json')

# --- CONTROLE DE ESTADO ---
if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = 'OPERATIONAL'


def toggle_view():
    if st.session_state['view_mode'] == 'OPERATIONAL':
        st.session_state['view_mode'] = 'DASHBOARD'
    else:
        st.session_state['view_mode'] = 'OPERATIONAL'


# --- FUNÇÕES DE DATA E HORA ---
def get_competencia_atual():
    hoje = datetime.now()
    primeiro_dia_este_mes = hoje.replace(day=1)
    ultimo_dia_mes_passado = primeiro_dia_este_mes - timedelta(days=1)
    return ultimo_dia_mes_passado.strftime("%m/%Y")


def gerar_opcoes_periodo(n_meses=12):
    """Gera lista de períodos MM/YYYY dos últimos n_meses."""
    opcoes = []
    hoje = datetime.now()
    for i in range(1, n_meses + 1):
        primeiro_dia = hoje.replace(day=1)
        data_alvo = primeiro_dia - timedelta(days=1)  # último dia do mês anterior
        for _ in range(i - 1):
            data_alvo = data_alvo.replace(day=1) - timedelta(days=1)
        opcoes.append(data_alvo.strftime("%m/%Y"))
    return opcoes


def format_last_update(ts):
    if pd.isnull(ts): return "N/A"
    try:
        return ts.strftime("%d/%m/%Y às %H:%M")
    except:
        return str(ts)


# --- GERENCIAMENTO DE DADOS ---
def get_credentials():
    return service_account.Credentials.from_service_account_file(
        KEY_FILE, scopes=['https://www.googleapis.com/auth/drive',
                          'https://www.googleapis.com/auth/spreadsheets',
                          'https://www.googleapis.com/auth/cloud-platform']
    )


def load_ignored():
    try:
        creds = get_credentials()
        client = bigquery.Client(credentials=creds)
        query = f"SELECT cnpj, obrigacao FROM `{BQ_TABLE_IGNORED}`"
        df = client.query(query).to_dataframe()

        result = {}
        if not df.empty:
            for cnpj, group in df.groupby('cnpj'):
                result[cnpj] = group['obrigacao'].tolist()
        return result
    except Exception:
        return {}


def toggle_ignore(cnpj, obrigacao):
    """Insere ou Remove do BigQuery - SOMENTE ADMIN"""
    if permissao_atual != 'admin':
        st.warning("⚠️ Você não tem permissão para esta ação.")
        return
    
    try:
        creds = get_credentials()
        client = bigquery.Client(credentials=creds)

        current_ignored = load_ignored()
        lista_atual = current_ignored.get(cnpj, [])

        if obrigacao in lista_atual:
            query = f"""
                DELETE FROM `{BQ_TABLE_IGNORED}` 
                WHERE cnpj = '{cnpj}' AND obrigacao = '{obrigacao}'
            """
            client.query(query).result()
            st.toast(f"'{obrigacao}' reativada!", icon="⚡")
        else:
            query = f"""
                INSERT INTO `{BQ_TABLE_IGNORED}` (cnpj, obrigacao, data_ignorado)
                VALUES ('{cnpj}', '{obrigacao}', CURRENT_TIMESTAMP())
            """
            client.query(query).result()
            st.toast(f"'{obrigacao}' adormecida.", icon="💤")

        st.cache_data.clear()
        st.rerun()

    except Exception as e:
        st.error(f"Erro ao salvar no banco: {e}")


def load_unidentified_bq():
    try:
        creds = get_credentials()
        client = bigquery.Client(credentials=creds)

        query = f"""
            SELECT id_arquivo, nome_arquivo, link_arquivo, data_processamento
            FROM `{BQ_TABLE_ID}` bq
            WHERE (status_auditoria = 'NAO_IDENTIFICADO' 
                OR categoria IS NULL
                OR categoria = 'NAO_IDENTIFICADO'
                OR categoria = '')
            AND NOT EXISTS (
                SELECT 1 
                FROM `{BQ_TABLE_DISCARDED}` d
                WHERE d.id_arquivo = bq.id_arquivo
                AND TIMESTAMP_TRUNC(d.data_processamento, SECOND) = TIMESTAMP_TRUNC(bq.data_processamento, SECOND)
            )
            ORDER BY data_processamento DESC
            LIMIT 50
        """
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"Erro ao carregar não identificados: {e}")
        return pd.DataFrame()


def action_allocate_file(id_arquivo, data_proc, cnpj_destino, nova_categoria):
    """Aloca arquivo - SOMENTE ADMIN. Altera apenas o registro específico."""
    if permissao_atual != 'admin':
        st.warning("⚠️ Você não tem permissão para esta ação.")
        return
    
    try:
        creds = get_credentials()
        client = bigquery.Client(credentials=creds)

        query = f"""
            UPDATE `{BQ_TABLE_ID}`
            SET cnpj = '{cnpj_destino}', 
                categoria = '{nova_categoria}',
                status_auditoria = 'MANUAL_OK'
            WHERE id_arquivo = '{id_arquivo}'
            AND TIMESTAMP_TRUNC(data_processamento, SECOND) = TIMESTAMP_TRUNC(TIMESTAMP('{data_proc}'), SECOND)
        """
        client.query(query).result()
        st.toast("Arquivo alocado com sucesso!", icon="✅")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        if 'streaming buffer' in str(e).lower():
            st.warning("⏳ Este arquivo foi processado há pouco tempo. Aguarde ~30 minutos e tente novamente.")
        else:
            st.error(f"Erro ao atualizar: {e}")


def action_discard_file(id_arquivo, data_proc, nome_arquivo=''):
    """Descarta registro específico inserindo na tabela de controle - SOMENTE ADMIN"""
    if permissao_atual != 'admin':
        st.warning("⚠️ Você não tem permissão para esta ação.")
        return
    
    try:
        creds = get_credentials()
        client = bigquery.Client(credentials=creds)

        # INSERT com id_arquivo + data_processamento para atingir só AQUELE registro
        query = f"""
            INSERT INTO `{BQ_TABLE_DISCARDED}` (id_arquivo, data_processamento, nome_arquivo)
            VALUES ('{id_arquivo}', TIMESTAMP('{data_proc}'), '{nome_arquivo}')
        """

        client.query(query).result()
        st.toast("Arquivo descartado!", icon="🗑️")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao descartar: {e}")


# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=300)
def load_data_bq(periodo):
    try:
        creds = get_credentials()
        client = bigquery.Client(credentials=creds)

        query = f"""
            SELECT 
                cnpj, 
                categoria as obrigacao, 
                periodo, 
                status_auditoria, 
                id_arquivo, 
                nome_arquivo, 
                link_arquivo,
                data_processamento as data_proc_full,
                DATE(data_processamento) as data_proc
            FROM `{BQ_TABLE_ID}` t
            WHERE t.periodo = '{periodo}'
            AND NOT EXISTS (
                SELECT 1 
                FROM `{BQ_TABLE_DISCARDED}` d
                WHERE d.id_arquivo = t.id_arquivo
                AND TIMESTAMP_TRUNC(d.data_processamento, SECOND) = TIMESTAMP_TRUNC(t.data_processamento, SECOND)
            )
        """
        df = client.query(query).to_dataframe()

        last_update = df['data_proc_full'].max() if not df.empty else None

        return df, last_update
    except Exception as e:
        st.error(f"Erro ao conectar BigQuery: {e}")
        return pd.DataFrame(), None


@st.cache_data(ttl=3600)
def load_master_data():
    try:
        creds = get_credentials()
        loader = ReferenceLoader(creds)
        loader.load_data()
        if loader.df_empresas is not None and not loader.df_empresas.empty:
            return loader.df_empresas
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
        return pd.DataFrame()


# --- MODAL ---
@st.dialog("Detalhes das Obrigações", width="large")
def open_company_modal(row, df_bq):
    empresa = row['Empresa']
    cnpj = row['CNPJ']

    st.markdown(f"### 🏢 {empresa}")
    st.caption(f"CNPJ: {cnpj}")
    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### ✅ Entregues")
        if row['Entregues']:
            for item in row['Entregues']:
                files = df_bq[(df_bq['cnpj_clean'] == cnpj) & (df_bq['obrigacao'] == item)].sort_values('periodo',
                                                                                                        ascending=False)
                if not files.empty:
                    with st.popover(f"📄 {item}", use_container_width=True):
                        for _, f in files.iterrows():
                            st.markdown(f"[{f.get('periodo')} - {f.get('nome_arquivo')}]({f.get('link_arquivo', '#')})")
                else:
                    st.button(f"📄 {item}", disabled=True, key=f"dsb_{cnpj}_{item}", use_container_width=True)
        else:
            st.info("Nenhuma entrega identificada.")

    with c2:
        st.markdown("#### ⚠️ Pendentes")
        if row['FaltantesAtivos']:
            for item in row['FaltantesAtivos']:
                # Botão de dormir/acordar SOMENTE para admins
                if permissao_atual == 'admin':
                    if st.button(f"⚠️ {item}", key=f"btn_ign_{cnpj}_{item}", use_container_width=True,
                                 help="Clique para adormecer"):
                        toggle_ignore(cnpj, item)
                else:
                    st.markdown(f"⚠️ {item}")
        elif not row['FaltantesIgnorados']:
            st.success("Tudo em dia!")

        if row['FaltantesIgnorados']:
            st.markdown("---")
            st.caption("💤 ADORMECIDOS")
            for item in row['FaltantesIgnorados']:
                if permissao_atual == 'admin':
                    if st.button(f"💤 {item}", key=f"btn_wake_{cnpj}_{item}", use_container_width=True,
                                 help="Clique para reativar"):
                        toggle_ignore(cnpj, item)
                else:
                    st.markdown(f"💤 {item}")


# --- PROCESSAMENTO ---
def processar_painel(periodo):
    df_bq, last_update = load_data_bq(periodo)
    df_master = load_master_data()
    ignored_data = load_ignored()

    if df_master.empty: return pd.DataFrame(), pd.DataFrame(), None

    if 'cnpj' in df_master.columns:
        df_master['clean_cnpj'] = df_master['cnpj'].astype(str).str.replace(r'\D', '', regex=True)

    metas = list(AuditorClassifier().CATEGORIES.keys())
    painel_data = []

    for _, row in df_master.iterrows():
        cnpj = row['clean_cnpj']
        nome = row.get('empresa', 'N/A')
        grupo = row.get('grupo', 'Sem Grupo')

        entregas = []
        if not df_bq.empty and 'cnpj' in df_bq.columns:
            df_bq['cnpj_clean'] = df_bq['cnpj'].astype(str).str.replace(r'\D', '', regex=True)
            entregas = df_bq[df_bq['cnpj_clean'] == cnpj]['obrigacao'].unique().tolist()

        lista_ignorados = ignored_data.get(cnpj, [])
        faltantes_ativos = [m for m in metas if m not in entregas and m not in lista_ignorados]
        faltantes_ignorados = [m for m in metas if m not in entregas and m in lista_ignorados]

        meta_ajustada = max(1, len(metas) - len(lista_ignorados))
        progresso = min(1.0, len(entregas) / meta_ajustada)
        status = "OK" if progresso == 1 else "PENDENTE"
        has_delivery = len(entregas) > 0

        painel_data.append({
            "CNPJ": cnpj, "Empresa": nome, "Grupo": grupo,
            "Entregues": entregas, "FaltantesAtivos": faltantes_ativos,
            "FaltantesIgnorados": faltantes_ignorados,
            "QtdPendentes": len(faltantes_ativos),
            "Progresso": progresso, "Status": status, "HasDelivery": has_delivery
        })

    return pd.DataFrame(painel_data), df_bq, last_update


# ==============================================================================
# INTERFACE
# ==============================================================================

# Cabeçalho com info de usuário
c_voltar, c_logo_center, c_user_info = st.columns([1, 2, 2])

with c_voltar:
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
    if st.button("← Hub", use_container_width=True):
        st.switch_page("app.py")

with c_logo_center:
    logo_path = os.path.join(audit_fiscal_dir, "logo_taxbase.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=300)
    else:
        st.markdown("<h1 style='text-align:center; color:#0099D5;'>TAXBASE AUDITOR</h1>", unsafe_allow_html=True)

with c_user_info:
    st.markdown("<div style='margin-top: 45px;'></div>", unsafe_allow_html=True)
    
    perm_badge = 'admin' if permissao_atual == 'admin' else ''
    perm_texto = 'ADMIN' if permissao_atual == 'admin' else 'USUÁRIO'
    
    col_info, col_btn = st.columns([2, 1])
    with col_info:
        st.markdown(f"""
            <div style='text-align: right;'>
                <strong>{usuario_nome}</strong><br/>
                <span class='perm-badge {perm_badge}'>{perm_texto}</span>
            </div>
        """, unsafe_allow_html=True)
    with col_btn:
        if st.session_state['view_mode'] == 'OPERATIONAL':
            st.button("📊 Dashboard", on_click=toggle_view, type="primary", use_container_width=True)
        else:
            st.button("📋 Lista", on_click=toggle_view, type="secondary", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- SELETOR DE PERÍODO DE APURAÇÃO ---
opcoes_periodo = gerar_opcoes_periodo(12)
periodo_default = get_competencia_atual()

col_periodo_label, col_periodo_sel, col_periodo_spacer = st.columns([1, 1, 3])
with col_periodo_label:
    st.markdown("<div style='margin-top: 8px; font-weight: 600; font-family: Inter, sans-serif;'>📅 Período de Apuração:</div>", unsafe_allow_html=True)
with col_periodo_sel:
    idx_default = opcoes_periodo.index(periodo_default) if periodo_default in opcoes_periodo else 0
    periodo_selecionado = st.selectbox(
        "Período",
        options=opcoes_periodo,
        index=idx_default,
        key="periodo_apuracao",
        label_visibility="collapsed"
    )

df_painel, df_bq_raw, last_update_ts = processar_painel(periodo_selecionado)

if not df_painel.empty:

    # Barra de Informações
    st.markdown(f"""
        <div class="info-bar">
            <div class="info-item">📅 Competência Selecionada: <strong>{periodo_selecionado}</strong></div>
            <div class="info-item">🔄 Última Execução do Robô: <strong>{format_last_update(last_update_ts)}</strong></div>
        </div>
    """, unsafe_allow_html=True)

    # KPIs
    total_empresas = len(df_painel)
    total_obrigacoes_ok = df_painel['Entregues'].apply(len).sum()
    total_obrigacoes_pendente = df_painel['FaltantesAtivos'].apply(len).sum()
    total_meta = total_obrigacoes_ok + total_obrigacoes_pendente
    conclusao_pct = (total_obrigacoes_ok / total_meta * 100) if total_meta > 0 else 0

    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card blue"><div class="kpi-label">🏢 Empresas</div><div class="kpi-value">{total_empresas}</div></div>
        <div class="kpi-card"><div class="kpi-label" style="color:#27AE60;">✅ Entregas</div><div class="kpi-value">{total_obrigacoes_ok}</div></div>
        <div class="kpi-card"><div class="kpi-label" style="color:#F39C12;">⚠️ Pendentes</div><div class="kpi-value">{total_obrigacoes_pendente}</div></div>
        <div class="kpi-card"><div class="kpi-label" style="color:#343A40;">📊 Conformidade</div><div class="kpi-value">{conclusao_pct:.1f}%</div></div>
    </div>
    """, unsafe_allow_html=True)

    # VISÃO OPERACIONAL (LISTA)
    if st.session_state['view_mode'] == 'OPERATIONAL':
        c_f1, c_f2, c_f3 = st.columns(3)
        if 'filtro_ativo' not in st.session_state: st.session_state['filtro_ativo'] = 'TODOS'


        def f_btn(lbl, key):
            t = "primary" if st.session_state['filtro_ativo'] == key else "secondary"
            if st.button(lbl, type=t, use_container_width=True, key=key):
                st.session_state['filtro_ativo'] = key
                st.rerun()


        with c_f1:
            f_btn("👁️ Todos", 'TODOS')
        with c_f2:
            f_btn("✅ Entregues", 'HAS_DELIVERY')
        with c_f3:
            f_btn("⚠️ Pendentes", 'PENDENTE')

        filtro = st.session_state['filtro_ativo']
        if filtro == 'HAS_DELIVERY':
            df_view = df_painel[df_painel['HasDelivery'] == True]
        elif filtro == 'PENDENTE':
            df_view = df_painel[df_painel['QtdPendentes'] > 0]
        else:
            df_view = df_painel

        for grupo in df_view.sort_values(['Grupo', 'Empresa'])['Grupo'].unique():
            df_grupo = df_view[df_view['Grupo'] == grupo]
            with st.expander(f"📂 {grupo} ({len(df_grupo)})", expanded=True):
                for _, row in df_grupo.iterrows():
                    pct = int(row['Progresso'] * 100)
                    with st.container(border=True):
                        c_info, c_btn = st.columns([0.85, 0.15])
                        with c_info:
                            st.markdown(f"""
                                <div class="company-title-box">
                                    <span class="company-name">{row['Empresa']}</span>
                                    <span class="cnpj-text">{row['CNPJ']}</span>
                                </div>
                            """, unsafe_allow_html=True)
                        with c_btn:
                            if st.button("🔎 Ver", key=f"btn_open_{row['CNPJ']}"):
                                open_company_modal(row, df_bq_raw)

                        st.markdown(f"""
                            <div class="progress-wrapper">
                                <div class="progress-fill" style="width: {pct}%;"></div>
                            </div>
                        """, unsafe_allow_html=True)

    # VISÃO DASHBOARD (GRÁFICOS + SANEAMENTO)
    else:
        st.markdown("### 📊 Indicadores Gerenciais")
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            if not df_bq_raw.empty:
                df_timeline = df_bq_raw.groupby('data_proc').size().reset_index(name='Arquivos')
                fig_timeline = px.bar(df_timeline, x='data_proc', y='Arquivos',
                                      title="Volume de Arquivos Recebidos (Diário)",
                                      color_discrete_sequence=['#0099D5'])
                st.plotly_chart(fig_timeline, use_container_width=True)
            else:
                st.info("Sem dados de timeline.")

        with col_g2:
            if not df_bq_raw.empty:
                df_pie = df_bq_raw['obrigacao'].value_counts().reset_index()
                df_pie.columns = ['Obrigacao', 'Qtd']
                fig_pie = px.pie(df_pie, names='Obrigacao', values='Qtd',
                                 title="Distribuição por Tipo de Obrigação",
                                 hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Sem dados de obrigações.")

        st.markdown("### 🚨 Top Empresas com Pendências")
        df_pendencias = df_painel[df_painel['QtdPendentes'] > 0].sort_values('QtdPendentes', ascending=False).head(15)

        if not df_pendencias.empty:
            fig_bar = px.bar(df_pendencias, x='Empresa', y='QtdPendentes',
                             title="Ranking: Quem tem mais pendências?",
                             text='QtdPendentes',
                             color='QtdPendentes',
                             color_continuous_scale=['#FFD700', '#FF4500'])
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.success("Tudo 100%! Nenhuma pendência crítica.")

        # --- SEÇÃO DE SANEAMENTO (SOMENTE ADMIN) ---
        if permissao_atual == 'admin':
            st.markdown("---")
            st.markdown("<br>", unsafe_allow_html=True)

            c_l1, c_l2, c_l3 = st.columns([3, 2, 3])
            with c_l2:
                logo_path = os.path.join(audit_fiscal_dir, "logo_taxbase.png")
                if os.path.exists(logo_path):
                    st.image(logo_path, width=200)
                else:
                    st.markdown("<h3 style='text-align:center; color:#CCC;'>TAXBASE</h3>", unsafe_allow_html=True)

            st.markdown("<h4 style='text-align: center; color: #7F8C8D;'>Saneamento de Arquivos Não Identificados</h4>",
                        unsafe_allow_html=True)

            df_unid = load_unidentified_bq()

            if not df_unid.empty:
                st.warning(f"Existem {len(df_unid)} arquivos aguardando classificação manual.")

                for i, row_u in df_unid.iterrows():
                    with st.expander(
                            f"📁 Arquivo: {row_u['nome_arquivo']} ({format_last_update(row_u['data_processamento'])})",
                            expanded=False):

                        c_detalhe, c_acao = st.columns([1, 1])

                        with c_detalhe:
                            st.markdown(f"**Nome:** `{row_u['nome_arquivo']}`")
                            if row_u['link_arquivo']:
                                st.markdown(f"🔗 [Baixar/Visualizar Arquivo]({row_u['link_arquivo']})")
                            else:
                                st.caption("Link indisponível")

                        with c_acao:
                            st.markdown("**Ação Requerida:**")

                            lista_empresas = df_painel[['Empresa', 'CNPJ']].drop_duplicates().sort_values('Empresa')
                            opcoes_empresa = {f"{r.Empresa} ({r.CNPJ})": r.CNPJ for _, r in lista_empresas.iterrows()}

                            sel_empresa_label = st.selectbox("Alocar para Empresa:", options=list(opcoes_empresa.keys()),
                                                             key=f"sel_emp_{i}")
                            sel_cnpj = opcoes_empresa[sel_empresa_label]

                            lista_obrigacoes = sorted(list(AuditorClassifier().CATEGORIES.keys()))
                            sel_categoria = st.selectbox("Definir Categoria:", options=lista_obrigacoes, key=f"sel_cat_{i}")

                            c_btn_save, c_btn_del = st.columns(2)
                            with c_btn_save:
                                if st.button("💾 Salvar/Alocar", key=f"btn_save_{i}", type="primary",
                                             use_container_width=True):
                                    action_allocate_file(row_u['id_arquivo'], str(row_u['data_processamento']), sel_cnpj, sel_categoria)

                            with c_btn_del:
                                if st.button("🗑️ Descartar", key=f"btn_del_{i}", type="secondary",
                                             use_container_width=True):
                                    action_discard_file(row_u['id_arquivo'], str(row_u['data_processamento']), row_u['nome_arquivo'])
            else:
                st.markdown("""
                    <div style='text-align: center; padding: 20px; background-color: #F0F8FF; border-radius: 10px; border: 1px dashed #0099D5;'>
                        <h5 style='color: #0099D5; margin:0;'>✨ Nenhum arquivo pendente de identificação!</h5>
                        <small style='color: #666;'>O robô identificou todos os arquivos processados.</small>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)

else:
    st.info("Aguardando dados... Verifique se o processamento backend rodou.")
