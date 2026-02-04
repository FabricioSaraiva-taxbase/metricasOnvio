import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. CONFIGURAÇÃO VISUAL E CSS (Cores da Taxbase) ---
st.set_page_config(page_title="Taxbase Hub", page_icon="🏢", layout="wide")

# Definição de Cores
TAXBASE_BLUE = "#003366"  # Azul escuro corporativo
TAXBASE_GREY = "#F0F2F6"
TEXT_COLOR = "#333333"

# CSS Personalizado para esconder menus padrões e aplicar estilo
st.markdown(f"""
    <style>
    /* Esconder Menu Hamburger e Footer padrão do Streamlit */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* Estilo dos Títulos */
    h1, h2, h3 {{
        color: {TAXBASE_BLUE};
        font-family: 'Arial', sans-serif;
    }}

    /* Cards de Métricas */
    div[data-testid="stMetricValue"] {{
        color: {TAXBASE_BLUE};
        font-weight: bold;
    }}

    /* Abas */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: white;
        border-radius: 4px 4px 0px 0px;
        color: {TAXBASE_BLUE};
        font-weight: bold;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {TAXBASE_BLUE} !important;
        color: white !important;
    }}
    </style>
""", unsafe_allow_html=True)


# --- 2. SISTEMA DE AUTENTICAÇÃO SIMPLES ---
def check_password():
    """Retorna True se login der certo, False caso contrário"""
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_role'] = None
        st.session_state['user_name'] = None

    if not st.session_state['logged_in']:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            # Tenta mostrar logo se existir
            if os.path.exists("logo_taxbase.png"):
                st.image("logo_taxbase.png", width=200)
            else:
                st.title("Taxbase Hub")

            st.markdown("### Acesso Restrito")
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")

            if st.button("Entrar"):
                # CREDENCIAIS (Hardcoded para teste)
                if usuario == "fabricio" and senha == "admin123":
                    st.session_state['logged_in'] = True
                    st.session_state['user_role'] = 'admin'  # PODE EDITAR
                    st.session_state['user_name'] = 'Fabrício'
                    st.rerun()
                elif usuario == "fernando" and senha == "view123":
                    st.session_state['logged_in'] = True
                    st.session_state['user_role'] = 'viewer'  # SÓ VÊ
                    st.session_state['user_name'] = 'Fernando'
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        return False
    return True


# --- 3. FUNÇÕES DE DADOS (Motor) ---
def carregar_dados_mes(mes_arquivo):
    """Carrega o CSV de um mês específico da pasta /data"""
    file_path = os.path.join("data", mes_arquivo)

    if not os.path.exists(file_path):
        return None

    try:
        try:
            df = pd.read_csv(file_path, sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, sep=';', encoding='latin1')
    except Exception as e:
        st.error(f"Erro ao ler arquivo {mes_arquivo}: {e}")
        return None

    # Limpeza básica
    df['Contato_Clean'] = df['Contato'].apply(lambda x: str(x).strip().upper() if pd.notnull(x) else "")

    # Cruzamento com statusContatos.xlsx (Sempre lê o arquivo mestre atualizado)
    map_path = 'statusContatos.xlsx'
    if os.path.exists(map_path):
        try:
            df_map = pd.read_excel(map_path, engine='openpyxl')
            # Normalização de colunas
            cols_map = {c.upper(): c for c in df_map.columns}
            if 'NOME DO CONTATO' in cols_map and 'NOME CLIENTE' in cols_map:
                col_nome = cols_map['NOME DO CONTATO']
                col_cli = cols_map['NOME CLIENTE']

                df_map_clean = df_map[[col_nome, col_cli]].copy()
                df_map_clean.columns = ['Nome_Map', 'Cliente_Alvo']
                df_map_clean['Nome_Map_Clean'] = df_map_clean['Nome_Map'].apply(
                    lambda x: str(x).strip().upper() if pd.notnull(x) else "")
                df_map_clean = df_map_clean.drop_duplicates(subset=['Nome_Map_Clean'])

                # Merge
                df = pd.merge(df, df_map_clean, left_on='Contato_Clean', right_on='Nome_Map_Clean', how='left')
                df['Cliente_Final'] = df['Cliente_Alvo'].fillna("NÃO IDENTIFICADO")
            else:
                df['Cliente_Final'] = "NÃO IDENTIFICADO"
        except:
            df['Cliente_Final'] = "NÃO IDENTIFICADO"  # Fallback se falhar leitura do excel
    else:
        df['Cliente_Final'] = "NÃO IDENTIFICADO"

    # Datas
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'])
        df['Dia'] = df['Data'].dt.date

    return df


