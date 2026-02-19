// ==============================================================================
// HUB TAXBASE - APP.JS (SPA Router + Auth + Dashboard)
// ==============================================================================

// --- STATE ---
let currentUser = null;
let allSystems = [];
let allFuncoes = [];

// --- AUTH HELPERS ---
function getToken() {
    return localStorage.getItem('taxbase_token');
}

function setToken(token) {
    localStorage.setItem('taxbase_token', token);
}

function clearToken() {
    localStorage.removeItem('taxbase_token');
    localStorage.removeItem('taxbase_user');
}

async function api(url, options = {}) {
    const token = getToken();
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
        const res = await fetch(url, { ...options, headers });
        const data = await res.json();

        // Exceção: Login pode retornar 401 se credenciais inválidas (não redirecionar)
        if (res.status === 401) {
            if (url.includes('/api/login')) {
                throw new Error(data.error || 'Credenciais inválidas');
            }
            clearToken();
            showLogin();
            return null;
        }

        if (!res.ok) {
            throw new Error(data.error || 'Erro desconhecido');
        }
        return data;
    } catch (err) {
        if (err.message !== 'Failed to fetch') {
            showToast(err.message, 'error');
        }
        throw err;
    }
}

// --- TOAST ---
function showToast(msg, type = 'success') {
    const container = document.getElementById('toast-container');
    const icons = { success: '✅', error: '❌', warning: '⚠️' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${icons[type] || ''}</span> ${msg}`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(30px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// --- ROUTER ---
function showLogin() {
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('app-screen').classList.add('hidden');
    document.getElementById('login-email').focus();
}

function showDashboard() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app-screen').classList.remove('hidden');
    updateNavbar();
    loadSystems();
}

// --- LOGIN ---
async function handleLogin() {
    const email = document.getElementById('login-email').value.trim().toLowerCase();
    const senha = document.getElementById('login-senha').value;
    const errorEl = document.getElementById('login-error');
    const errorText = document.getElementById('login-error-text');
    const btn = document.getElementById('login-btn');

    if (!email || !senha) {
        errorEl.classList.remove('hidden');
        errorText.textContent = 'Preencha e-mail e senha.';
        return;
    }

    btn.disabled = true;
    btn.textContent = '⏳ Entrando...';
    errorEl.classList.add('hidden');

    try {
        const data = await api('/api/login', {
            method: 'POST',
            body: JSON.stringify({ email, senha })
        });

        if (data && data.token) {
            setToken(data.token);
            currentUser = data.usuario;
            localStorage.setItem('taxbase_user', JSON.stringify(currentUser));
            showToast(`Bem-vindo, ${currentUser.nome}!`);
            showDashboard();
        }
    } catch (err) {
        errorEl.classList.remove('hidden');
        errorText.textContent = 'Credenciais inválidas. Tente novamente.';
    } finally {
        btn.disabled = false;
        btn.textContent = '🔐 Entrar';
    }
}

function handleLogout() {
    clearToken();
    currentUser = null;
    allSystems = [];
    showLogin();
    showToast('Sessão encerrada.', 'warning');
}

// --- NAVBAR ---
function updateNavbar() {
    if (!currentUser) return;
    document.getElementById('nav-user-name').textContent = currentUser.nome;
    document.getElementById('nav-user-role').textContent = currentUser.funcao?.nome || '';

    const permissao = currentUser.permissao || 'usuario';
    const badgeEl = document.getElementById('nav-user-badge');
    const isAdmin = permissao === 'admin';
    badgeEl.innerHTML = `<span class="badge ${isAdmin ? 'badge-red' : 'badge-green'}">${isAdmin ? 'ADMIN' : 'USUÁRIO'}</span>`;

    // Show admin button
    const adminBtn = document.getElementById('btn-admin');
    if (isAdmin) adminBtn.style.display = '';

    // Show roles tab only for admin master
    if (currentUser.is_admin_master) {
        document.getElementById('tab-btn-roles').style.display = '';
    }
}

// --- SYSTEMS ---
async function loadSystems() {
    const grid = document.getElementById('systems-grid');
    grid.innerHTML = '<div class="loader"><div class="spinner"></div>Carregando sistemas...</div>';

    try {
        const data = await api('/api/sistemas');
        if (!data) return;

        allSystems = data;
        renderSystems(data);
    } catch (err) {
        grid.innerHTML = '<div class="loader">❌ Erro ao carregar sistemas</div>';
    }
}

function renderSystems(systems) {
    const grid = document.getElementById('systems-grid');
    const empty = document.getElementById('empty-state');

    if (!systems.length) {
        grid.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }

    empty.classList.add('hidden');

    grid.innerHTML = systems.map((sys, i) => {
        const statusClass = sys.status_class || 'offline';
        const statusText = sys.status_texto || 'Offline';
        const categoria = sys.categoria || '';
        const desc = sys.desc || sys.descricao || 'Sistema integrado ao Hub Taxbase';
        const isInternal = sys.is_internal;
        const delay = i * 0.08;

        return `
            <div class="card" style="animation-delay: ${delay}s" data-name="${sys.nome?.toLowerCase() || ''}">
                <div class="card-header">
                    <div>
                        <div class="card-title">${sys.nome || 'Sistema'}</div>
                        ${categoria ? `<span class="tag mt-1">📂 ${categoria}</span>` : ''}
                    </div>
                    <span class="status status-${statusClass}">
                        <span class="status-dot"></span>
                        ${statusText}
                    </span>
                </div>
                <div class="card-desc">${desc}</div>
                <div class="flex justify-between items-center">
                    ${isInternal
                ? `<a href="${sys.url.includes('/sso') ? sys.url + '?token=' + getToken() : sys.url}" class="btn btn-primary btn-sm">🚀 Acessar</a>`
                : `<a href="${sys.url || '#'}" target="_blank" rel="noopener" class="btn btn-primary btn-sm">🔗 Acessar</a>`
            }
                    <small class="text-muted text-xs font-mono">${sys.sistema_id || ''}</small>
                </div>
            </div>
        `;
    }).join('');
}

function filterSystems() {
    const query = document.getElementById('search-input').value.toLowerCase();
    if (!query) {
        renderSystems(allSystems);
        return;
    }
    const filtered = allSystems.filter(s =>
        (s.nome || '').toLowerCase().includes(query) ||
        (s.categoria || '').toLowerCase().includes(query) ||
        (s.desc || '').toLowerCase().includes(query)
    );
    renderSystems(filtered);
}

// ==============================================================================
// ADMIN PANEL
// ==============================================================================

function openAdminModal() {
    document.getElementById('admin-modal').classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    loadAdminData();
}

function closeAdminModal() {
    document.getElementById('admin-modal').classList.add('hidden');
    document.body.style.overflow = '';
}

function switchTab(tabId, btn) {
    // Hide all
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    // Show target
    document.getElementById(tabId).classList.add('active');
    btn.classList.add('active');
}

async function loadAdminData() {
    await Promise.all([loadAdminSystems(), loadAdminUsers(), loadAdminRoles()]);
}

// --- Admin: Systems ---
async function loadAdminSystems() {
    const container = document.getElementById('admin-systems-list');
    try {
        const data = await api('/api/sistemas');
        if (!data) return;
        container.innerHTML = data.map(sys => `
            <div class="expander" id="sys-exp-${sys.sistema_id}">
                <div class="expander-header" onclick="toggleExpander('sys-exp-${sys.sistema_id}')">
                    <span>🖥️ ${sys.nome} <small class="text-muted">(${sys.status_manual || 'Automático'})</small></span>
                    <span class="expander-arrow">▼</span>
                </div>
                <div class="expander-body">
                    <div class="input-group">
                        <label>Status Manual</label>
                        <select class="input" id="edit-status-${sys.sistema_id}">
                            <option ${sys.status_manual === 'Automático' ? 'selected' : ''}>Automático</option>
                            <option ${sys.status_manual === 'Forçar Online' ? 'selected' : ''}>Forçar Online</option>
                            <option ${sys.status_manual === 'Forçar Offline' ? 'selected' : ''}>Forçar Offline</option>
                            <option ${sys.status_manual === 'Manutenção' ? 'selected' : ''}>Manutenção</option>
                        </select>
                    </div>
                    <div class="flex gap-sm">
                        <button class="btn btn-primary btn-sm" onclick="updateSystem('${sys.sistema_id}')">💾 Salvar</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteSystem('${sys.sistema_id}')">🗑️ Excluir</button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (e) { container.innerHTML = '<p class="text-muted">Erro ao carregar</p>'; }
}

async function createSystem() {
    const nome = document.getElementById('sys-nome').value;
    const sistema_id = document.getElementById('sys-id').value;
    const url = document.getElementById('sys-url').value;
    const cat = document.getElementById('sys-cat').value;
    const desc = document.getElementById('sys-desc').value;
    const status = document.getElementById('sys-status').value;

    if (!nome || !sistema_id || !url) { showToast('Nome, ID e URL obrigatórios', 'error'); return; }

    try {
        await api('/api/sistemas', {
            method: 'POST',
            body: JSON.stringify({ nome, sistema_id, url, categoria: cat, desc, status_manual: status })
        });
        showToast('Sistema criado!');
        ['sys-nome', 'sys-id', 'sys-url', 'sys-cat', 'sys-desc'].forEach(id => document.getElementById(id).value = '');
        loadAdminSystems();
        loadSystems();
    } catch (e) { }
}

async function updateSystem(id) {
    const status_manual = document.getElementById(`edit-status-${id}`).value;
    try {
        await api(`/api/sistemas/${id}`, { method: 'PUT', body: JSON.stringify({ status_manual }) });
        showToast('Atualizado!');
        loadAdminSystems();
        loadSystems();
    } catch (e) { }
}

async function deleteSystem(id) {
    if (!confirm(`Excluir sistema ${id}?`)) return;
    try {
        await api(`/api/sistemas/${id}`, { method: 'DELETE' });
        showToast('Excluído!');
        loadAdminSystems();
        loadSystems();
    } catch (e) { }
}

// --- Admin: Users ---
async function loadAdminUsers() {
    const container = document.getElementById('admin-users-list');
    try {
        const [users, funcoes] = await Promise.all([api('/api/usuarios'), api('/api/funcoes')]);
        if (!users) return;
        allFuncoes = funcoes || [];

        // Populate role select
        const sel = document.getElementById('user-funcao');
        sel.innerHTML = allFuncoes.map(f => `<option value="${f.id}">${f.nome}</option>`).join('');

        container.innerHTML = users.map(u => `
            <div class="expander" id="user-exp-${u.email.replace(/[@.]/g, '_')}">
                <div class="expander-header" onclick="toggleExpander('user-exp-${u.email.replace(/[@.]/g, '_')}')">
                    <span>
                        👤 ${u.nome}
                        <span class="badge ${u.permissao === 'admin' ? 'badge-red' : 'badge-green'}" style="margin-left:8px;">${u.funcao_nome}</span>
                    </span>
                    <span class="expander-arrow">▼</span>
                </div>
                <div class="expander-body">
                    <p class="text-sm text-muted mb-1">Email: ${u.email}</p>
                    <div class="input-group">
                        <label>Alterar Função</label>
                        <select class="input" id="edit-func-${u.email.replace(/[@.]/g, '_')}">
                            ${allFuncoes.map(f => `<option value="${f.id}" ${f.id === u.funcao_id ? 'selected' : ''}>${f.nome}</option>`).join('')}
                        </select>
                    </div>
                    <div class="flex gap-sm">
                        <button class="btn btn-primary btn-sm" onclick="updateUser('${u.email}')">💾 Salvar</button>
                        ${!u.is_admin_master ? `<button class="btn btn-danger btn-sm" onclick="deleteUser('${u.email}')">🗑️ Excluir</button>` : '<small class="text-muted">Admin Master</small>'}
                    </div>
                </div>
            </div>
        `).join('');
    } catch (e) { container.innerHTML = '<p class="text-muted">Erro ao carregar</p>'; }
}

async function createUser() {
    const nome = document.getElementById('user-nome').value;
    const email = document.getElementById('user-email').value;
    const funcao_id = document.getElementById('user-funcao').value;
    const senha = document.getElementById('user-senha').value;

    if (!nome || !email || !senha) { showToast('Preencha todos os campos', 'error'); return; }

    try {
        await api('/api/usuarios', { method: 'POST', body: JSON.stringify({ nome, email, funcao_id, senha }) });
        showToast('Usuário criado!');
        ['user-nome', 'user-email', 'user-senha'].forEach(id => document.getElementById(id).value = '');
        loadAdminUsers();
    } catch (e) { }
}

async function updateUser(email) {
    const safeId = email.replace(/[@.]/g, '_');
    const funcao_id = document.getElementById(`edit-func-${safeId}`).value;
    try {
        await api(`/api/usuarios/${email}`, { method: 'PUT', body: JSON.stringify({ funcao_id }) });
        showToast('Atualizado!');
        loadAdminUsers();
    } catch (e) { }
}

async function deleteUser(email) {
    if (!confirm(`Excluir ${email}?`)) return;
    try {
        await api(`/api/usuarios/${email}`, { method: 'DELETE' });
        showToast('Excluído!');
        loadAdminUsers();
    } catch (e) { }
}

// --- Admin: Roles ---
async function loadAdminRoles() {
    const container = document.getElementById('admin-roles-list');
    try {
        const funcoes = await api('/api/funcoes');
        if (!funcoes) return;

        container.innerHTML = funcoes.map(f => `
            <div class="expander" id="role-exp-${f.id}">
                <div class="expander-header" onclick="toggleExpander('role-exp-${f.id}')">
                    <span>
                        🎭 ${f.nome}
                        <span class="badge ${f.permissao === 'admin' ? 'badge-red' : 'badge-green'}" style="margin-left:8px;">${f.permissao.toUpperCase()}</span>
                    </span>
                    <span class="expander-arrow">▼</span>
                </div>
                <div class="expander-body">
                    <p class="text-sm text-muted mb-1">ID: <span class="font-mono">${f.id}</span></p>
                    <p class="text-sm mb-2">${f.descricao || 'Sem descrição'}</p>
                    <div class="input-group">
                        <label>Descrição</label>
                        <input type="text" class="input" id="edit-desc-${f.id}" value="${f.descricao || ''}">
                    </div>
                    <div class="input-group">
                        <label>Permissão</label>
                        <select class="input" id="edit-perm-${f.id}">
                            <option value="usuario" ${f.permissao === 'usuario' ? 'selected' : ''}>Usuário</option>
                            <option value="admin" ${f.permissao === 'admin' ? 'selected' : ''}>Admin</option>
                        </select>
                    </div>
                    <div class="flex gap-sm">
                        <button class="btn btn-primary btn-sm" onclick="updateRole('${f.id}')">💾 Salvar</button>
                        ${f.id !== 'admin_master' ? `<button class="btn btn-danger btn-sm" onclick="deleteRole('${f.id}')">🗑️ Excluir</button>` : '<small class="text-muted">Protegido</small>'}
                    </div>
                </div>
            </div>
        `).join('');
    } catch (e) { container.innerHTML = '<p class="text-muted">Erro ao carregar</p>'; }
}

async function createRole() {
    const id = document.getElementById('role-id').value;
    const nome = document.getElementById('role-nome').value;
    const descricao = document.getElementById('role-desc').value;
    const permissao = document.getElementById('role-perm').value;

    if (!id || !nome) { showToast('ID e Nome obrigatórios', 'error'); return; }

    try {
        await api('/api/funcoes', { method: 'POST', body: JSON.stringify({ id, nome, descricao, permissao, sistemas: ['*'] }) });
        showToast('Função criada!');
        ['role-id', 'role-nome', 'role-desc'].forEach(id => document.getElementById(id).value = '');
        loadAdminRoles();
    } catch (e) { }
}

async function updateRole(id) {
    const descricao = document.getElementById(`edit-desc-${id}`).value;
    const permissao = document.getElementById(`edit-perm-${id}`).value;
    try {
        await api(`/api/funcoes/${id}`, { method: 'PUT', body: JSON.stringify({ descricao, permissao }) });
        showToast('Atualizado!');
        loadAdminRoles();
    } catch (e) { }
}

async function deleteRole(id) {
    if (!confirm(`Excluir função ${id}?`)) return;
    try {
        await api(`/api/funcoes/${id}`, { method: 'DELETE' });
        showToast('Excluído!');
        loadAdminRoles();
    } catch (e) { }
}

// --- Expander Toggle ---
function toggleExpander(id) {
    document.getElementById(id).classList.toggle('open');
}

// --- SESSION CHECK ---
async function checkSession() {
    const token = getToken();
    if (!token) {
        showLogin();
        return;
    }

    try {
        // Validate token and get user data
        const user = await api('/api/me');
        if (user) {
            currentUser = user;
            // Update local storage in case user data changed
            localStorage.setItem('taxbase_user', JSON.stringify(currentUser));
            showDashboard();
            // showToast(`Bem-vindo de volta, ${user.nome.split(' ')[0]}!`, 'success');
        } else {
            throw new Error('Sessão inválida');
        }
    } catch (e) {
        clearToken();
        showLogin();
    }
}

// ==============================================================================
// INIT
// ==============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Enter key for login
    document.getElementById('login-senha').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLogin();
    });
    document.getElementById('login-email').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') document.getElementById('login-senha').focus();
    });

    // Check for existing session instead of always showing login
    checkSession();
});
