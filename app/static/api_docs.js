// =============================================================================
// TurbineLabelStudio API 文档 & 内联测试
// =============================================================================

const API_GROUPS = [
  {
    id: "auth",
    title: "🔐 认证 (Auth)",
    apis: [
      {
        method: "POST",
        path: "/api/login",
        summary: "用户登录",
        description: "使用 name 和 password 登录系统，返回用户信息、session_id 和权限。",
        body: { name: "txkj", password: "txkj" },
        response: { user: { id: 1, name: "txkj", alias: null, end_time: null, role: "管理员" }, session_id: "...", permissions: { label_write: true, label_export: true, account_manage: true }, server_time: "2026-07-10 12:00:00" },
        auth: false,
      },
      {
        method: "GET",
        path: "/api/permissions",
        summary: "获取当前用户权限",
        description: "通过 Header X-User-Id 和 X-Session-Id 获取当前会话的用户信息和权限。",
        response: { user: { id: 1, name: "txkj", alias: null, end_time: null, role: "管理员" }, permissions: { label_write: true, label_export: true, account_manage: true }, server_time: "2026-07-10 12:00:00" },
        auth: true,
      },
    ],
  },
  {
    id: "labels",
    title: "🏷️ 标签管理 (Labels)",
    apis: [
      {
        method: "GET",
        path: "/api/labels",
        summary: "获取标签列表",
        description: "返回全部标签，按 id 排序。",
        response: { items: [{ id: 1, label: "裂纹", des: "叶片表面裂纹", update_by: "txkj", update_time: "2026-07-10 12:00:00", extra_info: { color: "#e74c3c" } }] },
        auth: true,
      },
      {
        method: "POST",
        path: "/api/labels",
        summary: "新建标签",
        description: "需要 label_write 权限。label 唯一，重复会返回 400。",
        body: { label: "新标签", des: "描述", extra_info: { color: "#3498db" } },
        response: { item: { id: 2, label: "新标签", des: "描述", extra_info: { color: "#3498db" } } },
        auth: true,
      },
      {
        method: "PUT",
        path: "/api/labels/{label_id}",
        summary: "更新标签",
        description: "需要 label_write 权限。根据 label_id 更新标签信息。",
        pathParams: { label_id: "1" },
        body: { label: "裂纹修改", des: "更新后的描述" },
        response: { item: { id: 1, label: "裂纹修改", des: "更新后的描述" } },
        auth: true,
      },
      {
        method: "DELETE",
        path: "/api/labels/{label_id}",
        summary: "删除标签",
        description: "需要 label_write 权限。已被标注引用的标签无法删除(400)。",
        pathParams: { label_id: "1" },
        response: { ok: true },
        auth: true,
      },
    ],
  },
  {
    id: "annotations",
    title: "✏️ 标注管理 (Annotations)",
    apis: [
      {
        method: "GET",
        path: "/api/annotation-view/options",
        summary: "获取标注视图选项",
        description: "返回所有 BUC 标注统计、标签、关联数据集等。",
        query: {},
        response: { datasets: [], items: [{ buc: "BUC_000001", func: "wh_jzp_before_20260708", annotation_count: 3, labels: [], datasets: [] }] },
        auth: true,
      },
      {
        method: "GET",
        path: "/api/annotation-view/data",
        summary: "获取标注数据",
        description: "根据 BUC 和 func 获取标注详情、图片 URL 和 6 个通道音频 URL。",
        query: { buc: "BUC_000001", func: "wh_jzp_before_20260708" },
        response: { buc: "BUC_000001", func: "wh_jzp_before_20260708", image_url: "/api/annotation-view/image?...", annotations: [], channels: [] },
        auth: true,
      },
      {
        method: "GET",
        path: "/api/annotation-view/image",
        summary: "获取标注图片",
        description: "根据 BUC + func 返回生成的标注图片（JPEG）。",
        query: { buc: "BUC_000001", func: "wh_jzp_before_20260708" },
        isBinary: true,
        auth: false,
      },
      {
        method: "GET",
        path: "/api/annotation-view/wav/{md5}",
        summary: "获取音频文件",
        description: "根据 md5 返回 WAV 音频文件。",
        pathParams: { md5: "abc123..." },
        isBinary: true,
        auth: false,
      },
      {
        method: "POST",
        path: "/api/annotations",
        summary: "创建标注框",
        description: "需要 label_write 权限并且该图片已被当前用户锁定。",
        body: { buc: "BUC_000001", func: "wh_jzp_before_20260708", x1: 0.1, y1: 0.1, x2: 0.5, y2: 0.5, label_id: 1, difficult: false, update_reason: "新增标注" },
        response: { item: { id: 1, buc: "BUC_000001", func: "wh_jzp_before_20260708", x1: 0.1, y1: 0.1, x2: 0.5, y2: 0.5, label_id: 1 } },
        auth: true,
      },
      {
        method: "DELETE",
        path: "/api/annotations/{annotation_id}",
        summary: "删除标注框",
        description: "需要 label_write 权限并且图片已被锁定。",
        pathParams: { annotation_id: "1" },
        response: { ok: true },
        auth: true,
      },
      {
        method: "POST",
        path: "/api/annotation-lock/lock",
        summary: "锁定标注图片",
        description: "需要 label_write 权限。编辑标注前先锁定图片，防止多人同时编辑。锁定时长 5 分钟。",
        body: { buc: "BUC_000001", func: "wh_jzp_before_20260708" },
        response: { item: { buc: "BUC_000001", func: "wh_jzp_before_20260708", locked_by: 1, locked_at: "2026-07-10 12:00:00" }, expires_in: 300 },
        auth: true,
      },
      {
        method: "POST",
        path: "/api/annotation-lock/heartbeat",
        summary: "标注锁心跳",
        description: "续期标注锁定，过期前调用此接口重置 5 分钟 TTL。",
        body: { buc: "BUC_000001", func: "wh_jzp_before_20260708" },
        response: { item: { buc: "BUC_000001", func: "wh_jzp_before_20260708", locked_by: 1, locked_at: "2026-07-10 12:05:00" }, expires_in: 300 },
        auth: true,
      },
      {
        method: "POST",
        path: "/api/annotation-lock/unlock",
        summary: "解锁标注图片",
        description: "释放当前用户持有的锁。",
        body: { buc: "BUC_000001", func: "wh_jzp_before_20260708" },
        response: { ok: true },
        auth: true,
      },
    ],
  },
  {
    id: "public",
    title: "📦 公开数据 API (Public)",
    description: "以下 API 均需要登录鉴权（通过 Header），用于外部系统集成获取 BUC 音频、图片和标注数据。",
    apis: [
      {
        method: "POST",
        path: "/api/public/datasets",
        summary: "创建数据集 (Public)",
        description: "需要 account_manage 权限。",
        body: { name: "测试数据集", des: "描述", extra_info: {} },
        response: { item: { id: 1, name: "测试数据集", des: "描述", bucs: [], extra_info: {} } },
        auth: true,
      },
      {
        method: "PUT",
        path: "/api/public/datasets/{dataset_id}/bucs",
        summary: "更新数据集 BUC 列表",
        description: "需要 account_manage 权限。替换数据集关联的 BUC 列表，BUC 必须存在于 wav_buc 表。",
        pathParams: { dataset_id: "1" },
        body: { bucs: ["BUC_000001", "BUC_000002"] },
        response: { item: { id: 1, name: "测试数据集", des: "描述", bucs: ["BUC_000001", "BUC_000002"] } },
        auth: true,
      },
      {
        method: "GET",
        path: "/api/public/bucs/{buc}/image",
        summary: "下载 BUC 图片",
        description: "根据 BUC 和 func 参数下载标注图片（JPEG）。默认 func 为 wh_jzp_before_20260708。",
        pathParams: { buc: "BUC_000001" },
        query: { func: "wh_jzp_before_20260708" },
        isBinary: true,
        auth: true,
      },
      {
        method: "GET",
        path: "/api/public/bucs/{buc}/mel",
        summary: "下载 BUC Mel 图",
        description: "根据 BUC 和 func 参数下载 Mel 频谱图（JPEG）。",
        pathParams: { buc: "BUC_000001" },
        query: { func: "wh_jzp_before_20260708" },
        isBinary: true,
        auth: true,
      },
      {
        method: "GET",
        path: "/api/public/bucs/{buc}/audio/{position_id}",
        summary: "下载单通道音频",
        description: "根据 BUC 和 position_id (B1A/B1B/B2A/B2B/B3A/B3B) 下载单个 WAV 文件。",
        pathParams: { buc: "BUC_000001", position_id: "B1A" },
        isBinary: true,
        auth: true,
      },
      {
        method: "GET",
        path: "/api/public/bucs/{buc}/audio",
        summary: "下载全部通道音频 ZIP",
        description: "根据 BUC 打包所有 6 个通道的 WAV 文件为 ZIP 并下载。",
        pathParams: { buc: "BUC_000001" },
        isBinary: true,
        auth: true,
      },
      {
        method: "GET",
        path: "/api/public/bucs/{buc}/annotations",
        summary: "获取 BUC 标注数据",
        description: "根据 BUC 和 func 参数返回标注框列表、标签名和 BUC 音频元数据。",
        pathParams: { buc: "BUC_000001" },
        query: { func: "wh_jzp_before_20260708" },
        response: { buc: "BUC_000001", func: "wh_jzp_before_20260708", buc_audio: [], annotation_count: 3, annotations: [{ id: 1, buc: "BUC_000001", x1: 0.1, y1: 0.1, x2: 0.5, y2: 0.5, label_id: 1, label: "裂纹", label_des: "叶片表面裂纹" }] },
        auth: true,
      },
    ],
  },
  {
    id: "datasets",
    title: "📊 数据集管理 (Datasets Internal)",
    apis: [
      {
        method: "GET",
        path: "/api/datasets",
        summary: "获取数据集列表",
        description: "返回全部数据集和所有 BUC 列表。",
        response: { items: [{ id: 1, name: "数据集1", des: "描述", bucs: ["BUC_000001"], extra_info: {} }], all_bucs: ["BUC_000001"] },
        auth: true,
      },
      {
        method: "POST",
        path: "/api/datasets",
        summary: "创建数据集",
        description: "需要 account_manage 权限。可同时关联 BUC 列表。",
        body: { name: "新数据集", des: "描述", bucs: ["BUC_000001"] },
        response: { item: { id: 2, name: "新数据集", des: "描述", bucs: ["BUC_000001"] } },
        auth: true,
      },
      {
        method: "PUT",
        path: "/api/datasets/{dataset_id}",
        summary: "更新数据集",
        description: "需要 account_manage 权限。",
        pathParams: { dataset_id: "1" },
        body: { name: "改名", des: "新描述", bucs: ["BUC_000001"] },
        response: { item: { id: 1, name: "改名", des: "新描述", bucs: ["BUC_000001"] } },
        auth: true,
      },
      {
        method: "DELETE",
        path: "/api/datasets/{dataset_id}",
        summary: "删除数据集",
        description: "需要 account_manage 权限。",
        pathParams: { dataset_id: "1" },
        response: { ok: true },
        auth: true,
      },
    ],
  },
  {
    id: "accounts",
    title: "👤 账号管理 (Accounts)",
    apis: [
      {
        method: "GET",
        path: "/api/accounts",
        summary: "获取账号列表",
        description: "返回所有用户账号信息。",
        response: { items: [{ id: 1, name: "txkj", alias: "管理员", end_time: null, role: "管理员" }] },
        auth: true,
      },
      {
        method: "POST",
        path: "/api/accounts",
        summary: "创建账号",
        description: "需要 account_manage 权限。role 可选：观察者/编辑者/管理员。",
        body: { name: "newuser", password: "123456", alias: "新用户", role: "编辑者" },
        response: { item: { id: 2, name: "newuser", alias: "新用户", end_time: null, role: "编辑者" } },
        auth: true,
      },
      {
        method: "PUT",
        path: "/api/accounts/{account_id}",
        summary: "更新账号",
        description: "需要 account_manage 权限。",
        pathParams: { account_id: "2" },
        body: { name: "newuser", password: "newpass", alias: "改名", role: "观察者" },
        response: { item: { id: 2, name: "newuser", alias: "改名", end_time: null, role: "观察者" } },
        auth: true,
      },
      {
        method: "POST",
        path: "/api/accounts/{account_id}/disable",
        summary: "停用账号",
        description: "需要 account_manage 权限。设置账号 end_time 为当前时间。",
        pathParams: { account_id: "2" },
        response: { item: { id: 2, name: "newuser", alias: "改名", end_time: "2026-07-10 12:00:00", role: "观察者" } },
        auth: true,
      },
    ],
  },
];

