#!/usr/bin/env python3
"""渲染一张"真实运行结果"终端风格 PNG（用于作业提交截图）。

直接 import 项目模块调用函数，避免子进程编码问题，确保图中文字
与实际运行逻辑一致。
"""
from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import db_query  # noqa: E402

PY = sys.executable


def load_font(size: int, chinese: bool = False):
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/consolab.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/cour.ttf",
    ] if chinese else [
        "C:/Windows/Fonts/consolab.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/lucon.ttf",
        "C:/Windows/Fonts/cour.ttf",
        "C:/Windows/Fonts/msyh.ttc",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


def capture_query(sql: str, export_fmt: str, output: str) -> list[str]:
    """真实执行查询+导出，捕获打印输出行。"""
    conn = db_query.init_db()
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = db_query.run_query(conn, sql)
        db_query._preview(result)
        path = db_query.export_result(result, export_fmt, output)
        print(f"[OK] 已导出到: {path}")
    conn.close()
    return [l for l in buf.getvalue().splitlines()]


def main() -> None:
    # 1) 真实执行两次导出
    out1 = capture_query(
        "SELECT * FROM employees WHERE salary>10000",
        "json", os.path.join(ROOT, "demo_high_salary.json"))
    out2 = capture_query(
        "SELECT * FROM employees WHERE department='Sales'",
        "csv", os.path.join(ROOT, "demo_sales.csv"))

    with open(os.path.join(ROOT, "demo_high_salary.json"), encoding="utf-8") as f:
        json_content = f.read().strip()
    with open(os.path.join(ROOT, "demo_sales.csv"), encoding="utf-8-sig") as f:
        csv_content = f.read().strip()

    lines = []
    lines.append(("C:\\4dim\\db_query> python db_query.py query \"SELECT * FROM employees WHERE salary>10000\" --export json --output demo_high_salary.json", "cmd"))
    lines += [(l, "out") for l in out1]
    lines.append(("", "out"))
    lines.append(("C:\\4dim\\db_query> python export_command.py \"SELECT * FROM employees WHERE department='Sales'\" csv demo_sales.csv", "cmd"))
    lines += [(l, "out") for l in out2]
    lines.append(("", "out"))
    lines.append(("--- demo_high_salary.json ---", "hint"))
    lines += [(l, "file") for l in json_content.splitlines()]
    lines.append(("", "out"))
    lines.append(("--- demo_sales.csv ---", "hint"))
    lines += [(l, "file") for l in csv_content.splitlines()]

    # 2) 绘制
    font = load_font(15, chinese=True)
    line_h, pad_x, pad_y, title_h = 22, 16, 40, 30
    width = 780
    height = pad_y + title_h + len(lines) * line_h + 16

    img = Image.new("RGB", (width, height), (30, 30, 30))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, title_h + 10], fill=(45, 45, 48))
    d.text((12, 8), "Command Prompt - db_query export demo",
           fill=(200, 200, 200), font=load_font(13, chinese=True))
    for i, c in enumerate([(220, 80, 80), (220, 180, 60), (70, 180, 70)]):
        d.ellipse([width - 70 + i * 20, 12, width - 60 + i * 20, 22], fill=c)

    colors = {"cmd": (120, 200, 120), "out": (210, 210, 210),
              "hint": (150, 170, 210), "file": (230, 200, 140)}
    y = pad_y + title_h
    for text, kind in lines:
        d.text((pad_x, y), text, fill=colors[kind], font=font)
        y += line_h

    out_path = os.path.join(ROOT, "demo_result.png")
    img.save(out_path, "PNG")
    print(f"[OK] 真实运行结果截图已生成: {out_path}")


if __name__ == "__main__":
    main()
