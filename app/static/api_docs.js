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
        method: "POST",
        path: "/api/public/bucs",
        summary: "插入 WAV 映射并生成 BUC",
        description: "需要 account_manage 权限。传入 6 个 WAV MD5 与标准点位，系统自动生成一个新的 BUC。",
        body: {
          wave_position_id: {
            aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa: "B1A",
            bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb: "B1B",
            cccccccccccccccccccccccccccccccc: "B2A",
            dddddddddddddddddddddddddddddddd: "B2B",
            eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee: "B3A",
            ffffffffffffffffffffffffffffffff: "B3B",
          },
        },
        response: { buc: "BUC_000123", items: [{ wave_md5: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", position_id: "B1A", buc: "BUC_000123" }] },
        auth: true,
        pythonExample: `headers = login_headers()
status, data = request_json("POST", "/api/public/bucs",
    payload={
        "wave_position_id": {
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": "B1A",
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb": "B1B",
            "cccccccccccccccccccccccccccccccc": "B2A",
            "dddddddddddddddddddddddddddddddd": "B2B",
            "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee": "B3A",
            "ffffffffffffffffffffffffffffffff": "B3B",
        }
    },
    headers=headers,
)
print(f"新 BUC: {data['buc']}")`,
      },
      {
        method: "GET",
        path: "/api/public/wav-md5/{md5}/buc",
        summary: "查询 MD5 是否已关联 BUC",
        description: "根据单个 WAV MD5 查询是否已经存在于 wav_buc 表，并返回关联 BUC。",
        pathParams: { md5: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" },
        response: { wave_md5: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", exists: true, buc: "BUC_000001", item: { wave_md5: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", position_id: "B1A", buc: "BUC_000001" } },
        auth: true,
        pythonExample: `headers = login_headers()
status, data = request_json("GET",
    "/api/public/wav-md5/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/buc",
    headers=headers,
)
print(data["exists"], data["buc"])`,
      },
      {
        method: "GET",
        path: "/api/public/bucs/{buc}/wav-md5s",
        summary: "查询 BUC 关联的 MD5 列表",
        description: "根据 BUC 返回该 BUC 下所有 position_id 与 wave_md5 映射，按 B1A/B1B/B2A/B2B/B3A/B3B 排序。",
        pathParams: { buc: "BUC_000001" },
        response: { buc: "BUC_000001", count: 6, items: [{ wave_md5: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", position_id: "B1A", buc: "BUC_000001" }] },
        auth: true,
        pythonExample: `headers = login_headers()
status, data = request_json("GET",
    "/api/public/bucs/BUC_000001/wav-md5s",
    headers=headers,
)
for item in data["items"]:
    print(item["position_id"], item["wave_md5"])`,
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
      {
        method: "GET",
        path: "/api/public/bucs/{buc}/annotations/xml",
        summary: "下载 BUC 标注 XML",
        description: "根据 BUC 和 func 参数下载 Pascal VOC / LabelImg 兼容的 XML 标注文件。未传 func 时使用默认 func。",
        pathParams: { buc: "BUC_000001" },
        query: { func: "wh_jzp_before_20260708" },
        isBinary: true,
        auth: true,
        pythonExample: `headers = login_headers()
status, path = download_file(
    f"/api/public/bucs/BUC_000001/annotations/xml",
    save_name="BUC_000001_wh_jzp_before_20260708.xml",
    headers=headers,
    query={"func": "wh_jzp_before_20260708"},
)
print(f"XML 已保存至: {path}")`,
      },
    ],
  },
  {
    id: "annotation-changes",
    title: "🧾 标注框变动 (Annotation Changes)",
    description: "查询标注框审计记录，仅包含 annotation 表的新增、修改和删除，不包含图片锁和评论日志。",
    apis: [
      {
        method: "GET",
        path: "/api/annotation-changes",
        summary: "获取标注框变动记录",
        description: "可使用 user_id、label_id、buc 任意组合筛选；同时返回页面下拉框需要的人员、标签和 BUC 选项。",
        query: { user_id: "4", label_id: "23", buc: "BUC_000001" },
        response: {
          filters: { users: [], labels: [], bucs: ["BUC_000001"] },
          count: 1,
          items: [{ id: 552, act: "create", update_time: "2026-07-13 09:16:44", annotation_id: 15722, buc: "BUC_000020", label_id: 23, label: "标签名称", box: { x1: 822, y1: 812, x2: 1119, y2: 1018 } }],
        },
        auth: true,
        pythonExample: `headers = login_headers()
status, data = request_json("GET", "/api/annotation-changes",
    headers=headers,
    query={"user_id": 4, "label_id": 23, "buc": "BUC_000001"},
)
print(f"符合条件的变动数: {data['count']}")`,
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
  const stats = document.getElementById("apiStats");
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

  const visibleApiCount = filteredGroups.reduce((sum, g) => sum + g.apis.length, 0);
  const methodCounts = filteredGroups.flatMap(g => g.apis).reduce((acc, api) => {
    acc[api.method] = (acc[api.method] || 0) + 1;
    return acc;
  }, {});

  if (stats) {
    stats.innerHTML = `
      <span class="api-stat"><strong>${visibleApiCount}</strong> 接口</span>
      ${Object.entries(methodCounts).map(([method, count]) => `<span class="api-stat"><strong>${count}</strong> ${method}</span>`).join("")}
    `;
  }

  // Detail first. The left catalog click handler scrolls only this right panel.
  detail.innerHTML = `
    <div class="api-util-section" id="api-util-python">
      <h2>Python 工具模块</h2>
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

  // TOC uses data-target instead of native anchor jumping so the outer page and
  // the left catalog keep their own scroll positions.
  toc.innerHTML = `
    <div class="toc-title">
      <span>接口目录</span>
      <span class="toc-count">${visibleApiCount} 项</span>
    </div>
    <a class="toc-group-link" href="#api-util-python" data-target="api-util-python">Python 工具模块</a>
    ${filteredGroups.map(g =>
      `<div class="toc-group">
        <a class="toc-group-link" href="#api-group-${g.id}" data-target="api-group-${g.id}">${g.title}</a>
        ${g.apis.map(a => {
          const targetId = `api-${slug(a)}`;
          return `<a class="toc-item" href="#${targetId}" data-target="${targetId}"><span class="method-tag method-${a.method.toLowerCase()}">${a.method}</span>${a.summary}</a>`;
        }).join("")}
      </div>`
    ).join("")}
  `;

  // 绑定 TOC 点击事件——在右侧面板内滚动，左侧导航固定不动
  toc.querySelectorAll('[data-target]').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      scrollApiDetailTo(el.dataset.target);
      history.replaceState(null, "", `#${el.dataset.target}`);
    });
  });

  // Syntax highlight for Python code blocks
  document.querySelectorAll(".python-code").forEach(el => {
    el.style.whiteSpace = "pre-wrap";
    el.style.wordBreak = "break-word";
  });

  bindApiDetailScrollSpy();

  const hashTarget = getApiHashTarget();
  if (hashTarget) {
    requestAnimationFrame(() => scrollApiDetailTo(hashTarget, "auto"));
  } else {
    setActiveTocLink("api-util-python");
  }
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

function scrollApiDetailTo(targetId, behavior = "smooth") {
  const detail = document.getElementById("apiDetail");
  const target = document.getElementById(targetId);
  if (!detail || !target) return;

  const targetRect = target.getBoundingClientRect();
  const detailRect = detail.getBoundingClientRect();
  const top = detail.scrollTop + targetRect.top - detailRect.top - 8;
  detail.scrollTo({ top, behavior });
  setActiveTocLink(targetId);
}

function setActiveTocLink(targetId) {
  document.querySelectorAll("#apiToc [data-target]").forEach(el => {
    el.classList.toggle("active", el.dataset.target === targetId);
  });
}

function bindApiDetailScrollSpy() {
  const detail = document.getElementById("apiDetail");
  if (!detail) return;

  detail.onscroll = () => {
    const targets = Array.from(document.querySelectorAll("#apiToc [data-target]"))
      .map(el => document.getElementById(el.dataset.target))
      .filter(Boolean);
    const nearBottom = detail.scrollTop + detail.clientHeight >= detail.scrollHeight - 4;
    if (nearBottom && targets.length) {
      setActiveTocLink(targets[targets.length - 1].id);
      return;
    }

    const detailTop = detail.getBoundingClientRect().top;
    let active = targets[0]?.id || "";

    for (const target of targets) {
      if (target.getBoundingClientRect().top - detailTop <= 16) {
        active = target.id;
      } else {
        break;
      }
    }

    if (active) setActiveTocLink(active);
  };
}

function getApiHashTarget() {
  const rawHash = decodeURIComponent(location.hash.replace(/^#/, ""));
  if (!rawHash) return "";
  if (document.getElementById(rawHash)) return rawHash;
  if (document.getElementById(`api-group-${rawHash}`)) return `api-group-${rawHash}`;

  const normalized = rawHash.toLowerCase();
  const api = API_GROUPS.flatMap(g => g.apis).find(item => {
    const pathAlias = item.path
      .replace(/^\/+/, "")
      .replace(/[{}]/g, "")
      .replace(/[^a-zA-Z0-9]+/g, "-")
      .replace(/^-|-$/g, "")
      .toLowerCase();
    return slug(item) === normalized || pathAlias === normalized || item.path.toLowerCase().endsWith(`/${normalized}`);
  });

  return api ? `api-${slug(api)}` : "";
}