// =============================================================================
// 渲染
// =============================================================================

let currentTryApi = null;

function renderApiDocs() {
  const toc = document.getElementById("apiToc");
  const detail = document.getElementById("apiDetail");
  const searchTerm = (document.getElementById("apiSearch")?.value || "").toLowerCase().trim();

  let filteredGroups = API_GROUPS.map(g => {
    const filtered = g.apis.filter(a =>
      a.summary.toLowerCase().includes(searchTerm) ||
      a.path.toLowerCase().includes(searchTerm) ||
      a.description.toLowerCase().includes(searchTerm) ||
      (g.title || "").toLowerCase().includes(searchTerm)
    );
    return { ...g, apis: filtered };
  }).filter(g => g.apis.length > 0);

  // TOC
  toc.innerHTML = filteredGroups.map(g =>
    `<div class="toc-group">
      <a class="toc-group-link" href="#api-group-${g.id}">${g.title}</a>
      ${g.apis.map(a => `<a class="toc-item" href="#api-${slug(a)}"><span class="method-tag method-${a.method.toLowerCase()}">${a.method}</span>${a.summary}</a>`).join("")}
    </div>`
  ).join("");

  // Detail
  detail.innerHTML = filteredGroups.map(g => `
    <div class="api-group" id="api-group-${g.id}">
      <h2 class="api-group-title">${g.title}</h2>
      ${g.description ? `<p class="muted" style="margin:0 0 12px">${g.description}</p>` : ""}
      ${g.apis.map(a => renderApiCard(a)).join("")}
    </div>
  `).join("");

  // Re-attach try buttons
  document.querySelectorAll(".try-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const groupId = btn.dataset.group;
      const apiIndex = parseInt(btn.dataset.index);
      const group = API_GROUPS.find(g => g.id === groupId);
      if (group && group.apis[apiIndex]) {
        openTry(group.apis[apiIndex]);
      }
    });
  });
}

