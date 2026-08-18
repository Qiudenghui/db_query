#!/usr/bin/env python3
"""智能数据库查询工具（第二章/第三章综合练习）。

一个基于 SQLite 的轻量级命令行数据库查询工具，支持：
- 自然语言式 / 直接 SQL 查询
- 将查询结果导出为 CSV 或 JSON
- 通过 `export` 子命令实现“查询 + 导出”一键完成

用法示例：
    # 交互模式
    python db_query.py

    # 直接执行一条 SQL 并导出为 CSV
    python db_query.py query "SELECT * FROM employees WHERE department='Sales'" --export csv --output result.csv

    # 直接执行一条 SQL 并导出为 JSON
    python db_query.py query "SELECT * FROM employees" --export json --output result.json
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from typing import Any, Iterable


def _setup_stdout() -> None:
    """Windows 控制台默认 GBK，无法打印部分 Unicode。重配置为 UTF-8。"""
    try:
        if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
            sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo.db")
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT,
    salary REAL,
    hire_date TEXT
);

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT
);
"""

SEED_SQL = [
    "INSERT OR IGNORE INTO departments (id, name, location) VALUES (1, 'Sales', 'Beijing'), (2, 'Engineering', 'Shanghai'), (3, 'HR', 'Shenzhen');",
    "INSERT OR IGNORE INTO employees (id, name, department, salary, hire_date) VALUES "
    "(1, 'Alice', 'Sales', 8000, '2021-03-01'),"
    "(2, 'Bob', 'Engineering', 12000, '2020-07-15'),"
    "(3, 'Carol', 'HR', 7500, '2022-01-10'),"
    "(4, 'David', 'Engineering', 15000, '2019-11-20'),"
    "(5, 'Eve', 'Sales', 9000, '2023-05-30');",
]


@dataclass
class QueryResult:
    """统一的查询结果封装，方便在导出模块间流转。"""

    columns: list[str]
    rows: list[tuple[Any, ...]]

    def to_dicts(self) -> list[dict[str, Any]]:
        return [dict(zip(self.columns, row)) for row in self.rows]

    @property
    def count(self) -> int:
        return len(self.rows)


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    """初始化（或连接）SQLite 数据库，并写入示例数据。"""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA_SQL)
    for stmt in SEED_SQL:
        conn.execute(stmt)
    conn.commit()
    return conn


def run_query(conn: sqlite3.Connection, sql: str) -> QueryResult:
    """执行一条只读查询，返回结构化结果。"""
    cur = conn.execute(sql)
    columns = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    return QueryResult(columns=columns, rows=rows)


# ---------------------------------------------------------------------------
# 导出模块：把 QueryResult 格式化为文件
# ---------------------------------------------------------------------------
def export_csv(result: QueryResult, output: str) -> str:
    """将查询结果导出为 CSV 文件，返回实际写入路径。"""
    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(result.columns)
        writer.writerows(result.rows)
    return os.path.abspath(output)


def export_json(result: QueryResult, output: str) -> str:
    """将查询结果导出为 JSON 文件（数组对象形式），返回实际写入路径。"""
    data = result.to_dicts()
    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return os.path.abspath(output)


EXPORTERS = {
    "csv": export_csv,
    "json": export_json,
}


def export_result(result: QueryResult, fmt: str, output: str | None = None) -> str:
    """根据格式选择导出器，自动生成默认文件名。"""
    fmt = fmt.lower()
    if fmt not in EXPORTERS:
        raise ValueError(f"不支持的导出格式: {fmt!r}，仅支持 {list(EXPORTERS)}")
    if not output:
        output = f"export_{result.count}rows.{fmt}"
    return EXPORTERS[fmt](result, output)


# ---------------------------------------------------------------------------
# 交互模式：查询后 AI 助手主动询问是否导出
# ---------------------------------------------------------------------------
def interactive(conn: sqlite3.Connection) -> None:
    print("=" * 60)
    print("智能数据库查询工具 (输入 SQL 或 'help' / 'exit')")
    print("=" * 60)
    while True:
        try:
            sql = input("\nSQL> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        if not sql:
            continue
        if sql.lower() in {"exit", "quit"}:
            print("再见！")
            break
        if sql.lower() == "help":
            print("示例: SELECT * FROM employees WHERE department='Sales'")
            print("查询后我会询问你是否要导出为 CSV 或 JSON。")
            continue
        try:
            result = run_query(conn, sql)
        except sqlite3.Error as e:
            print(f"查询出错: {e}")
            continue

        print(f"\n返回 {result.count} 行，字段: {', '.join(result.columns)}")
        _preview(result)

        # 核心交互点：AI 助手主动询问是否导出
        ask = input("需要将这次查询结果导出为 CSV 或 JSON 文件吗？(csv/json/n): ").strip().lower()
        if ask in {"csv", "json"}:
            path = export_result(result, ask)
            print(f"[OK] 已导出到: {path}")
        elif ask == "n":
            print("好的，未导出。")
        else:
            print("未识别的输入，跳过导出。")


def _preview(result: QueryResult, limit: int = 5) -> None:
    for row in result.rows[:limit]:
        print(row)
    if result.count > limit:
        print(f"... 省略 {result.count - limit} 行")


# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="智能数据库查询工具")
    sub = p.add_subparsers(dest="command")

    q = sub.add_parser("query", help="执行一条 SQL")
    q.add_argument("sql", help="要执行的 SQL 语句")
    q.add_argument("--export", choices=["csv", "json"], help="导出格式")
    q.add_argument("--output", help="导出文件路径（默认自动命名）")

    sub.add_parser("interactive", help="进入交互模式（默认）")
    return p


def main(argv: list[str] | None = None) -> int:
    _setup_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)
    conn = init_db()

    if args.command == "query":
        result = run_query(conn, args.sql)
        print(f"返回 {result.count} 行")
        _preview(result)
        if args.export:
            path = export_result(result, args.export, args.output)
            print(f"[OK] 已导出到: {path}")
        conn.close()
        return 0

    # 默认进入交互模式
    interactive(conn)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
