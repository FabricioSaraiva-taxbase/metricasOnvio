import streamlit as st
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
from google.oauth2 import service_account
import os
import json
from datetime import datetime, timedelta
import pytz

# --- IMPORTAÇÃO DOS NOSSOS MÓDULOS ---
# Certifique-se que estes arquivos existem no mesmo diretório
from config import BQ_TABLE_ID, SPREADSHEET_ID
from reference_data import ReferenceLoader
from auditor_logic import AuditorClassifier

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Painel Fiscal - Taxbase", layout="wide", initial_sidebar_state="collapsed")

# --- CONFIGURAÇÕES DE CONEXÃO ---
# Tabela onde salvamos o que foi ignorado
BQ_TABLE_IGNORED = "auditor-processos.auditoria_fiscal.controle_ignorados"
BQ_TABLE_DISCARDED = "auditor-processos.auditoria_fiscal.controle_descartados"
KEY_FILE = 'credentials.json'  # Verifique se o nome do arquivo é este ou service_account.json

# --- CONTROLE DE ESTADO ---
if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = 'OPERATIONAL'


def toggle_view():
    """Alterna entre Lista e Dashboard"""
    if st.session_state['view_mode'] == 'OPERATIONAL':
        st.session_state['view_mode'] = 'DASHBOARD'
    else:
        st.session_state['view_mode'] = 'OPERATIONAL'


# --- FUNÇÕES DE DATA E HORA ---
def get_competencia_atual():
    # Regra: Competência é o mês anterior ao atual
    hoje = datetime.now()
    primeiro_dia_este_mes = hoje.replace(day=1)
    ultimo_dia_mes_passado = primeiro_dia_este_mes - timedelta(days=1)
    return ultimo_dia_mes_passado.strftime("%m/%Y")


def format_last_update(ts):
    if pd.isnull(ts): return "N/A"
    try:
        # Formata para padrão BR
        return ts.strftime("%d/%m/%Y às %H:%M")
    except:
        return str(ts)


# --- GERENCIAMENTO DE DADOS (BIGQUERY & DRIVE) ---
def get_credentials():
    return service_account.Credentials.from_service_account_file(
        KEY_FILE, scopes=['https://www.googleapis.com/auth/drive',
                          'https://www.googleapis.com/auth/spreadsheets',
                          'https://www.googleapis.com/auth/cloud-platform']
    )


def load_ignored():
    """Lê do BigQuery quais obrigações estão dormindo."""
    try:
        creds = get_credentials()
        client = bigquery.Client(credentials=creds)
        query = f"SELECT cnpj, obrigacao FROM `{BQ_TABLE_IGNORED}`"
        df = client.query(query).to_dataframe()

        # Transforma em dicionário {CNPJ: [Lista de Obrigações]}
        result = {}
        if not df.empty:
            for cnpj, group in df.groupby('cnpj'):
                result[cnpj] = group['obrigacao'].tolist()
        return result
    except Exception:
        return {}


def toggle_ignore(cnpj, obrigacao):
    """Insere ou Remove do BigQuery (Nuvem)."""
    try:
        creds = get_credentials()
        client = bigquery.Client(credentials=creds)

        # Verifica estado atual
        current_ignored = load_ignored()
        lista_atual = current_ignored.get(cnpj, [])

        if obrigacao in lista_atual:
            # ACORDAR: Deleta do Banco
            query = f"""
                DELETE FROM `{BQ_TABLE_IGNORED}` 
                WHERE cnpj = '{cnpj}' AND obrigacao = '{obrigacao}'
            """
            client.query(query).result()
            st.toast(f"'{obrigacao}' reativada!", icon="⚡")
        else:
            # DORMIR: Insere no Banco
            query = f"""
                INSERT INTO `{BQ_TABLE_IGNORED}` (cnpj, obrigacao, data_ignorado)
                VALUES ('{cnpj}', '{obrigacao}', CURRENT_TIMESTAMP())
            """
            client.query(query).result()
            st.toast(f"'{obrigacao}' adormecida.", icon="💤")

        # Limpa cache para atualizar a tela imediatamente
        st.cache_data.clear()
        st.rerun()

    except Exception as e:
        st.error(f"Erro ao salvar no banco: {e}")


# --- NOVAS FUNÇÕES: SANEAMENTO DE ARQUIVOS ---
def load_unidentified_bq():
    """Carrega arquivos que o robô não conseguiu identificar."""
    try:
        creds = get_credentials()
        client = bigquery.Client(credentials=creds)

        # Filtro para pegar 'NAO_IDENTIFICADO' e variações
        query = f"""
            SELECT id_arquivo, nome_arquivo, link_arquivo, data_processamento
            FROM `{BQ_TABLE_ID}`
            WHERE (status_auditoria = 'NAO_IDENTIFICADO' 
                OR categoria IS NULL
                OR categoria = 'NAO_IDENTIFICADO'
                OR categoria = '')
            AND CONCAT(id_arquivo, '|', CAST(data_processamento AS STRING)) NOT IN (
                SELECT CONCAT(id_arquivo, '|', CAST(data_processamento AS STRING)) FROM `{BQ_TABLE_DISCARDED}`
            )
            ORDER BY data_processamento DESC
            LIMIT 50
        """
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"Erro ao carregar não identificados: {e}")
        return pd.DataFrame()


