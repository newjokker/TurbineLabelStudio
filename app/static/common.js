const ROLE_TEXT = {
  annotation_view: '查看标注',
  annotation_edit: '编辑标注',
  annotation_export: '导出标注',
  audit_view: '查看审计',
  label_view: '查看标签',
  label_manage: '管理标签',
  dataset_view: '查看数据集',
  dataset_manage: '管理数据集',
  buc_view: '查看 BUC',
  buc_manage: '管理 BUC',
  account_view: '查看账号',
  account_manage: '账号管理'
};

function getUser() {
  const text = localStorage.getItem('tls_user');
  return text ? JSON.parse(text) : null;
}

function setUser(user, permissions, sessionId) {
  localStorage.setItem('tls_user', JSON.stringify(user));
  localStorage.setItem('tls_permissions', JSON.stringify(permissions));
  if (sessionId) localStorage.setItem('tls_session_id', sessionId);
}

function getPermissions() {
  const text = localStorage.getItem('tls_permissions');
  return text ? JSON.parse(text) : {};
}

function hasPermission(permission) {
  return !!getPermissions()[permission];
}

async function refreshPermissions() {
  const data = await apiFetch('/api/permissions');
  setUser(data.user, data.permissions);
  return data.permissions;
}

function logout() {
  localStorage.removeItem('tls_user');
  localStorage.removeItem('tls_permissions');
  localStorage.removeItem('tls_session_id');
  location.href = '/login.html';
}

function requireLogin() {
  const user = getUser();
  if (!user) location.href = '/login.html';
  return user;
}

async function apiFetch(url, options = {}) {
  const user = getUser();
  const sessionId = localStorage.getItem('tls_session_id');
  const headers = options.headers || {};
  if (user) headers['X-User-Id'] = user.id;
  if (sessionId) headers['X-Session-Id'] = sessionId;
  if (options.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';
  const response = await fetch(url, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem('tls_user');
      localStorage.removeItem('tls_permissions');
      localStorage.removeItem('tls_session_id');
    }
    throw new Error(data.detail || '请求失败');
  }
  return data;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[char]));
}

function renderHeader(active, options = {}) {
  const user = getUser();
  const showActions = options.showActions !== false;
  document.getElementById('siteHeader').innerHTML = `
    <div class="topbar">
      <h1>TurbineLabelStudio</h1>
      ${showActions ? `
        <nav class="nav">
          <a href="/index.html" class="home-link ${active === 'index' ? 'active' : ''}">回到首页</a>
          ${user ? `<span class="role-badge">${escapeHtml(user.alias || user.name)} / ${escapeHtml(user.role)}</span><button class="secondary" onclick="logout()">退出</button>` : '<a href="/login.html">登录</a>'}
        </nav>
      ` : ''}
    </div>
  `;
}

function renderPermissionText(target) {
  const permissions = getPermissions();
  const enabled = Object.entries(ROLE_TEXT)
    .filter(([key]) => permissions[key])
    .map(([, text]) => text);
  target.textContent = enabled.length ? `当前权限：${enabled.join('、')}` : '当前权限：只读查看';
}
