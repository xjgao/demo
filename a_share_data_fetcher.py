#!/usr/bin/env python3
"""A股股票数据拉取并存储到SQLite数据库。"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

EASTMONEY_API = "https://push2.eastmoney.com/api/qt/clist/get"


@dataclass
class StockQuote:
    symbol: str
    name: str
    latest_price: float | None
    change_percent: float | None
    change_amount: float | None
    volume: float | None
    turnover: float | None
    open_price: float | None
    high_price: float | None
    low_price: float | None
    pre_close: float | None
    volume_ratio: float | None
    turnover_rate: float | None
    pe_ratio: float | None


def _to_float(value: object) -> float | None:
    if value in (None, "-", ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def create_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS a_share_quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fetched_at TEXT NOT NULL,
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            latest_price REAL,
            change_percent REAL,
            change_amount REAL,
            volume REAL,
            turnover REAL,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            pre_close REAL,
            volume_ratio REAL,
            turnover_rate REAL,
            pe_ratio REAL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_a_share_quotes_symbol_fetched_at
        ON a_share_quotes(symbol, fetched_at)
        """
    )


def fetch_a_share_quotes(page_size: int = 5000) -> list[StockQuote]:
    params = {
        "pn": "1",
        "pz": str(page_size),
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
        "fields": "f12,f14,f2,f3,f4,f5,f6,f17,f15,f16,f18,f10,f8,f9",
    }
    url = EASTMONEY_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urllib.request.urlopen(req, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))

    diff = payload.get("data", {}).get("diff", [])
    quotes: list[StockQuote] = []
    for item in diff:
        symbol = str(item.get("f12", "")).strip()
        name = str(item.get("f14", "")).strip()
        if not symbol or not name:
            continue

        quotes.append(
            StockQuote(
                symbol=symbol,
                name=name,
                latest_price=_to_float(item.get("f2")),
                change_percent=_to_float(item.get("f3")),
                change_amount=_to_float(item.get("f4")),
                volume=_to_float(item.get("f5")),
                turnover=_to_float(item.get("f6")),
                open_price=_to_float(item.get("f17")),
                high_price=_to_float(item.get("f15")),
                low_price=_to_float(item.get("f16")),
                pre_close=_to_float(item.get("f18")),
                volume_ratio=_to_float(item.get("f10")),
                turnover_rate=_to_float(item.get("f8")),
                pe_ratio=_to_float(item.get("f9")),
            )
        )

    return quotes


def save_quotes(conn: sqlite3.Connection, quotes: Iterable[StockQuote], fetched_at: str) -> int:
    rows = [
        (
            fetched_at,
            q.symbol,
            q.name,
            q.latest_price,
            q.change_percent,
            q.change_amount,
            q.volume,
            q.turnover,
            q.open_price,
            q.high_price,
            q.low_price,
            q.pre_close,
            q.volume_ratio,
            q.turnover_rate,
            q.pe_ratio,
        )
        for q in quotes
    ]

    conn.executemany(
        """
        INSERT INTO a_share_quotes (
            fetched_at, symbol, name, latest_price, change_percent, change_amount,
            volume, turnover, open_price, high_price, low_price, pre_close,
            volume_ratio, turnover_rate, pe_ratio
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def run(db_path: Path, page_size: int = 5000) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    fetched_at = dt.datetime.now(dt.timezone.utc).isoformat()

    quotes = fetch_a_share_quotes(page_size=page_size)
    if not quotes:
        print("未拉取到任何A股数据。")
        return 0

    with sqlite3.connect(db_path) as conn:
        create_table(conn)
        inserted = save_quotes(conn, quotes, fetched_at)
        conn.commit()

    print(f"拉取完成：{inserted} 条，写入数据库：{db_path}")
    return inserted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="拉取A股数据并保存到SQLite数据库")
    parser.add_argument("--db", default="data/a_share_stock.db", help="SQLite数据库路径")
    parser.add_argument("--page-size", type=int, default=5000, help="单次拉取条数上限")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(Path(args.db), page_size=args.page_size)


if __name__ == "__main__":
    main()