function slug(api) {
  return (api.method + "-" + api.path).replace(/[{}]/g, "").replace(/[^a-zA-Z0-9-]/g, "-").toLowerCase();
}

function renderApiCard(api) {
  let fullPath = api.path;
  if (api.pathParams) {
    for (const [k, v] of Object.entries(api.pathParams)) {
      fullPath = fullPath.replace(`{${k}}`, `<b class="path-param">${escapeHtml(v)}</b>`);
    }
  }

  let queryStr = "";
  if (api.query && Object.keys(api.query).length) {
    queryStr = "?" + Object.entries(api.query).map(([k, v]) => `${k}=<b class="path-param">${escapeHtml(String(v))}</b>`).join("&");
  }

  const groupId = api._groupId || "";
  const apiIndex = api._index ?? -1;

  return `
    <div class="api-card" id="api-${slug(api)}">
      <div class="api-card-head">
        <span class="method-tag method-${api.method.toLowerCase()}">${api.method}</span>
        <code class="api-path">${fullPath}${queryStr}</code>
        ${api.auth !== false ? '<span class="auth-badge">🔒 需登录</span>' : '<span class="auth-badge public-badge">🔓 公开</span>'}
        <button class="try-btn secondary" data-group="${escapeHtml(groupId)}" data-index="${apiIndex}">▶ Try</button>
      </div>
      <div class="api-card-body">
        <p class="muted" style="margin:0 0 12px;">${api.description}</p>

        ${api.pathParams ? `
        <div class="api-section">
          <strong class="api-section-title">路径参数</strong>
          <table class="api-param-table">
            <thead><tr><th>参数</th><th>示例值</th></tr></thead>
            <tbody>${Object.entries(api.pathParams).map(([k, v]) => `<tr><td><code>${k}</code></td><td><code>${escapeHtml(String(v))}</code></td></tr>`).join("")}</tbody>
          </table>
        </div>` : ""}

        ${api.query ? `
        <div class="api-section">
          <strong class="api-section-title">Query 参数</strong>
          <table class="api-param-table">
            <thead><tr><th>参数</th><th>示例值</th></tr></thead>
            <tbody>${Object.entries(api.query).map(([k, v]) => `<tr><td><code>${k}</code></td><td><code>${escapeHtml(String(v))}</code></td></tr>`).join("")}</tbody>
          </table>
        </div>` : ""}

        ${api.body ? `
        <div class="api-section">
          <strong class="api-section-title">Request Body (JSON)</strong>
          <pre class="api-code">${JSON.stringify(api.body, null, 2)}</pre>
        </div>` : ""}

        ${api.response ? `
        <div class="api-section">
          <strong class="api-section-title">Response (JSON)</strong>
          <pre class="api-code">${JSON.stringify(api.response, null, 2)}</pre>
        </div>` : ""}

        ${api.isBinary ? `
        <div class="api-section">
          <strong class="api-section-title">Response</strong>
          <p class="muted" style="margin:0;">二进制文件流（JPEG / WAV / ZIP）</p>
        </div>` : ""}
      </div>
    </div>
  `;
}

