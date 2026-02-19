# ==============================================================================
# HUB TAXBASE - BACKEND FLASK + JWT
# ==============================================================================

import os
import sys
import json
import hashlib
import time
import requests
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, render_template

# JWT usando PyJWT
import jwt as pyjwt


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder='static', template_folder='templates')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'taxbase-hub-secret-2026')

# BigQuery Config
BQ_PROJECT_ID = "taxbasehub"
BQ_DATASET_ID = "hub_dados"
TABLE_USUARIOS = f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}.usuarios"
TABLE_SISTEMAS = f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}.sistemas"
TABLE_FUNCOES = f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}.funcoes"

ADM_EMAIL = "admin@taxbase.com.br"

# Audit Fiscal
AUDIT_FISCAL_DIR = os.path.join(os.path.dirname(__file__), 'AUDIT_FISCAL')
sys.path.insert(0, AUDIT_FISCAL_DIR)
KEY_FILE = os.path.join(AUDIT_FISCAL_DIR, 'credentials.json')

# BigQuery tables (Audit)
BQ_TABLE_ID = 'auditor-processos.auditoria_fiscal.registros_auditoria'
BQ_TABLE_MASTER = 'auditor-processos.auditoria_fiscal.empresas_obrigacoes'
BQ_TABLE_IGNORED = 'auditor-processos.auditoria_fiscal.controle_ignorados'
BQ_TABLE_DISCARDED = 'auditor-processos.auditoria_fiscal.controle_descartados'


# ==============================================================================
# FUNÇÕES UTILITÁRIAS (BigQuery)
# ==============================================================================

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def get_bq_client():
    from google.cloud import bigquery
    # Tenta carregar do arquivo local (Dev)
    if os.path.exists(KEY_FILE):
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(
            KEY_FILE,
            scopes=["https://www.googleapis.com/auth/bigquery",
                    "https://www.googleapis.com/auth/spreadsheets.readonly",
                    "https://www.googleapis.com/auth/drive.readonly"]
        )
        return bigquery.Client(credentials=creds, project=BQ_PROJECT_ID)
    
    # Fallback para credenciais padrão (Cloud Run)
    import google.auth
    creds, project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/bigquery",
                "https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/drive.readonly"]
    )
    return bigquery.Client(credentials=creds, project=BQ_PROJECT_ID)

def run_query(query):
    """Executa query SQL e retorna lista de dicts"""
    try:
        client = get_bq_client()
        df = client.query(query).to_dataframe()
        
        # Converte para dict
        records = df.to_dict('records')
        
        # Garante que não tenha tipos numpy (int64, ndarray) que quebram o jsonify
        # Hack rápido: iterar e converter ndarray para list
        import numpy as np
        for row in records:
            for k, v in row.items():
                if isinstance(v, np.ndarray):
                    row[k] = v.tolist()
        
        return records
    except Exception as e:
        print(f"Erro Query: {e}")
        return []

def run_command(query):
    """Executa comando DML (INSERT, UPDATE, DELETE)"""
    try:
        client = get_bq_client()
        client.query(query).result()
        return True
    except Exception as e:
        print(f"Erro Command: {e}")
        return False

# ==============================================================================
# FUNÇÕES DE PERMISSÕES
# ==============================================================================

def carregar_funcoes():
    return run_query(f"SELECT * FROM `{TABLE_FUNCOES}`")

def obter_funcao_por_id(funcao_id):
    # Fallback local para dev
    DEV_FUNCOES = {
        "admin_master": {"id": "admin_master", "nome": "Admin Master", "permissao": "admin_master", "sistemas": ["*"]},
        "admin": {"id": "admin", "nome": "Administrador", "permissao": "admin", "sistemas": ["*"]},
    }
    
    res = run_query(f"SELECT * FROM `{TABLE_FUNCOES}` WHERE id = '{funcao_id}'")
    if res:
        return res[0]
    
    # BigQuery vazio ou inacessível — usa fallback
    fallback = DEV_FUNCOES.get(funcao_id)
    if fallback:
        print(f"DEBUG: Usando função local para '{funcao_id}'")
    return fallback

def obter_funcao_usuario(email):
    # Join manual para evitar complexidade na query agora
    res_user = run_query(f"SELECT * FROM `{TABLE_USUARIOS}` WHERE email = '{email}'")
    if not res_user: return None
    
    user = res_user[0]
    funcao_id = user.get('funcao_id', 'admin_master' if email == ADM_EMAIL else None)
    
    if funcao_id:
        return obter_funcao_por_id(funcao_id)
    return None

