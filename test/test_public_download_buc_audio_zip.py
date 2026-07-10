#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test GET /api/public/bucs/{buc}/audio."""

from _common import DEFAULT_BUC, download_file, login_headers, print_result


def main():
    headers = login_headers()
    status, data = download_file(
        f"/api/public/bucs/{DEFAULT_BUC}/audio",
        f"{DEFAULT_BUC}_audio.zip",
        headers=headers,
    )
    print_result(f"GET /api/public/bucs/{DEFAULT_BUC}/audio", status, data)


if __name__ == "__main__":
    main()
