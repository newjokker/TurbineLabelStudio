#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过 TurbineLabelStudio API 下载全部 BUC 的 mel 图和标注 XML。

示例：
    python 012_下载buc的mel和xml.py ./res

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


DEFAULT_BASE_URL = os.environ.get("TLS_BASE_URL", "http://192.168.3.69:12502")
DEFAULT_FUNC = os.environ.get("TLS_FUNC", "wh_jzp_before_20260708")
DEFAULT_USERNAME = os.environ.get("TLS_USERNAME", "ldq")
DEFAULT_PASSWORD = os.environ.get("TLS_PASSWORD", "747225581")


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


def get_all_bucs_by_api(base_url, headers):
    """通过导出 API 获取全部 BUC。"""
    data = request_json(
        "GET",
        api_url(base_url, "/api/public/bucs"),
        headers=headers,
    )
    items = data.get("items", [])
    bucs = []
    seen = set()
    for item in items:
        buc = item.get("buc") if isinstance(item, dict) else item
        buc = str(buc or "").strip()
        if buc and buc not in seen:
            seen.add(buc)
            bucs.append(buc)
    return bucs


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


def format_exception(exc):
    if isinstance(exc, error.HTTPError):
        return f"HTTP {exc.code}: {read_http_error(exc)}"
    return str(exc)


def is_complete_file_pair(image_path, xml_path):
    """JPG 非空且 XML 可解析时，才视为已完整下载。"""
    if not image_path.is_file() or image_path.stat().st_size == 0:
        return False
    if not xml_path.is_file() or xml_path.stat().st_size == 0:
        return False
    try:
        return ET.parse(xml_path).getroot().tag == "annotation"
    except (ET.ParseError, OSError):
        return False


def parse_args():
    parser = argparse.ArgumentParser(description="通过 API 下载全部 BUC 的 mel 图和 XML")
    parser.add_argument("save_dir", nargs="?", default="./res", help="文件保存目录")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API 服务地址")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help="登录账号")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="登录密码")
    parser.add_argument("--func", default=DEFAULT_FUNC, help="mel 图生成方法")
    parser.add_argument("--overwrite", action="store_true", help="重新下载已经存在的完整文件对")
    return parser.parse_args()


def main():
    args = parse_args()
    save_dir = Path(args.save_dir).expanduser().resolve()
    username = args.username or input("请输入登录账号：").strip()
    password = args.password if args.password is not None else getpass.getpass("请输入登录密码：")

    if not username or not password:
        raise ValueError("登录账号和密码不能为空")

    save_dir.mkdir(parents=True, exist_ok=True)
    headers = login(args.base_url, username, password)
    bucs = get_all_bucs_by_api(args.base_url, headers)
    total = len(bucs)
    print(f"API 共返回 {total} 个 BUC，保存目录：{save_dir}")

    success_count = 0
    skip_count = 0
    empty_annotation_count = 0
    failures = []

    for index, buc in enumerate(bucs, start=1):
        file_prefix = f"{buc}_{args.func}"
        image_path = save_dir / f"{file_prefix}.jpg"
        xml_path = save_dir / f"{file_prefix}.xml"
        if not args.overwrite and is_complete_file_pair(image_path, xml_path):
            skip_count += 1
            print(f"[{index}/{total}] 跳过已存在：{buc}")
            continue

        try:
            image_path, xml_path, annotation_count = export_buc_by_api(
                base_url=args.base_url,
                headers=headers,
                buc=buc,
                save_dir=save_dir,
                func_name=args.func,
            )
            success_count += 1
            if annotation_count == 0:
                empty_annotation_count += 1
            print(
                f"[{index}/{total}] 下载成功：{buc} "
                f"标注框={annotation_count}"
            )
        except error.HTTPError as exc:
            # 长时间批量下载期间，账号可能在别处重新登录并使会话失效。
            if exc.code == 401:
                try:
                    headers = login(args.base_url, username, password)
                    image_path, xml_path, annotation_count = export_buc_by_api(
                        base_url=args.base_url,
                        headers=headers,
                        buc=buc,
                        save_dir=save_dir,
                        func_name=args.func,
                    )
                    success_count += 1
                    if annotation_count == 0:
                        empty_annotation_count += 1
                    print(f"[{index}/{total}] 重新登录后下载成功：{buc} 标注框={annotation_count}")
                    continue
                except Exception as retry_exc:
                    reason = format_exception(retry_exc)
            else:
                reason = format_exception(exc)
            failures.append({"buc": buc, "reason": reason})
            print(f"[{index}/{total}] 下载失败：{buc}，原因：{reason}", file=sys.stderr)
        except Exception as exc:
            reason = format_exception(exc)
            failures.append({"buc": buc, "reason": reason})
            print(f"[{index}/{total}] 下载失败：{buc}，原因：{reason}", file=sys.stderr)

    failure_path = save_dir / "download_failures.json"
    if failures:
        failure_path.write_text(
            json.dumps(failures, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    else:
        failure_path.unlink(missing_ok=True)

    print(
        "批量下载完成："
        f"总数={total}，成功={success_count}，跳过={skip_count}，"
        f"空标注={empty_annotation_count}，失败={len(failures)}"
    )
    if failures:
        print(f"失败清单：{failure_path}")
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except error.HTTPError as exc:
        print(f"API 请求失败（HTTP {exc.code}）：{read_http_error(exc)}", file=sys.stderr)
        sys.exit(1)
    except error.URLError as exc:
        print(f"连接 API 失败：{exc.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"下载失败：{exc}", file=sys.stderr)
        sys.exit(1)