def usuario_tem_acesso_sistema(funcao, sistema_id):
    if not funcao:
        return False
    # No BQ, arrays vêm como lista python
    sistemas_permitidos = funcao.get('sistemas', [])
    # Se vier como string (caso antigo), converte
    if isinstance(sistemas_permitidos, str):
         sistemas_permitidos = [sistemas_permitidos]
         
    return '*' in sistemas_permitidos or sistema_id in sistemas_permitidos

def filtrar_sistemas_por_funcao(sistemas, funcao):
    if not funcao:
        return []
    sistemas_permitidos = funcao.get('sistemas', [])
    if isinstance(sistemas_permitidos, str):
         sistemas_permitidos = [sistemas_permitidos]

    if '*' in sistemas_permitidos:
        return sistemas
    return [s for s in sistemas if s.get('sistema_id') in sistemas_permitidos]


# ==============================================================================
# AUTH & LOGIN
# ==============================================================================

def verificar_login(email, senha):
    senha_hash = hash_senha(senha)
    safe_email = email.replace("'", "") 
    
    print(f"DEBUG_LOGIN: Tentando login para {safe_email} com hash {senha_hash}")
    
    # --- Fallback local para dev (quando BigQuery está inacessível) ---
    DEV_USERS = {
        "admin@taxbase.com.br": {
            "email": "admin@taxbase.com.br",
            "nome": "Admin Taxbase",
            "funcao_id": "admin_master",
            "senha": hash_senha("admin123")
        }
    }
    
    # Tenta BigQuery primeiro
    query = f"SELECT * FROM `{TABLE_USUARIOS}` WHERE email = '{safe_email}' AND senha = '{senha_hash}'"
    res = run_query(query)
    
    if res:
        return res[0]
    
    # BigQuery retornou vazio — pode ser credenciais erradas OU BigQuery inacessível
    # Tenta fallback local
    dev_user = DEV_USERS.get(safe_email)
    if dev_user and dev_user["senha"] == senha_hash:
        print(f"DEBUG_LOGIN: Login via fallback local para {safe_email}")
        return dev_user
    
    print(f"DEBUG_LOGIN: Login falhou para {safe_email}")
    return None


def criar_novo_usuario(email, nome, funcao_id, senha):
    safe_email = email.replace("'", "")
    # Check exists
    check = run_query(f"SELECT 1 FROM `{TABLE_USUARIOS}` WHERE email = '{safe_email}'")
    if check:
        return False, "E-mail já cadastrado."
    
    senha_hash = hash_senha(senha)
    
    query = f"""
        INSERT INTO `{TABLE_USUARIOS}` (email, nome, funcao_id, senha)
        VALUES ('{safe_email}', '{nome.replace("'", "")}', '{funcao_id}', '{senha_hash}')
    """
    if run_command(query):
        return True, "Usuário criado com sucesso!"
    return False, "Erro ao criar usuário no banco."


def gerar_token(email, nome, funcao):
    payload = {
        'email': email,
        'nome': nome,
        'funcao_id': funcao.get('id', '') if funcao else '',
        'funcao_nome': funcao.get('nome', '') if funcao else '',
        'permissao': funcao.get('permissao', 'usuario') if funcao else 'usuario',
        'sistemas': funcao.get('sistemas', []) if funcao else [],
        'exp': datetime.utcnow() + timedelta(hours=12)
    }
    return pyjwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


def decodificar_token(token):
    try:
        return pyjwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None


# Decorator para proteger rotas
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token não fornecido'}), 401
        dados = decodificar_token(token)
        if not dados:
            return jsonify({'error': 'Token inválido ou expirado'}), 401
        request.user = dados
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    @auth_required
    def decorated(*args, **kwargs):
        if request.user.get('permissao') != 'admin':
            return jsonify({'error': 'Acesso negado - admin necessário'}), 403
        return f(*args, **kwargs)
    return decorated


def master_required(f):
    @wraps(f)
    @auth_required
    def decorated(*args, **kwargs):
        if request.user.get('email') != ADM_EMAIL:
            return jsonify({'error': 'Acesso negado - admin master necessário'}), 403
        return f(*args, **kwargs)
    return decorated