function filterApis() {
  renderApiDocs();
}

// =============================================================================
// 内联 Try It 功能
// =============================================================================

function openTry(api) {
  currentTryApi = api;
  const panel = document.getElementById("tryPanel");
  const title = document.getElementById("tryTitle");
  const pathEl = document.getElementById("tryPath");

  panel.style.display = "";
  title.textContent = `${api.method} ${api.summary}`;
  pathEl.textContent = api.path;

  let paramHtml = "";

  // path params
  if (api.pathParams) {
    for (const [k, v] of Object.entries(api.pathParams)) {
      paramHtml += `<label>路径参数 <code>${k}</code><input type="text" id="trypp-${k}" value="${escapeHtml(String(v))}"></label>`;
    }
  }

  // query params
  if (api.query && Object.keys(api.query).length) {
    for (const [k, v] of Object.entries(api.query)) {
      paramHtml += `<label>Query <code>${k}</code><input type="text" id="tryqp-${k}" value="${escapeHtml(String(v))}"></label>`;
    }
  }

  // body
  if (api.body) {
    paramHtml += `<label>Request Body (JSON)<textarea id="tryBody" rows="6">${JSON.stringify(api.body, null, 2)}</textarea></label>`;
  }

  document.getElementById("tryParams").innerHTML = paramHtml || '<p class="muted">该接口无需额外参数。</p>';
  document.getElementById("tryStatus").textContent = "";
  document.getElementById("tryResponse").style.display = "none";

  panel.scrollIntoView({ behavior: "smooth", block: "center" });
}

