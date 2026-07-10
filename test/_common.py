#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Public API test helpers.

Run scripts from the repository root, for example:
    python test/test_public_get_buc_annotations.py
"""

import json
import os
from pathlib import Path
from urllib import error, parse, request


BASE_URL = os.environ.get("TLS_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
USERNAME = os.environ.get("TLS_USERNAME", "txkj")
PASSWORD = os.environ.get("TLS_PASSWORD", "txkj")
DEFAULT_BUC = os.environ.get("TLS_BUC", "BUC_000001")
DEFAULT_FUNC = os.environ.get("TLS_FUNC", "wh_jzp_before_20260708")
DEFAULT_POSITION_ID = os.environ.get("TLS_POSITION_ID", "B1A")
OUTPUT_DIR = Path(os.environ.get("TLS_OUTPUT_DIR", "test/output"))


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
    status, data = request_json(
        "POST",
        "/api/login",
        {
            "name": USERNAME,
            "password": PASSWORD,
        },
    )
    if status != 200:
        raise RuntimeError(f"登录失败 status={status} data={data}")
    return {
        "X-User-Id": str(data["user"]["id"]),
        "X-Session-Id": data["session_id"],
    }


def print_result(title, status, data):
    print(f"== {title} ==")
    print(f"status: {status}")
    if isinstance(data, Path):
        print(f"saved: {data}")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
