// =============================================================================
// TurbineLabelStudio API 文档 — 仅公开数据 & 数据集管理
// =============================================================================

const API_GROUPS = [
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
        pythonExample: `headers = login_headers()
status, data = request_json("POST", "/api/public/datasets",
    payload={"name": "测试数据集", "des": "描述", "extra_info": {}},
    headers=headers)`,
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
        pythonExample: `headers = login_headers()
status, data = request_json("PUT", "/api/public/datasets/1/bucs",
    payload={"bucs": ["BUC_000001", "BUC_000002"]},
    headers=headers)`,
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
        pythonExample: `headers = login_headers()
status, path = download_file(
    f"/api/public/bucs/BUC_000001/image",
    save_name="buc_image.jpg",
    headers=headers,
    query={"func": "wh_jzp_before_20260708"},
)
print(f"图片已保存至: {path}")`,
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
        pythonExample: `headers = login_headers()
status, path = download_file(
    f"/api/public/bucs/BUC_000001/mel",
    save_name="buc_mel.jpg",
    headers=headers,
    query={"func": "wh_jzp_before_20260708"},
)
print(f"Mel 图已保存至: {path}")`,
      },
      {
        method: "GET",
        path: "/api/public/bucs/{buc}/audio/{position_id}",
        summary: "下载单通道音频",
        description: "根据 BUC 和 position_id (B1A/B1B/B2A/B2B/B3A/B3B) 下载单个 WAV 文件。",
        pathParams: { buc: "BUC_000001", position_id: "B1A" },
        isBinary: true,
        auth: true,
        pythonExample: `headers = login_headers()
status, path = download_file(
    f"/api/public/bucs/BUC_000001/audio/B1A",
    save_name="buc_B1A.wav",
    headers=headers,
)
print(f"音频已保存至: {path}")`,
      },
      {
        method: "GET",
        path: "/api/public/bucs/{buc}/audio",
        summary: "下载全部通道音频 ZIP",
        description: "根据 BUC 打包所有 6 个通道的 WAV 文件为 ZIP 并下载。",
        pathParams: { buc: "BUC_000001" },
        isBinary: true,
        auth: true,
        pythonExample: `headers = login_headers()
status, path = download_file(
    f"/api/public/bucs/BUC_000001/audio",
    save_name="buc_audio_all.zip",
    headers=headers,
)
print(f"ZIP 已保存至: {path}")`,
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
        pythonExample: `headers = login_headers()
status, data = request_json("GET", f"/api/public/bucs/BUC_000001/annotations",
    headers=headers,
    query={"func": "wh_jzp_before_20260708"},
)
print(f"标注数量: {data['annotation_count']}")
for ann in data['annotations']:
    print(f"  - {ann['label']}: ({ann['x1']:.2f}, {ann['y1']:.2f}) -> ({ann['x2']:.2f}, {ann['y2']:.2f})")`,
      },
    ],
  },
  {
    id: "datasets",
    title: "📊 数据集管理 (Datasets)",
    apis: [
      {
        method: "GET",
        path: "/api/datasets",
        summary: "获取数据集列表",
        description: "返回全部数据集和所有 BUC 列表。",
        response: { items: [{ id: 1, name: "数据集1", des: "描述", bucs: ["BUC_000001"], extra_info: {} }], all_bucs: ["BUC_000001"] },
        auth: true,
        pythonExample: `headers = login_headers()
status, data = request_json("GET", "/api/datasets", headers=headers)
for ds in data["items"]:
    print(f"数据集: {ds['name']}  BUC 数: {len(ds['bucs'])}")`,
      },
      {
        method: "POST",
        path: "/api/datasets",
        summary: "创建数据集",
        description: "需要 account_manage 权限。可同时关联 BUC 列表。",
        body: { name: "新数据集", des: "描述", bucs: ["BUC_000001"] },
        response: { item: { id: 2, name: "新数据集", des: "描述", bucs: ["BUC_000001"] } },
        auth: true,
        pythonExample: `headers = login_headers()
status, data = request_json("POST", "/api/datasets",
    payload={"name": "新数据集", "des": "描述", "bucs": ["BUC_000001"]},
    headers=headers)`,
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
        pythonExample: `headers = login_headers()
status, data = request_json("PUT", "/api/datasets/1",
    payload={"name": "改名", "des": "新描述", "bucs": ["BUC_000001"]},
    headers=headers)`,
      },
      {
        method: "DELETE",
        path: "/api/datasets/{dataset_id}",
        summary: "删除数据集",
        description: "需要 account_manage 权限。",
        pathParams: { dataset_id: "1" },
        response: { ok: true },
        auth: true,
        pythonExample: `headers = login_headers()
status, data = request_json("DELETE", "/api/datasets/1", headers=headers)`,
      },
    ],
  },
];