# ==============================================================================
# STATUS DO SISTEMA
# ==============================================================================

def check_ping(url):
    try:
        r = requests.get(url, timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def obter_status_sistema(sistema):
    modo = sistema.get("status_manual", "Automático")
    if modo == "Manutenção":
        return "manutencao", "Manutenção"
    elif modo == "Forçar Offline":
        return "offline", "Offline"
    elif modo == "Forçar Online":
        return "online", "Online"
    else:
        online = check_ping(sistema['url'])
        return ("online", "Online") if online else ("offline", "Offline")


# ==============================================================================
# INICIALIZAÇÃO
# ==============================================================================
# Inicialização de banco feita via script migrate_to_bq.py


# ==============================================================================
# ROTAS - PÁGINAS HTML
# ==============================================================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/auditor')
def auditor():
    return render_template('auditor.html')


# Servir logo
@app.route('/static/img/<path:filename>')
def serve_img(filename):
    return send_from_directory(os.path.join(app.static_folder, 'img'), filename)


# ==============================================================================
# API - AUTENTICAÇÃO
# ==============================================================================

import traceback

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        senha = data.get('senha', '')

        print(f"DEBUG_ROUTE: Login request for {email}")

        usuario = verificar_login(email, senha)
        if not usuario:
            print("DEBUG_ROUTE: Usuario nao encontrado ou senha incorreta.")
            return jsonify({'error': 'Credenciais inválidas'}), 401

        funcao = obter_funcao_por_id(usuario.get('funcao_id', ''))
        token = gerar_token(email, usuario.get('nome', email), funcao)

        return jsonify({
            'token': token,
            'usuario': {
                'email': email,
                'nome': usuario.get('nome', email),
                'funcao': funcao if funcao else {},
                'permissao': funcao.get('permissao', 'usuario') if funcao else 'usuario',
                'is_admin_master': email == ADM_EMAIL
            }
        })
    except Exception as e:
        print("ERROR_ROUTE_LOGIN:")
        traceback.print_exc()
        return jsonify({'error': f"Erro interno no login: {str(e)}"}), 500


@app.route('/api/me', methods=['GET'])
@auth_required
def api_me():
    return jsonify(request.user)


# ==============================================================================
# API - SISTEMAS
# ==============================================================================

@app.route('/api/sistemas', methods=['GET'])
@auth_required
def api_listar_sistemas():
    sistemas = run_query(f"SELECT * FROM `{TABLE_SISTEMAS}`")

    # Fallback: quando BigQuery está inacessível, usa sistemas_taxbase.json local
    if not sistemas:
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'sistemas_taxbase.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                sistemas = json.load(f)
            print("DEBUG: Sistemas carregados do arquivo local (BigQuery indisponível)")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar sistemas locais: {e}")
            sistemas = []

    # Adicionar sistema_id se não existir
    for sis in sistemas:
        if 'sistema_id' not in sis:
            sis['sistema_id'] = sis['nome'].upper().replace(' ', '_')

    # Filtrar por função
    funcao = obter_funcao_por_id(request.user.get('funcao_id', ''))
    sistemas_filtrados = filtrar_sistemas_por_funcao(sistemas, funcao)

    # Adicionar status
    resultado = []
    for sis in sistemas_filtrados:
        status_class, status_texto = obter_status_sistema(sis)
        
        # Correção de bugs de None na url
        if not sis.get('url'): sis['url'] = '#'

        resultado.append({
            **sis,
            'status_class': status_class,
            'status_texto': status_texto,
            'is_internal': sis.get('sistema_id') in ['AUDIT_FISCAL', 'METRICAS_ONVIO']
        })

    return jsonify(resultado)


@app.route('/api/sistemas', methods=['POST'])
@admin_required
def api_criar_sistema():
    data = request.get_json()
    
    novo = {
        "nome": data.get('nome', ''),
        "sistema_id": data.get('sistema_id', '').upper(),
        "url": data.get('url', ''),
        "categoria": data.get('categoria', ''),
        "desc": data.get('desc', ''),
        "status_manual": data.get('status_manual', 'Automático')
    }

    if not novo['nome'] or not novo['sistema_id'] or not novo['url']:
        return jsonify({'error': 'Nome, ID e URL são obrigatórios'}), 400

    query = f"""
        INSERT INTO `{TABLE_SISTEMAS}` (sistema_id, nome, url, categoria, `desc`, status_manual)
        VALUES ('{novo['sistema_id']}', '{novo['nome']}', '{novo['url']}', '{novo['categoria']}', '{novo['desc']}', '{novo['status_manual']}')
    """
    if run_command(query):
        return jsonify({'message': 'Sistema criado!', 'sistema': novo}), 201
    return jsonify({'error': 'Erro ao criar sistema'}), 500


@app.route('/api/sistemas/<sistema_id>', methods=['PUT'])
@admin_required
def api_editar_sistema(sistema_id):
    data = request.get_json()
    
    updates = []
    # Mapear campos JSON para colunas BQ
    field_map = {'desc': '`desc`'} # Escape desc keyword
    
    for key in ['nome', 'url', 'categoria', 'desc', 'status_manual']:
        if key in data:
            val = data[key]
            col = field_map.get(key, key)
            updates.append(f"{col} = '{val}'")
            
    if not updates:
        return jsonify({'message': 'Nada a atualizar'})

    query = f"UPDATE `{TABLE_SISTEMAS}` SET {', '.join(updates)} WHERE sistema_id = '{sistema_id}'"
    
    if run_command(query):
         return jsonify({'message': 'Atualizado!'})

    return jsonify({'error': 'Erro ao atualizar'}), 500


@app.route('/api/sistemas/<sistema_id>', methods=['DELETE'])
@admin_required
def api_excluir_sistema(sistema_id):
    query = f"DELETE FROM `{TABLE_SISTEMAS}` WHERE sistema_id = '{sistema_id}'"
    run_command(query)
    return jsonify({'message': 'Excluído!'})


# ==============================================================================
# API - USUÁRIOS
# ==============================================================================

# ==============================================================================
# API - USUÁRIOS
# ==============================================================================

@app.route('/api/usuarios', methods=['GET'])
@admin_required
def api_listar_usuarios():
    usuarios = run_query(f"SELECT * FROM `{TABLE_USUARIOS}`")
    
    resultado = []
    for u in usuarios:
        funcao = obter_funcao_por_id(u.get('funcao_id', ''))
        resultado.append({
            'email': u['email'],
            'nome': u.get('nome', u['email']),
            'funcao_id': u.get('funcao_id', ''),
            'funcao_nome': funcao['nome'] if funcao else 'Sem função',
            'permissao': funcao.get('permissao', 'usuario') if funcao else 'usuario',
            'is_admin_master': u['email'] == ADM_EMAIL
        })

    return jsonify(resultado)


@app.route('/api/usuarios', methods=['POST'])
@admin_required
def api_criar_usuario():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    nome = data.get('nome', '')
    funcao_id = data.get('funcao_id', '')
    senha = data.get('senha', '')

    if not email or not nome or not senha:
        return jsonify({'error': 'Email, nome e senha são obrigatórios'}), 400

    ok, msg = criar_novo_usuario(email, nome, funcao_id, senha)
    if ok:
        return jsonify({'message': msg}), 201
    return jsonify({'error': msg}), 400


@app.route('/api/usuarios/<email>', methods=['PUT'])
@admin_required
def api_editar_usuario(email):
    data = request.get_json()
    updates = []
    
    if 'funcao_id' in data:
        updates.append(f"funcao_id = '{data['funcao_id']}'")
    if 'nome' in data:
        updates.append(f"nome = '{data['nome']}'")
    if 'senha' in data and data['senha']:
        s = hash_senha(data['senha'])
        updates.append(f"senha = '{s}'")
        
    if not updates:
        return jsonify({'message': 'Nada a atualizar'})

    query = f"UPDATE `{TABLE_USUARIOS}` SET {', '.join(updates)} WHERE email = '{email}'"
    run_command(query)
    
    return jsonify({'message': 'Atualizado!'})


@app.route('/api/usuarios/<email>', methods=['DELETE'])
@admin_required
def api_excluir_usuario(email):
    if email == ADM_EMAIL:
        return jsonify({'error': 'Não é possível excluir o admin master'}), 403
    
    run_command(f"DELETE FROM `{TABLE_USUARIOS}` WHERE email = '{email}'")
    return jsonify({'message': 'Excluído!'})


# ==============================================================================
# API - FUNÇÕES / CARGOS
# ==============================================================================

@app.route('/api/funcoes', methods=['GET'])
@auth_required
def api_listar_funcoes():
    return jsonify(carregar_funcoes())


@app.route('/api/funcoes', methods=['POST'])
@master_required
def api_criar_funcao():
    data = request.get_json()
    
    funcao_id = data.get('id', '').lower().replace(' ', '_')
    if not funcao_id or not data.get('nome'):
        return jsonify({'error': 'ID e Nome são obrigatórios'}), 400

    # Check
    check = run_query(f"SELECT 1 FROM `{TABLE_FUNCOES}` WHERE id = '{funcao_id}'")
    if check:
        return jsonify({'error': 'ID já existe'}), 400
        
    sistemas = data.get('sistemas', ['*'])
    # BQ Array string format: ["a", "b"]
    sis_str = json.dumps(sistemas)

    query = f"""
        INSERT INTO `{TABLE_FUNCOES}` (id, nome, sistemas, permissao, descricao)
        VALUES ('{funcao_id}', '{data['nome']}', JSON_ARRAY{sis_str}, '{data.get('permissao', 'usuario')}', '{data.get('descricao', '')}')
    """
    # Note: JSON_ARRAY[...] might be tricky with string replacement.
    # Better to just pass the string representation if the field is defined as REPEATED STRING?
    # Actually, INSERT expects ARRAY<STRING>. usage: ["a", "b"]
    # Let's simple format:
    sis_list_str = str(sistemas).replace("'", '"') # ['*'] -> ["*"]
    
    query = f"""
        INSERT INTO `{TABLE_FUNCOES}` (id, nome, sistemas, permissao, descricao)
        VALUES ('{funcao_id}', '{data['nome']}', {sis_list_str}, '{data.get('permissao', 'usuario')}', '{data.get('descricao', '')}')
    """

    if run_command(query):
        return jsonify({'message': f"Função '{data['nome']}' criada!"}), 201
    return jsonify({'error': 'Erro ao criar função'}), 500


@app.route('/api/funcoes/<funcao_id>', methods=['PUT'])
@master_required
def api_editar_funcao(funcao_id):
    data = request.get_json()
    updates = []
    
    if 'nome' in data: updates.append(f"nome = '{data['nome']}'")
    if 'permissao' in data: updates.append(f"permissao = '{data['permissao']}'")
    if 'descricao' in data: updates.append(f"descricao = '{data['descricao']}'")
    if 'sistemas' in data:
        sis_list_str = str(data['sistemas']).replace("'", '"')
        updates.append(f"sistemas = {sis_list_str}")

    if not updates:
        return jsonify({'message': 'Nada a atualizar'})

    query = f"UPDATE `{TABLE_FUNCOES}` SET {', '.join(updates)} WHERE id = '{funcao_id}'"
    run_command(query)
    
    return jsonify({'message': 'Atualizado!'})


@app.route('/api/funcoes/<funcao_id>', methods=['DELETE'])
@master_required
def api_excluir_funcao(funcao_id):
    if funcao_id == 'admin_master':
        return jsonify({'error': 'Não é possível excluir admin_master'}), 403
    
    run_command(f"DELETE FROM `{TABLE_FUNCOES}` WHERE id = '{funcao_id}'")
    return jsonify({'message': 'Excluído!'})


# ==============================================================================
# API - AUDITOR FISCAL
# ==============================================================================

def get_bq_credentials():
    """Retorna credenciais do BigQuery (Arquivo local ou Default/Cloud)"""
    try:
        # Tenta carregar do arquivo local (Dev)
        if os.path.exists(KEY_FILE):
            from google.oauth2 import service_account
            return service_account.Credentials.from_service_account_file(
                KEY_FILE,
                scopes=["https://www.googleapis.com/auth/bigquery",
                        "https://www.googleapis.com/auth/spreadsheets.readonly",
                        "https://www.googleapis.com/auth/drive.readonly"]
            )
        
        # Fallback para credenciais padrão do ambiente (Cloud Run)
        import google.auth
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/bigquery",
                    "https://www.googleapis.com/auth/spreadsheets.readonly",
                    "https://www.googleapis.com/auth/drive.readonly"]
        )
        return credentials
    except Exception as e:
        print(f"Erro ao obter credenciais: {e}")
        return None


