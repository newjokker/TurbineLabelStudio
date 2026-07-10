#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""综合 API 测试脚本 —— 覆盖全部公开接口。

使用方式:
    cd /Volumes/Jokker/Code/TurbineLabelStudio
    python test/test_all_apis.py

环境变量（可选）:
    TLS_BASE_URL       服务地址（默认 http://127.0.0.1:8765）
    TLS_USERNAME       登录用户名（默认 txkj）
    TLS_PASSWORD       登录密码（默认 txkj）
    TLS_BUC            测试 BUC（默认 BUC_000001）
    TLS_FUNC           测试 func（默认 wh_jzp_before_20260708）
    TLS_POSITION_ID    测试 position_id（默认 B1A）
    TLS_SKIP_BINARY    跳过二进制下载测试（默认 0，设为 1 跳过）
    TLS_SKIP_WRITE     跳过写操作测试（默认 0，设为 1 跳过）
"""

import json
import os
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path so `from test._common` works
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from _common import (
    BASE_URL, USERNAME, PASSWORD, DEFAULT_BUC, DEFAULT_FUNC, DEFAULT_POSITION_ID,
    api_url, login_headers, request_json, download_file, print_result, OUTPUT_DIR,
)

SKIP_BINARY = os.environ.get("TLS_SKIP_BINARY", "0") == "1"
SKIP_WRITE = os.environ.get("TLS_SKIP_WRITE", "0") == "1"

PASS = 0
FAIL = 0
SKIP = 0


def test(name, condition, detail=""):
    global PASS, FAIL, SKIP
    if condition is False:  # explicitly skipped
        SKIP += 1
        print(f"  ⏭  {name} [SKIP] {detail}")
        return True
    elif condition:
        PASS += 1
        print(f"  ✅ {name}")
        return True
    else:
        FAIL += 1
        print(f"  ❌ {name} {detail}")
        return False


# =============================================================================
# 认证
# =============================================================================
def test_auth():
    print("\n── 🔐 认证 ──")
    headers = login_headers()
    test("POST /api/login", bool(headers.get("X-User-Id")))

    status, data = request_json("GET", "/api/login")  # 不存在的路由
    test("GET /api/login → 405", status == 405)

    status, data = request_json("GET", "/api/permissions", headers=headers)
    test("GET /api/permissions → 200", status == 200, json.dumps(data, ensure_ascii=False)[:120])
    test("  + user.id 存在", "user" in data and "id" in data["user"])
    test("  + permissions 存在", "permissions" in data)
    return headers


# =============================================================================
# 标签
# =============================================================================
def test_labels(headers):
    print("\n── 🏷️ 标签管理 ──")
    status, data = request_json("GET", "/api/labels", headers=headers)
    test("GET /api/labels → 200", status == 200)
    test("  + items 为 list", isinstance(data.get("items"), list))

    if SKIP_WRITE:
        print("  ⏭ 写操作跳过 (TLS_SKIP_WRITE=1)")
        return

    tag_name = f"_api_test_label_{int(time.time())}"
    status, data = request_json(
        "POST", "/api/labels",
        {"label": tag_name, "des": "API 测试用标签", "extra_info": {"color": "#e74c3c"}},
        headers=headers,
    )
    ok = test("POST /api/labels → 200", status == 200, json.dumps(data, ensure_ascii=False)[:120])
    label_id = data.get("item", {}).get("id") if ok else None

    if label_id:
        status, data = request_json(
            "PUT", f"/api/labels/{label_id}",
            {"label": tag_name + "_改", "des": "更新后"},
            headers=headers,
        )
        test(f"PUT /api/labels/{label_id} → 200", status == 200)

        status, data = request_json("DELETE", f"/api/labels/{label_id}", headers=headers)
        test(f"DELETE /api/labels/{label_id} → 200", status == 200)


# =============================================================================
# 标注视图
# =============================================================================
def test_annotation_view(headers):
    print("\n── ✏️ 标注视图 ──")
    status, data = request_json("GET", "/api/annotation-view/options", headers=headers)
    test("GET /api/annotation-view/options → 200", status == 200)
    test("  + items 为 list", isinstance(data.get("items"), list))
    test("  + datasets 为 list", isinstance(data.get("datasets"), list))

    status, data = request_json(
        "GET", "/api/annotation-view/data",
        headers=headers,
        query={"buc": DEFAULT_BUC, "func": DEFAULT_FUNC},
    )
    test("GET /api/annotation-view/data → 200", status == 200, json.dumps(data, ensure_ascii=False)[:120])
    test("  + buc 匹配", data.get("buc") == DEFAULT_BUC)
    test("  + annotations 为 list", isinstance(data.get("annotations"), list))
    test("  + channels 为 list", isinstance(data.get("channels"), list))


# =============================================================================
# 标注锁
# =============================================================================
def test_annotation_lock(headers):
    print("\n── 🔒 标注锁 ──")
    if SKIP_WRITE:
        print("  ⏭ 写操作跳过 (TLS_SKIP_WRITE=1)")
        return

    status, data = request_json(
        "POST", "/api/annotation-lock/lock",
        {"buc": DEFAULT_BUC, "func": DEFAULT_FUNC},
        headers=headers,
    )
    test("POST /api/annotation-lock/lock → 200", status == 200, json.dumps(data, ensure_ascii=False)[:120])
    test("  + expires_in", isinstance(data.get("expires_in"), int))

    status, data = request_json(
        "POST", "/api/annotation-lock/heartbeat",
        {"buc": DEFAULT_BUC, "func": DEFAULT_FUNC},
        headers=headers,
    )
    test("POST /api/annotation-lock/heartbeat → 200", status == 200)

    status, data = request_json(
        "POST", "/api/annotation-lock/unlock",
        {"buc": DEFAULT_BUC, "func": DEFAULT_FUNC},
        headers=headers,
    )
    test("POST /api/annotation-lock/unlock → 200", status == 200)


# =============================================================================
# 标注
# =============================================================================
def test_annotations(headers):
    print("\n── ✏️ 标注 CRUD ──")
    if SKIP_WRITE:
        print("  ⏭ 写操作跳过 (TLS_SKIP_WRITE=1)")
        return

    # Lock first
    request_json("POST", "/api/annotation-lock/lock", {"buc": DEFAULT_BUC, "func": DEFAULT_FUNC}, headers=headers)

    # First get label list to find a valid label_id
    status, label_data = request_json("GET", "/api/labels", headers=headers)
    labels = label_data.get("items", [])
    if not labels:
        test("创建标注 → 无可用标签", False, "请先创建标签")
        request_json("POST", "/api/annotation-lock/unlock", {"buc": DEFAULT_BUC, "func": DEFAULT_FUNC}, headers=headers)
        return
    label_id = labels[0]["id"]

    status, data = request_json(
        "POST", "/api/annotations",
        {"buc": DEFAULT_BUC, "func": DEFAULT_FUNC, "x1": 0.1, "y1": 0.1, "x2": 0.5, "y2": 0.5,
         "label_id": label_id, "difficult": False, "update_reason": "API 测试"},
        headers=headers,
    )
    ok = test("POST /api/annotations → 200", status == 200, json.dumps(data, ensure_ascii=False)[:120])
    annotation_id = data.get("item", {}).get("id") if ok else None

    if annotation_id:
        status, data = request_json("DELETE", f"/api/annotations/{annotation_id}", headers=headers)
        test(f"DELETE /api/annotations/{annotation_id} → 200", status == 200)

    # Unlock
    request_json("POST", "/api/annotation-lock/unlock", {"buc": DEFAULT_BUC, "func": DEFAULT_FUNC}, headers=headers)


# =============================================================================
# 公开数据 API
# =============================================================================
def test_public_bucs(headers):
    print("\n── 📦 公开 BUC 数据 ──")

    status, data = request_json(
        "GET", f"/api/public/bucs/{DEFAULT_BUC}/annotations",
        headers=headers, query={"func": DEFAULT_FUNC},
    )
    test("GET /api/public/bucs/{buc}/annotations → 200", status == 200, json.dumps(data, ensure_ascii=False)[:120])
    test("  + buc 匹配", data.get("buc") == DEFAULT_BUC)
    test("  + annotations 为 list", isinstance(data.get("annotations"), list))
    test("  + buc_audio 为 list", isinstance(data.get("buc_audio"), list))

    if SKIP_BINARY:
        print("  ⏭ 二进制下载跳过 (TLS_SKIP_BINARY=1)")
    else:
        status, result = download_file(
            f"/api/public/bucs/{DEFAULT_BUC}/image",
            f"{DEFAULT_BUC}_{DEFAULT_FUNC}_test.jpg",
            headers=headers,
            query={"func": DEFAULT_FUNC},
        )
        test(f"GET /api/public/bucs/{DEFAULT_BUC}/image → 200", status == 200,
             isinstance(result, Path) and f"saved: {result}" or str(result)[:120])

        status, result = download_file(
            f"/api/public/bucs/{DEFAULT_BUC}/mel",
            f"{DEFAULT_BUC}_{DEFAULT_FUNC}_mel_test.jpg",
            headers=headers,
            query={"func": DEFAULT_FUNC},
        )
        test(f"GET /api/public/bucs/{DEFAULT_BUC}/mel → 200", status == 200)

        status, result = download_file(
            f"/api/public/bucs/{DEFAULT_BUC}/audio/{DEFAULT_POSITION_ID}",
            f"{DEFAULT_BUC}_{DEFAULT_POSITION_ID}_test.wav",
            headers=headers,
        )
        test(f"GET /api/public/bucs/{DEFAULT_BUC}/audio/{DEFAULT_POSITION_ID} → 200", status == 200)

        status, result = download_file(
            f"/api/public/bucs/{DEFAULT_BUC}/audio",
            f"{DEFAULT_BUC}_audio_test.zip",
            headers=headers,
        )
        test(f"GET /api/public/bucs/{DEFAULT_BUC}/audio (ZIP) → 200", status == 200)


# =============================================================================
# 数据集
# =============================================================================
def test_datasets(headers):
    print("\n── 📊 数据集管理 ──")
    status, data = request_json("GET", "/api/datasets", headers=headers)
    test("GET /api/datasets → 200", status == 200)
    test("  + items 为 list", isinstance(data.get("items"), list))
    test("  + all_bucs 为 list", isinstance(data.get("all_bucs"), list))

    if SKIP_WRITE:
        print("  ⏭ 写操作跳过 (TLS_SKIP_WRITE=1)")
        return

    # Public create
    ds_name = f"_api_test_ds_{int(time.time())}"
    status, data = request_json(
        "POST", "/api/public/datasets",
        {"name": ds_name, "des": "API 测试数据集"},
        headers=headers,
    )
    ok = test("POST /api/public/datasets → 200", status == 200, json.dumps(data, ensure_ascii=False)[:120])
    ds_id = data.get("item", {}).get("id") if ok else None

    # Update BUCs
    if ds_id:
        status, data = request_json(
            "PUT", f"/api/public/datasets/{ds_id}/bucs",
            {"bucs": [DEFAULT_BUC]},
            headers=headers,
        )
        test(f"PUT /api/public/datasets/{ds_id}/bucs → 200", status == 200)

        # Internal update
        status, data = request_json(
            "PUT", f"/api/datasets/{ds_id}",
            {"name": ds_name + "_改", "des": "更新后", "bucs": [DEFAULT_BUC]},
            headers=headers,
        )
        test(f"PUT /api/datasets/{ds_id} → 200", status == 200)

        # Delete
        status, data = request_json("DELETE", f"/api/datasets/{ds_id}", headers=headers)
        test(f"DELETE /api/datasets/{ds_id} → 200", status == 200)


# =============================================================================
# 账号
# =============================================================================
def test_accounts(headers):
    print("\n── 👤 账号管理 ──")
    status, data = request_json("GET", "/api/accounts", headers=headers)
    test("GET /api/accounts → 200", status == 200)
    test("  + items 为 list", isinstance(data.get("items"), list))

    if SKIP_WRITE:
        print("  ⏭ 写操作跳过 (TLS_SKIP_WRITE=1)")
        return

    account_name = f"_api_test_user_{int(time.time())}"
    status, data = request_json(
        "POST", "/api/accounts",
        {"name": account_name, "password": "test123", "alias": "测试账号", "role": "观察者"},
        headers=headers,
    )
    ok = test("POST /api/accounts → 200", status == 200, json.dumps(data, ensure_ascii=False)[:120])
    account_id = data.get("item", {}).get("id") if ok else None

    if account_id:
        status, data = request_json(
            "PUT", f"/api/accounts/{account_id}",
            {"name": account_name + "_改", "password": "newpass", "alias": "改名", "role": "编辑者"},
            headers=headers,
        )
        test(f"PUT /api/accounts/{account_id} → 200", status == 200)

        status, data = request_json(
            "POST", f"/api/accounts/{account_id}/disable",
            headers=headers,
        )
        test(f"POST /api/accounts/{account_id}/disable → 200", status == 200)


# =============================================================================
# Main
# =============================================================================
def main():
    print("=" * 70)
    print("TurbineLabelStudio API 全量测试")
    print(f"  BASE_URL      = {BASE_URL}")
    print(f"  USERNAME      = {USERNAME}")
    print(f"  DEFAULT_BUC   = {DEFAULT_BUC}")
    print(f"  DEFAULT_FUNC  = {DEFAULT_FUNC}")
    print(f"  SKIP_BINARY   = {SKIP_BINARY}")
    print(f"  SKIP_WRITE    = {SKIP_WRITE}")
    print(f"  OUTPUT_DIR    = {OUTPUT_DIR}")
    print("=" * 70)

    headers = test_auth()

    test_labels(headers)
    test_annotation_view(headers)
    test_annotation_lock(headers)
    test_annotations(headers)
    test_public_bucs(headers)
    test_datasets(headers)
    test_accounts(headers)

    total = PASS + FAIL + SKIP
    print(f"\n{'=' * 70}")
    print(f"  总计: {total}  |  ✅ 通过: {PASS}  |  ❌ 失败: {FAIL}  |  ⏭ 跳过: {SKIP}")
    print(f"{'=' * 70}")

    if FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()