def action_allocate_file(id_arquivo, data_proc, cnpj_destino, nova_categoria):
    """Atualiza apenas o registro específico no BigQuery."""
    try:
        creds = get_credentials()
        client = bigquery.Client(credentials=creds)

        query = f"""
            UPDATE `{BQ_TABLE_ID}`
            SET cnpj = '{cnpj_destino}', 
                categoria = '{nova_categoria}',
                status_auditoria = 'MANUAL_OK'
            WHERE id_arquivo = '{id_arquivo}'
            AND CAST(data_processamento AS STRING) = '{data_proc}'
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
    """Remove o registro específico do painel inserindo na tabela de controle."""
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


# --- CSS PREMIUM (FIX TEMAS & INTERFACE) ---
st.markdown("""
<style>
    /* 1. FORÇAR TEMA CLARO */
    [data-testid="stAppViewContainer"] { background-color: #FFFFFF; color: #343A40; }
    [data-testid="stHeader"] { background-color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #F0F2F6; }

    /* 2. LIMPEZA DA INTERFACE */
    header[data-testid="stHeader"] { display: none; }
    div[data-testid="stToolbar"] { visibility: hidden; display: none; }
    footer { visibility: hidden; display: none; }
    .stApp { margin-top: -60px; }

    /* 3. CORES TAXBASE */
    :root {
        --primary-color: #0099D5;
        --background-color: #FFFFFF;
        --secondary-background-color: #F0F2F6;
        --text-color: #343A40;
        --font: "Segoe UI", sans-serif;
    }

    button:focus, div:focus, input:focus, textarea:focus, select:focus {
        border-color: #0099D5 !important;
        box-shadow: 0 0 0 1px #0099D5 !important;
        outline: none !important;
    }

    /* Info Bar */
    .info-bar {
        background-color: #F8F9FA;
        border-radius: 8px;
        padding: 8px 20px;
        margin-bottom: 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid #E9ECEF;
        color: #495057;
        font-family: "Segoe UI", sans-serif;
        font-size: 0.9rem;
    }
    .info-item strong { color: #0099D5; font-weight: 700; }

    /* Botões */
    .stButton > button { border-color: #e0e0e0; color: #343A40; border-radius: 8px; font-weight: 600; }
    .stButton > button:hover { border-color: #0099D5 !important; color: #0099D5 !important; }
    .stButton > button:active { background-color: #0099D5 !important; color: white !important; border-color: #0099D5 !important; }

    /* Botão Primário (Azul) */
    .stButton > button[kind="primary"] { background-color: #0099D5 !important; border-color: #0099D5 !important; }
    .stButton > button[kind="primary"]:hover { background-color: #007BB5 !important; border-color: #007BB5 !important; }

    /* KPIs */
    .kpi-container { display: flex; gap: 15px; margin-bottom: 20px; }
    .kpi-card {
        flex: 1; background: white; border: 1px solid #e0e0e0; border-radius: 12px;
        padding: 15px; display: flex; align-items: center; justify-content: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03); height: 75px; font-family: 'Segoe UI', sans-serif;
    }
    .kpi-card.blue { background-color: #0099D5; color: white; border: none; }
    .kpi-value { font-size: 1.4rem; font-weight: 700; margin-left: 8px; }
    .kpi-label { font-size: 1rem; font-weight: 500; display: flex; align-items: center; }
    .kpi-card .kpi-value { color: #343A40; }
    .kpi-card.blue .kpi-value { color: #FFFFFF; }

    /* Cards Empresa */
    div[data-testid="stBorderContainer"] {
        border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        background-color: white; padding: 15px; margin-bottom: 10px;
    }
    .company-title-box { display: flex; align-items: baseline; }
    .company-name { font-weight: 700; font-size: 1.2rem; color: #343A40; margin-right: 10px; }
    .cnpj-text { font-size: 0.9rem; color: #7F8C8D; }

    /* Barra Progresso */
    .progress-wrapper {
        width: 100%; background-color: #eee; border-radius: 10px; height: 10px;
        margin-top: -12px; overflow: hidden; position: relative;
    }
    .progress-fill { height: 100%; background-color: #0099D5; border-radius: 10px; transition: width 0.5s ease-in-out; }

    /* MODAL */
    div[data-testid="stDialog"] div[data-testid="stPopover"] > button {
        background-color: #0099D5 !important; color: white !important; border: none !important;
        border-radius: 20px !important; width: 100%; font-weight: 600 !important;
    }
    div[data-testid="stDialog"] .stButton button {
        background-color: #FFF8E1 !important; color: #B78A06 !important; border: 1px solid #FFE082 !important;
        border-radius: 20px !important;
    }

    div[data-testid="stImage"] > img { display: block; margin-left: auto; margin-right: auto; }
</style>
""", unsafe_allow_html=True)


# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=300)
def load_data_bq():
    """Carrega dados do BigQuery (Arquivos processados)."""
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
            FROM `{BQ_TABLE_ID}`
            WHERE DATE(data_processamento) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        """
        df = client.query(query).to_dataframe()

        last_update = df['data_proc_full'].max() if not df.empty else None

        return df, last_update
    except Exception as e:
        st.error(f"Erro ao conectar BigQuery: {e}")
        return pd.DataFrame(), None


@st.cache_data(ttl=3600)
def load_master_data():
    """Carrega dados da Planilha."""
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
                if st.button(f"⚠️ {item}", key=f"btn_ign_{cnpj}_{item}", use_container_width=True,
                             help="Clique para adormecer"):
                    toggle_ignore(cnpj, item)
        elif not row['FaltantesIgnorados']:
            st.success("Tudo em dia!")

        if row['FaltantesIgnorados']:
            st.markdown("---")
            st.caption("💤 ADORMECIDOS")
            for item in row['FaltantesIgnorados']:
                if st.button(f"💤 {item}", key=f"btn_wake_{cnpj}_{item}", use_container_width=True,
                             help="Clique para reativar"):
                    toggle_ignore(cnpj, item)


# --- PROCESSAMENTO ---
def processar_painel():
    df_bq, last_update = load_data_bq()
    df_master = load_master_data()
    ignored_data = load_ignored()  # Puxa do BigQuery

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


# --- INTERFACE (CABEÇALHO COM LOGO CENTRALIZADA) ---
# Usando colunas [3, 2, 3] para centralizar
c_spacer, c_logo_center, c_btn_right = st.columns([3, 2, 3])

with c_logo_center:
    if os.path.exists("logo_taxbase.png"):
        # ALTERAÇÃO: Trocamos use_column_width=True por width=300 (fixo) para evitar o aviso
        st.image("logo_taxbase.png", width=300)
    else:
        st.markdown("<h1 style='text-align:center; color:#0099D5;'>TAXBASE AUDITOR</h1>", unsafe_allow_html=True)

with c_btn_right:
    st.markdown("<div style='margin-top: 45px;'></div>", unsafe_allow_html=True)
    c_vazio, c_botao_real = st.columns([1, 1.2])
    with c_botao_real:
        if st.session_state['view_mode'] == 'OPERATIONAL':
            st.button("📊 Dashboard", on_click=toggle_view, type="primary", use_container_width=True)
        else:
            st.button("📋 Lista", on_click=toggle_view, type="secondary", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

df_painel, df_bq_raw, last_update_ts = processar_painel()

if not df_painel.empty:

    # Barra de Informações
    st.markdown(f"""
        <div class="info-bar">
            <div class="info-item">📅 Competência Apurada: <strong>{get_competencia_atual()}</strong></div>
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

        # --- SEÇÃO DE SANEAMENTO DE ARQUIVOS (LOGO CENTRALIZADA) ---
        st.markdown("---")
        st.markdown("<br>", unsafe_allow_html=True)

        # 1. Logo Centralizada no Rodapé
        c_l1, c_l2, c_l3 = st.columns([3, 2, 3])
        with c_l2:
            if os.path.exists("logo_taxbase.png"):
                # ALTERAÇÃO: width fixo para remover o warning e manter centralização
                st.image("logo_taxbase.png", width=200)
            else:
                st.markdown("<h3 style='text-align:center; color:#CCC;'>TAXBASE</h3>", unsafe_allow_html=True)

        st.markdown("<h4 style='text-align: center; color: #7F8C8D;'>Saneamento de Arquivos Não Identificados</h4>",
                    unsafe_allow_html=True)

        # 2. Carregar Pendências do Banco
        df_unid = load_unidentified_bq()

        if not df_unid.empty:
            st.warning(f"Existem {len(df_unid)} arquivos aguardando classificação manual.")

            # Cria um container para cada arquivo não identificado
            for i, row_u in df_unid.iterrows():
                # Expander fechado por padrão
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

                        # Selectbox para Empresa
                        lista_empresas = df_painel[['Empresa', 'CNPJ']].drop_duplicates().sort_values('Empresa')
                        opcoes_empresa = {f"{r.Empresa} ({r.CNPJ})": r.CNPJ for _, r in lista_empresas.iterrows()}

                        sel_empresa_label = st.selectbox("Alocar para Empresa:", options=list(opcoes_empresa.keys()),
                                                         key=f"sel_emp_{i}")
                        sel_cnpj = opcoes_empresa[sel_empresa_label]

                        # Selectbox para Categoria
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