// Python util 代码片段（展示在页面顶部）
const PYTHON_UTIL_CODE = `#!/usr/bin/env python3
"""TurbineLabelStudio Public API 调用工具"""

import json, os
from pathlib import Path
from urllib import error, parse, request

BASE_URL = os.environ.get("TLS_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
USERNAME = os.environ.get("TLS_USERNAME", "txkj")
PASSWORD = os.environ.get("TLS_PASSWORD", "txkj")
OUTPUT_DIR = Path(os.environ.get("TLS_OUTPUT_DIR", "output"))


def api_url(path, query=None):
    url = BASE_URL + path
    if query:
        url += "?" + parse.urlencode(query)
    return url


def request_json(method, path, payload=None, headers=None, query=None):
    body = None
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = request.Request(api_url(path, query), data=body, headers=req_headers, method=method)
    try:
        with request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, json.loads(text) if text else {}
    except error.HTTPError as exc:
        text = exc.read().decode("utf-8")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"raw": text}
        return exc.code, data


def download_file(path, save_name, headers=None, query=None):
    req_headers = {}
    if headers:
        req_headers.update(headers)
    req = request.Request(api_url(path, query), headers=req_headers, method="GET")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_path = OUTPUT_DIR / save_name
    try:
        with request.urlopen(req, timeout=300) as resp:
            save_path.write_bytes(resp.read())
            return resp.status, save_path
    except error.HTTPError as exc:
        text = exc.read().decode("utf-8")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"raw": text}
        return exc.code, data


def login_headers():
    status, data = request_json("POST", "/api/login",
        payload={"name": USERNAME, "password": PASSWORD})
    if status != 200:
        raise RuntimeError(f"登录失败 status={status} data={data}")
    return {
        "X-User-Id": str(data["user"]["id"]),
        "X-Session-Id": data["session_id"],
    }`;

// =============================================================================
// 渲染
// =============================================================================

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

  // TOC — 使用 click 事件避免浏览器锚点滚动导致侧栏位移
  toc.innerHTML = filteredGroups.map(g =>
    `<div class="toc-group">
      <a class="toc-group-link" data-target="api-group-${g.id}">${g.title}</a>
      ${g.apis.map(a => `<a class="toc-item" data-target="api-${slug(a)}"><span class="method-tag method-${a.method.toLowerCase()}">${a.method}</span>${a.summary}</a>`).join("")}
    </div>`
  ).join("");

  // 绑定 TOC 点击事件——在右侧面板内滚动，左侧导航固定不动
  const scrollContainer = detail;  // api-detail 是独立滚动容器
  toc.querySelectorAll('[data-target]').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      const target = document.getElementById(el.dataset.target);
      if (target && scrollContainer) {
        const targetRect = target.getBoundingClientRect();
        const containerRect = scrollContainer.getBoundingClientRect();
        const offset = targetRect.top - containerRect.top - 8;
        scrollContainer.scrollBy({ top: offset, behavior: 'smooth' });
      }
    });
  });

  // Detail
  detail.innerHTML = `
    <div class="api-util-section">
      <h2>🐍 Python 工具模块</h2>
      <p class="muted">以下代码可直接复制保存为 <code>tls_client.py</code>，所有 API 调用示例均基于此模块。</p>
      <pre class="api-code python-code">${escapeHtml(PYTHON_UTIL_CODE)}</pre>
    </div>
    ${filteredGroups.map(g => `
    <div class="api-group" id="api-group-${g.id}">
      <h2 class="api-group-title">${g.title}</h2>
      ${g.description ? `<p class="muted" style="margin:0 0 12px">${g.description}</p>` : ""}
      ${g.apis.map(a => renderApiCard(a)).join("")}
    </div>
  `).join("")}`;

  // Syntax highlight for Python code blocks
  document.querySelectorAll(".python-code").forEach(el => {
    el.style.whiteSpace = "pre-wrap";
    el.style.wordBreak = "break-word";
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

  return `
    <div class="api-card" id="api-${slug(api)}">
      <div class="api-card-head">
        <span class="method-tag method-${api.method.toLowerCase()}">${api.method}</span>
        <code class="api-path">${fullPath}${queryStr}</code>
        ${api.auth !== false ? '<span class="auth-badge">🔒 需登录</span>' : '<span class="auth-badge public-badge">🔓 公开</span>'}
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

        ${api.pythonExample ? `
        <div class="api-section python-example">
          <strong class="api-section-title">🐍 Python 调用示例</strong>
          <pre class="api-code python-code">${escapeHtml(api.pythonExample)}</pre>
        </div>` : ""}
      </div>
    </div>
  `;
}

function filterApis() {
  renderApiDocs();
}

