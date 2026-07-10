#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test POST /api/public/datasets."""

import os
import time

from _common import login_headers, print_result, request_json


def main():
    headers = login_headers()
    name = os.environ.get("TLS_DATASET_NAME", f"api_test_dataset_{int(time.time())}")
    des = os.environ.get("TLS_DATASET_DES", "公开 API 测试创建的数据集")
    status, data = request_json(
        "POST",
        "/api/public/datasets",
        {
            "name": name,
            "des": des,
        },
        headers=headers,
    )
    print_result("POST /api/public/datasets", status, data)


if __name__ == "__main__":
    main()