function closeTry() {
  document.getElementById("tryPanel").style.display = "none";
  currentTryApi = null;
}

async function sendTry() {
  const api = currentTryApi;
  if (!api) return;

  const statusEl = document.getElementById("tryStatus");
  const respEl = document.getElementById("tryResponse");
  const btn = document.getElementById("trySendBtn");
  statusEl.textContent = "请求中...";
  statusEl.className = "status";
  respEl.style.display = "none";
  btn.disabled = true;

  try {
    // Build path by replacing pathParams
    let path = api.path;
    if (api.pathParams) {
      for (const k of Object.keys(api.pathParams)) {
        const el = document.getElementById("trypp-" + k);
        path = path.replace(`{${k}}`, el ? el.value : "");
      }
    }

    // Build query string
    const queryParts = [];
    if (api.query) {
      for (const k of Object.keys(api.query)) {
        const el = document.getElementById("tryqp-" + k);
        if (el && el.value) {
          queryParts.push(`${encodeURIComponent(k)}=${encodeURIComponent(el.value)}`);
        }
      }
    }
    const queryStr = queryParts.length ? "?" + queryParts.join("&") : "";

    // Headers
    const user = getUser();
    const sessionId = localStorage.getItem("tls_session_id");
    const headers = {};
    if (user && sessionId) {
      headers["X-User-Id"] = String(user.id);
      headers["X-Session-Id"] = sessionId;
    }
    headers["Accept"] = "application/json";

    // Body
    let body = null;
    if (api.body) {
      const bodyEl = document.getElementById("tryBody");
      if (bodyEl) {
        try {
          JSON.parse(bodyEl.value); // validate
          body = bodyEl.value;
          headers["Content-Type"] = "application/json";
        } catch (e) {
          statusEl.textContent = "JSON 格式错误";
          statusEl.className = "status bad";
          btn.disabled = false;
          return;
        }
      }
    }

    // For binary endpoints, don't try to parse JSON
    const fetchOpts = { method: api.method, headers };
    if (body) fetchOpts.body = body;

    const resp = await fetch(path + queryStr, fetchOpts);
    const contentType = resp.headers.get("content-type") || "";

    let result;
    if (contentType.includes("application/json")) {
      result = await resp.json();
    } else {
      const blob = await resp.blob();
      result = {
        status: resp.status,
        contentType: contentType,
        size: blob.size,
        note: "二进制响应，此处仅显示元数据。",
      };
    }

    statusEl.textContent = resp.ok ? `✓ ${resp.status}` : `✗ ${resp.status}`;
    statusEl.className = resp.ok ? "status ok" : "status bad";
    respEl.textContent = JSON.stringify(result, null, 2);
    respEl.style.display = "";
  } catch (err) {
    statusEl.textContent = "网络错误";
    statusEl.className = "status bad";
    respEl.textContent = String(err);
    respEl.style.display = "";
  } finally {
    btn.disabled = false;
  }
}

// =============================================================================
// 初始化：给每个 API 标记 groupId 和 index，方便 try 按钮定位
// =============================================================================
(function initApiMeta() {
  API_GROUPS.forEach(group => {
    group.apis.forEach((api, idx) => {
      api._groupId = group.id;
      api._index = idx;
    });
  });
})();