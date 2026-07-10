#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test GET /api/public/bucs/{buc}/annotations."""

from _common import DEFAULT_BUC, DEFAULT_FUNC, login_headers, print_result, request_json


def main():
    headers = login_headers()
    status, data = request_json(
        "GET",
        f"/api/public/bucs/{DEFAULT_BUC}/annotations",
        headers=headers,
        query={"func": DEFAULT_FUNC},
    )
    print_result(f"GET /api/public/bucs/{DEFAULT_BUC}/annotations", status, data)


if __name__ == "__main__":
    main()
