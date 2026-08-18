#!/usr/bin/env python3
"""一键查询并导出命令（自动化流程入口）。

该脚本对应作业要求的"自动化流程"：把"执行查询"和"导出结果"合并为
一个简单命令触发，无需进入交互模式。

用法：
    python export_command.py "SELECT * FROM employees WHERE salary > 10000" csv
    python export_command.py "SELECT * FROM employees" json result.json

第一个参数为 SQL，第二个参数为导出格式（csv/json），第三个可选参数为输出路径。
"""
from __future__ import annotations

import sys

from db_query import export_result, init_db, run_query


def main() -> int:
    if len(sys.argv) < 3:
        print("用法: python export_command.py <SQL> <csv|json> [输出路径]")
        return 1

    sql = sys.argv[1]
    fmt = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) > 3 else None

    conn = init_db()
    try:
        result = run_query(conn, sql)
        path = export_result(result, fmt, output)
        print(f"查询返回 {result.count} 行，已导出为 {fmt.upper()} -> {path}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
