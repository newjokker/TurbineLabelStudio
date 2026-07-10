#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test PUT /api/public/datasets/{dataset_id}/bucs.

By default this script creates a temporary dataset, edits its BUC list, then
deletes it through the existing internal delete endpoint so real data is not
changed. Set TLS_DATASET_ID to edit a specific existing dataset.
"""

import os
import time

from _common import login_headers, print_result, request_json


def main():
    headers = login_headers()
    dataset_id = os.environ.get("TLS_DATASET_ID")
    created_temp = False

    if not dataset_id:
        status, data = request_json(
            "POST",
            "/api/public/datasets",
            {
                "name": f"api_test_dataset_bucs_{int(time.time())}",
                "des": "公开 API 测试编辑 BUC 的临时数据集",
            },
            headers=headers,
        )
        if status != 200:
            print_result("create temp dataset", status, data)
            return
        dataset_id = str(data["item"]["id"])
        created_temp = True

    bucs = [
        item.strip()
        for item in os.environ.get("TLS_DATASET_BUCS", "BUC_000001,BUC_000002").split(",")
        if item.strip()
    ]
    status, data = request_json(
        "PUT",
        f"/api/public/datasets/{dataset_id}/bucs",
        {
            "bucs": bucs,
        },
        headers=headers,
    )
    print_result(f"PUT /api/public/datasets/{dataset_id}/bucs", status, data)

    if created_temp:
        delete_status, delete_data = request_json(
            "DELETE",
            f"/api/datasets/{dataset_id}",
            headers=headers,
        )
        print_result(f"cleanup DELETE /api/datasets/{dataset_id}", delete_status, delete_data)


if __name__ == "__main__":
    main()
