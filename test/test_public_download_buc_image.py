#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test GET /api/public/bucs/{buc}/image."""

from _common import DEFAULT_BUC, DEFAULT_FUNC, download_file, login_headers, print_result


def main():
    headers = login_headers()
    status, data = download_file(
        f"/api/public/bucs/{DEFAULT_BUC}/image",
        f"{DEFAULT_BUC}_{DEFAULT_FUNC}.jpg",
        headers=headers,
        query={"func": DEFAULT_FUNC},
    )
    print_result(f"GET /api/public/bucs/{DEFAULT_BUC}/image", status, data)


if __name__ == "__main__":
    main()
