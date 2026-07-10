#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test GET /api/public/bucs/{buc}/audio/{position_id}."""

from _common import DEFAULT_BUC, DEFAULT_POSITION_ID, download_file, login_headers, print_result


def main():
    headers = login_headers()
    status, data = download_file(
        f"/api/public/bucs/{DEFAULT_BUC}/audio/{DEFAULT_POSITION_ID}",
        f"{DEFAULT_BUC}_{DEFAULT_POSITION_ID}.wav",
        headers=headers,
    )
    print_result(f"GET /api/public/bucs/{DEFAULT_BUC}/audio/{DEFAULT_POSITION_ID}", status, data)


if __name__ == "__main__":
    main()
