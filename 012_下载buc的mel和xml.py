#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过 TurbineLabelStudio API 下载指定 BUC 的 mel 图和标注 XML。

示例：
    python 012_下载buc的mel和xml.py BUC_000001 ./res

服务地址、账号和密码既可以通过参数传入，也可以使用环境变量：
    TLS_BASE_URL、TLS_USERNAME、TLS_PASSWORD、TLS_FUNC
"""

import argparse
import getpass
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib import error, parse, request


DEFAULT_BASE_URL = os.environ.get("TLS_BASE_URL", "http://127.0.0.1:12502")
DEFAULT_FUNC = os.environ.get("TLS_FUNC", "wh_jzp_before_20260708")


def api_url(base_url, path, query=None):
    url = f"{base_url.rstrip('/')}{path}"
    if query:
        url = f"{url}?{parse.urlencode(query)}"
    return url


def request_json(method, url, payload=None, headers=None, timeout=120):
    body = None
    request_headers = {"Accept": "application/json"}
    request_headers.update(headers or {})
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    req = request.Request(url, data=body, headers=request_headers, method=method)
    with request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def login(base_url, username, password):
    data = request_json(
        "POST",
        api_url(base_url, "/api/login"),
        {"name": username, "password": password},
    )
    return {
        "X-User-Id": str(data["user"]["id"]),
        "X-Session-Id": data["session_id"],
    }


def download_file(url, headers, save_path):
    """下载到临时文件，成功后再替换目标文件。"""
    temp_path = save_path.with_name(f".{save_path.name}.part")
    req = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=300) as resp, temp_path.open("wb") as f:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
        temp_path.replace(save_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def export_buc_by_api(base_url, headers, buc, save_dir, func_name=DEFAULT_FUNC):
    """通过 API 导出一个 BUC，并校验 JSON 标注数与 XML object 数一致。"""
    buc = buc.strip()
    func_name = func_name.strip()
    if not buc:
        raise ValueError("BUC 不能为空")
    if not func_name:
        raise ValueError("func 不能为空")
    if Path(buc).name != buc or Path(func_name).name != func_name:
        raise ValueError("BUC 和 func 不能包含路径分隔符")

    target_dir = Path(save_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_buc = parse.quote(buc, safe="")
    query = {"func": func_name}

    annotation_data = request_json(
        "GET",
        api_url(base_url, f"/api/public/bucs/{safe_buc}/annotations", query),
        headers=headers,
    )
    api_annotation_count = int(annotation_data.get("annotation_count", 0))

    file_prefix = f"{buc}_{func_name}"
    image_path = target_dir / f"{file_prefix}.jpg"
    xml_path = target_dir / f"{file_prefix}.xml"

    download_file(
        api_url(base_url, f"/api/public/bucs/{safe_buc}/mel", query),
        headers,
        image_path,
    )
    try:
        download_file(
            api_url(base_url, f"/api/public/bucs/{safe_buc}/annotations/xml", query),
            headers,
            xml_path,
        )
        xml_annotation_count = len(ET.parse(xml_path).getroot().findall("object"))
        if xml_annotation_count != api_annotation_count:
            raise RuntimeError(
                "标注数量不一致："
                f"JSON API={api_annotation_count}，XML object={xml_annotation_count}"
            )
    except Exception:
        image_path.unlink(missing_ok=True)
        xml_path.unlink(missing_ok=True)
        raise

    return image_path, xml_path, api_annotation_count


def read_http_error(exc):
    try:
        data = json.loads(exc.read().decode("utf-8"))
        detail = data.get("detail", data)
        return json.dumps(detail, ensure_ascii=False) if not isinstance(detail, str) else detail
    except (UnicodeDecodeError, json.JSONDecodeError):
        return str(exc.reason)


def parse_args():
    parser = argparse.ArgumentParser(description="通过 API 下载指定 BUC 的 mel 图和 XML")
    parser.add_argument("buc", nargs="?", help="例如 BUC_000001")
    parser.add_argument("save_dir", nargs="?", help="文件保存目录")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API 服务地址")
    parser.add_argument("--username", default=os.environ.get("ldq"), help="登录账号")
    parser.add_argument("--password", default=os.environ.get("ldq"), help="登录密码")
    parser.add_argument("--func", default=DEFAULT_FUNC, help="mel 图生成方法")
    return parser.parse_args()


def main():
    args = parse_args()
    save_dir = "./res"
    username = "ldq"
    password = "ldq"

    if not save_dir:
        raise ValueError("保存文件夹不能为空")
    if not username or not password:
        raise ValueError("登录账号和密码不能为空")

    headers = login(args.base_url, username, password)
    image_path, xml_path, annotation_count = export_buc_by_api(
        base_url=args.base_url,
        headers=headers,
        buc=args.buc,
        save_dir=save_dir,
        func_name=args.func,
    )

    print(f"mel 图已保存：{image_path}")
    print(f"XML 已保存：{xml_path}")
    print(f"标注框数量：{annotation_count}")
    if annotation_count == 0:
        print(f"提示：{args.buc} 在 func={args.func} 下没有标注记录，因此 XML 不含 object。")


if __name__ == "__main__":
    try:
        main()
    except error.HTTPError as exc:
        print(f"API 请求失败（HTTP {exc.code}）：{read_http_error(exc)}", file=sys.stderr)
        sys.exit(1)
    except error.URLError as exc:
        print(f"连接 API 失败：{exc.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"下载失败：{exc}", file=sys.stderr)
        sys.exit(1)
