const ROLE_TEXT = {
  label_write: '标签编辑',
  label_export: '标签导出',
  account_manage: '账号管理'
};

function getUser() {
  const text = localStorage.getItem('tls_user');
  return text ? JSON.parse(text) : null;
}

function setUser(user, permissions) {
  localStorage.setItem('tls_user', JSON.stringify(user));
  localStorage.setItem('tls_permissions', JSON.stringify(permissions));
}

function getPermissions() {
  const text = localStorage.getItem('tls_permissions');
  return text ? JSON.parse(text) : {};
}

function logout() {
  localStorage.removeItem('tls_user');
  localStorage.removeItem('tls_permissions');
  location.href = '/login.html';
}

function requireLogin() {
  const user = getUser();
  if (!user) location.href = '/login.html';
  return user;
}

async function apiFetch(url, options = {}) {
  const user = getUser();
  const headers = options.headers || {};
  if (user) headers['X-User-Id'] = user.id;
  if (options.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';
  const response = await fetch(url, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || '请求失败');
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

function renderHeader(active) {
  const user = getUser();
  document.getElementById('siteHeader').innerHTML = `
    <div class="topbar">
      <h1>TurbineLabelStudio</h1>
      <nav class="nav">
        <a href="/index.html" class="${active === 'index' ? 'active' : ''}">首页</a>
        <a href="/labels.html" class="${active === 'labels' ? 'active' : ''}">标签管理</a>
        <a href="/accounts.html" class="${active === 'accounts' ? 'active' : ''}">账号管理</a>
        ${user ? `<span class="role-badge">${escapeHtml(user.alias || user.name)} / ${escapeHtml(user.role)}</span><button class="secondary" onclick="logout()">退出</button>` : '<a href="/login.html">登录</a>'}
      </nav>
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
