#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test GET /api/public/bucs/{buc}/annotations/xml."""

from _common import DEFAULT_BUC, DEFAULT_FUNC, download_file, login_headers, print_result


def main():
    headers = login_headers()
    status, data = download_file(
        f"/api/public/bucs/{DEFAULT_BUC}/annotations/xml",
        f"{DEFAULT_BUC}_{DEFAULT_FUNC}.xml",
        headers=headers,
        query={"func": DEFAULT_FUNC},
    )
    print_result(f"GET /api/public/bucs/{DEFAULT_BUC}/annotations/xml", status, data)


if __name__ == "__main__":
    main()