@app.route('/api/auditor/painel', methods=['GET'])
@auth_required
def api_auditor_painel():
    """Retorna dados do painel fiscal processados"""
    try:
        from google.cloud import bigquery
        creds = get_bq_credentials()
        if not creds:
            return jsonify({'error': 'Credenciais BigQuery não configuradas'}), 500

        client = bigquery.Client(credentials=creds)

        # Período de apuração (query param ou auto-calculado)
        from datetime import datetime, timedelta
        def calc_competencia():
            hoje = datetime.now()
            primeiro_dia = hoje.replace(day=1)
            mes_anterior = primeiro_dia - timedelta(days=1)
            return mes_anterior.strftime("%m/%Y")

        def gerar_opcoes_periodo(n_meses=12):
            opcoes = []
            hoje = datetime.now()
            for i in range(1, n_meses + 1):
                primeiro_dia = hoje.replace(day=1)
                data_alvo = primeiro_dia - timedelta(days=1)
                for _ in range(i - 1):
                    data_alvo = data_alvo.replace(day=1) - timedelta(days=1)
                opcoes.append(data_alvo.strftime("%m/%Y"))
            return opcoes

        periodo_param = request.args.get('periodo', '').strip()
        print(f"DEBUG: api_auditor_painel param='{periodo_param}'")
        competencia = periodo_param if periodo_param else calc_competencia()

        # Calcular período EFD (1 mês antes do selecionado)
        try:
            dt_selecionada = datetime.strptime(competencia, "%m/%Y")
            # Subtrair 1 mês
            dt_efd = dt_selecionada.replace(day=1) - timedelta(days=1)
            # Ir para o primeiro dia do mês anterior para formatar
            dt_efd = dt_efd.replace(day=1)
            periodo_efd = dt_efd.strftime("%m/%Y")
        except Exception:
            periodo_efd = competencia # Fallback

        print(f"DEBUG: periodo_padrao='{competencia}', periodo_efd='{periodo_efd}'")

        # Carregar dados BQ - filtrar por período (Regra EFD vs Geral)
        # Regra:
        # - Geral: periodo = competencia
        # - EFD: periodo = periodo_efd
        query_bq = f"""
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
            WHERE (
                (t.periodo = '{competencia}' AND t.categoria != 'EFD_CONTRIBUICOES')
                OR
                (t.periodo = '{periodo_efd}' AND t.categoria = 'EFD_CONTRIBUICOES')
            )
            AND NOT EXISTS (
                SELECT 1 
                FROM `{BQ_TABLE_DISCARDED}` d
                WHERE d.id_arquivo = t.id_arquivo
                AND TIMESTAMP_TRUNC(d.data_processamento, SECOND) = TIMESTAMP_TRUNC(t.data_processamento, SECOND)
            )
        """

        import pandas as pd
        df_bq = client.query(query_bq).to_dataframe()
        if not df_bq.empty and 'data_proc_full' in df_bq.columns:
            df_bq['data_proc_full'] = df_bq['data_proc_full'].astype(str)
        last_update = str(df_bq['data_proc_full'].max()) if not df_bq.empty else None

        # Carregar master
        try:
            from reference_data import ReferenceLoader
            loader = ReferenceLoader(creds)
            loader.load_data()
            df_master = loader.df_empresas if loader.df_empresas is not None else pd.DataFrame()
        except Exception as e:
            print(f"ERRO CRITICO AO CARREGAR REFERENCE DATA: {e}")
            import traceback
            traceback.print_exc()
            df_master = pd.DataFrame()

        if df_master.empty:
            return jsonify({'painel': [], 'last_update': last_update, 'competencia': competencia, 'periodos_disponiveis': gerar_opcoes_periodo(12)})

        # Carregar ignorados
        try:
            query_ign = f"SELECT cnpj, obrigacao FROM `{BQ_TABLE_IGNORED}`"
            df_ign = client.query(query_ign).to_dataframe()
            ignored = {}
            for _, row in df_ign.iterrows():
                cnpj = str(row['cnpj'])
                if cnpj not in ignored:
                    ignored[cnpj] = []
                ignored[cnpj].append(row['obrigacao'])
        except Exception:
            ignored = {}

        # Processar painel
        if 'cnpj' in df_master.columns:
            df_master['clean_cnpj'] = df_master['cnpj'].astype(str).str.replace(r'\D', '', regex=True)

        # Tratar Grupos Vazios
        if 'grupo' in df_master.columns:
             df_master['grupo'] = df_master['grupo'].fillna('')
             df_master['grupo'] = df_master['grupo'].astype(str).str.strip()
             df_master['grupo'] = df_master['grupo'].replace(['', 'nan', 'None'], 'Sem Grupo')
        else:
             df_master['grupo'] = 'Sem Grupo'

        try:
            from file_classifier import AuditorClassifier
            metas = list(AuditorClassifier().CATEGORIES.keys())
        except Exception:
            metas = []

        painel_data = []
        for _, row in df_master.iterrows():
            cnpj = row['clean_cnpj']
            nome = row.get('empresa', 'N/A')
            grupo = row.get('grupo', 'Sem Grupo')

            entregas = []
            if not df_bq.empty and 'cnpj' in df_bq.columns:
                df_bq['cnpj_clean'] = df_bq['cnpj'].astype(str).str.replace(r'\D', '', regex=True)
                entregas = df_bq[df_bq['cnpj_clean'] == cnpj]['obrigacao'].unique().tolist()

            lista_ignorados = ignored.get(cnpj, [])
            faltantes_ativos = [m for m in metas if m not in entregas and m not in lista_ignorados]
            faltantes_ignorados = [m for m in metas if m not in entregas and m in lista_ignorados]

            meta_ajustada = max(1, len(metas) - len(lista_ignorados))
            progresso = min(1.0, len(entregas) / meta_ajustada)
            status = "OK" if progresso == 1 else "PENDENTE"

            # Arquivos para cada entrega
            arquivos_entregues = {}
            if not df_bq.empty:
                for obr in entregas:
                    files = df_bq[(df_bq['cnpj_clean'] == cnpj) & (df_bq['obrigacao'] == obr)].sort_values('periodo', ascending=False)
                    arquivos_entregues[obr] = files[['periodo', 'nome_arquivo', 'link_arquivo', 'id_arquivo', 'data_proc_full']].to_dict('records')

            painel_data.append({
                "cnpj": cnpj,
                "empresa": nome,
                "grupo": grupo,
                "entregues": entregas,
                "faltantes_ativos": faltantes_ativos,
                "faltantes_ignorados": faltantes_ignorados,
                "qtd_pendentes": len(faltantes_ativos),
                "progresso": progresso,
                "status": status,
                "has_delivery": len(entregas) > 0,
                "arquivos": arquivos_entregues
            })

        # Processar Daily Stats
        daily_stats = []
        if not df_bq.empty and 'data_proc' in df_bq.columns:
             counts = df_bq['data_proc'].value_counts().sort_index()
             daily_stats = [{'date': str(d), 'count': int(c)} for d, c in counts.items()]

        return jsonify({
            'painel': painel_data,
            'last_update': last_update,
            'competencia': competencia,
            'total_metas': len(metas),
            'metas': metas,
            'daily_stats': daily_stats,
            'periodos_disponiveis': gerar_opcoes_periodo(12)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auditor/unidentified', methods=['GET'])
@admin_required
def api_auditor_unidentified():
    """Retorna arquivos não identificados"""
    try:
        from google.cloud import bigquery
        import pandas as pd
        creds = get_bq_credentials()
        client = bigquery.Client(credentials=creds)

        query = f"""
            SELECT t.id_arquivo, t.nome_arquivo, t.link_arquivo, t.data_processamento
            FROM `{BQ_TABLE_ID}` t
            WHERE (t.status_auditoria = 'NAO_IDENTIFICADO' 
                OR t.categoria IS NULL
                OR t.categoria = 'NAO_IDENTIFICADO'
                OR t.categoria = '')
            AND NOT EXISTS (
                SELECT 1 
                FROM `{BQ_TABLE_DISCARDED}` d
                WHERE d.id_arquivo = t.id_arquivo
                AND TIMESTAMP_TRUNC(d.data_processamento, SECOND) = TIMESTAMP_TRUNC(t.data_processamento, SECOND)
            )
            ORDER BY t.data_processamento DESC
            LIMIT 50
        """
        df = client.query(query).to_dataframe()
        # Converter timestamps para string para JSON
        if not df.empty and 'data_processamento' in df.columns:
            df['data_processamento'] = df['data_processamento'].astype(str)
        return jsonify(df.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auditor/allocate', methods=['POST'])
@admin_required
def api_auditor_allocate():
    """Aloca um arquivo não identificado a uma empresa e obrigação (registro específico)"""
    data = request.json
    id_arquivo = data.get('id_arquivo')
    data_proc = data.get('data_processamento', '')
    cnpj = data.get('cnpj')
    obrigacao = data.get('obrigacao')

    if not all([id_arquivo, cnpj, obrigacao]):
        return jsonify({'error': 'Dados incompletos'}), 400

    try:
        from google.cloud import bigquery
        client = bigquery.Client(credentials=get_bq_credentials())
        
        # Update apenas o registro específico usando id_arquivo + data_processamento
        query = f"""
            UPDATE `{BQ_TABLE_ID}`
            SET 
                cnpj = @cnpj,
                categoria = @obrigacao,
                status_auditoria = 'ALOCADO_MANUAL'
            WHERE id_arquivo = @id_arquivo
            AND TIMESTAMP_TRUNC(data_processamento, SECOND) = TIMESTAMP_TRUNC(TIMESTAMP(@data_proc), SECOND)
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("cnpj", "STRING", cnpj),
                bigquery.ScalarQueryParameter("obrigacao", "STRING", obrigacao),
                bigquery.ScalarQueryParameter("id_arquivo", "STRING", id_arquivo),
                bigquery.ScalarQueryParameter("data_proc", "STRING", data_proc),
            ]
        )
        client.query(query, job_config=job_config).result()
        
        return jsonify({'message': 'Arquivo alocado com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/auditor/discard', methods=['POST'])
@admin_required
def api_auditor_discard():
    """Descarta registro específico inserindo na tabela de controle (sem DELETE)"""
    try:
        from google.cloud import bigquery
        data = request.get_json()
        id_arquivo = data.get('id_arquivo', '')
        nome_arquivo = data.get('nome_arquivo', '')
        data_processamento = data.get('data_processamento', '')

        if not id_arquivo:
            return jsonify({'error': 'id_arquivo é obrigatório'}), 400

        creds = get_bq_credentials()
        client = bigquery.Client(credentials=creds)

        # Apenas INSERT no controle (sem DELETE na tabela principal!)
        # Isso evita o erro de streaming buffer e não afeta outros registros
        query_insert = f"""
            INSERT INTO `{BQ_TABLE_DISCARDED}` (id_arquivo, data_processamento, nome_arquivo)
            VALUES (@id_arquivo, TIMESTAMP(@data_proc), @nome_arquivo)
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("id_arquivo", "STRING", id_arquivo),
                bigquery.ScalarQueryParameter("data_proc", "STRING", data_processamento),
                bigquery.ScalarQueryParameter("nome_arquivo", "STRING", nome_arquivo),
            ]
        )
        client.query(query_insert, job_config=job_config).result()

        return jsonify({'message': 'Arquivo descartado com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auditor/toggle-ignore', methods=['POST'])
@admin_required
def api_auditor_toggle_ignore():
    """Ignora/reativa obrigação"""
    try:
        from google.cloud import bigquery
        data = request.get_json()
        cnpj = data['cnpj']
        obrigacao = data['obrigacao']

        creds = get_bq_credentials()
        client = bigquery.Client(credentials=creds)

        # Verificar se já está ignorado
        check = f"""
            SELECT COUNT(*) as cnt FROM `{BQ_TABLE_IGNORED}`
            WHERE cnpj = '{cnpj}' AND obrigacao = '{obrigacao}'
        """
        result = client.query(check).to_dataframe()
        is_ignored = result['cnt'].iloc[0] > 0

        if is_ignored:
            query = f"""
                DELETE FROM `{BQ_TABLE_IGNORED}`
                WHERE cnpj = '{cnpj}' AND obrigacao = '{obrigacao}'
            """
            client.query(query).result()
            return jsonify({'message': 'Obrigação reativada!', 'action': 'reactivated'})
        else:
            query = f"""
                INSERT INTO `{BQ_TABLE_IGNORED}` (cnpj, obrigacao)
                VALUES ('{cnpj}', '{obrigacao}')
            """
            client.query(query).result()
            return jsonify({'message': 'Obrigação adormecida!', 'action': 'ignored'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    print("=" * 50)
    print("  HUB TAXBASE - Servidor Flask")
    print(f"  http://localhost:{port}")
    print("=" * 50)
    # Debug deve ser False em produção
    app.run(debug=os.environ.get("FLASK_DEBUG", "False").lower() == "true", host='0.0.0.0', port=port)