# --- 4. INTERFACE PRINCIPAL ---
def main_app():
    # Cabeçalho
    c1, c2 = st.columns([1, 6])
    with c1:
        if os.path.exists("logo_taxbase.png"):
            st.image("logo_taxbase.png", width=120)
    with c2:
        st.markdown(f"## Métricas de Atendimento | Olá, {st.session_state['user_name']}")

    st.markdown("---")

    # Definição das Abas
    tabs = st.tabs(["📊 Janeiro/26", "📊 Fevereiro/26", "📊 Março/26", "⚙️ Gestão (Admin)"])

    # --- LÓGICA DAS ABAS DE MESES ---
    meses_config = {
        "📊 Janeiro/26": "jan_2026.csv",
        "📊 Fevereiro/26": "fev_2026.csv",
        "📊 Março/26": "mar_2026.csv"
    }

    # Renderiza as abas de métricas
    for tab_name, arquivo_csv in meses_config.items():
        with tabs[list(meses_config.keys()).index(tab_name)]:

            df = carregar_dados_mes(arquivo_csv)

            if df is None:
                st.info(f"Ainda não há dados carregados para {tab_name}.")
            else:
                # --- FILTROS NO TOPO (Substituindo Sidebar) ---
                with st.container():
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        analistas = ["Todos"] + list(df['Atendido por'].unique())
                        filtro_analista = st.selectbox(f"Analista ({tab_name})", analistas, key=f"an_{tab_name}")
                    with col_f2:
                        # Filtro de data se quiser, por enquanto deixei fixo
                        pass

                    # Aplicar Filtros
                    df_filtered = df.copy()
                    if filtro_analista != "Todos":
                        df_filtered = df_filtered[df_filtered['Atendido por'] == filtro_analista]

                    # --- KPIS ---
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("Chamados", len(df_filtered))
                    k2.metric("Clientes Únicos", df_filtered['Cliente_Final'].nunique())

                    top_cli = df_filtered['Cliente_Final'].value_counts().idxmax() if not df_filtered.empty else "-"
                    vol_top = df_filtered['Cliente_Final'].value_counts().max() if not df_filtered.empty else 0
                    k3.metric("Top Cliente", top_cli)
                    k4.metric("Vol. Top 1", vol_top)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # --- GRÁFICOS (Sem o de Status) ---
                    g1, g2 = st.columns([2, 1])

                    with g1:
                        st.subheader("Ranking de Clientes")
                        ranking = df_filtered['Cliente_Final'].value_counts().head(10).reset_index()
                        ranking.columns = ['Cliente', 'Chamados']
                        # Cor azul taxbase
                        fig_bar = px.bar(ranking, x='Chamados', y='Cliente', orientation='h',
                                         text='Chamados', color_discrete_sequence=[TAXBASE_BLUE])
                        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig_bar, use_container_width=True)

                    with g2:
                        st.subheader("Evolução Diária")
                        timeline = df_filtered.groupby('Dia').size().reset_index(name='Chamados')
                        fig_line = px.line(timeline, x='Dia', y='Chamados', markers=True)
                        fig_line.update_traces(line_color=TAXBASE_BLUE)
                        st.plotly_chart(fig_line, use_container_width=True)

    # --- ABA DE GESTÃO (SÓ PARA ADMIN) ---
    with tabs[3]:  # Aba de Admin
        if st.session_state['user_role'] == 'admin':
            st.header("⚙️ Painel de Controle")
            st.markdown("Aqui você atualiza os dados do sistema. As alterações refletem imediatamente para todos.")

            c_up1, c_up2 = st.columns(2)

            # UPLOAD DE MÉTRICAS MENSAIS
            with c_up1:
                st.subheader("1. Atualizar Métricas (CSV Onvio)")
                uploaded_csv = st.file_uploader("Solte o arquivo do Onvio aqui (.csv)", type=['csv'])
                mes_destino = st.selectbox("Este arquivo pertence a qual mês?",
                                           ["jan_2026.csv", "fev_2026.csv", "mar_2026.csv"])

                if st.button("Salvar/Atualizar Mês"):
                    if uploaded_csv is not None:
                        # Garante que a pasta existe
                        if not os.path.exists("data"):
                            os.makedirs("data")

                        # Salva o arquivo na pasta data com o nome padrão
                        with open(os.path.join("data", mes_destino), "wb") as f:
                            f.write(uploaded_csv.getbuffer())
                        st.success(f"Arquivo de {mes_destino} atualizado com sucesso!")
                        st.rerun()  # Atualiza a tela

            # UPLOAD DA PLANILHA DE CONTATOS
            with c_up2:
                st.subheader("2. Atualizar 'De/Para' (Excel)")
                uploaded_xlsx = st.file_uploader("Atualizar statusContatos.xlsx", type=['xlsx'])

                if st.button("Salvar Novos Contatos"):
                    if uploaded_xlsx is not None:
                        with open("statusContatos.xlsx", "wb") as f:
                            f.write(uploaded_xlsx.getbuffer())
                        st.success("Base de Contatos (De/Para) atualizada!")
                        st.rerun()

            st.markdown("---")
            if st.button("Sair / Logout"):
                st.session_state['logged_in'] = False
                st.rerun()

        else:
            # Visão do Fernando (Viewer) na aba de Admin
            st.warning("🔒 Área restrita para administradores.")
            if st.button("Sair"):
                st.session_state['logged_in'] = False
                st.rerun()


# --- EXECUÇÃO ---
if __name__ == "__main__":
    if check_password():
        main_app()