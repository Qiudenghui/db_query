# 功能说明：数据导出（FEATURE_EXPORT）

> 训练营第一次作业 · 为"智能数据库查询工具"新增数据导出功能模块
> 学员：__________  提交日期：2026-08-19

---

## 一、功能概述

在原有"智能数据库查询工具"（基于 Python + SQLite 的命令行工具）基础上，新增
**数据导出功能模块**。用户执行 SQL 查询后，可将结果导出为 **CSV** 与 **JSON**
两种格式；并通过自动化命令实现"查询 + 导出"一键完成。

交付文件：
- `db_query.py`：查询工具核心（查询 + 导出 + 交互式主动询问）
- `export_command.py`：一键查询并导出的自动化命令入口
- `.claude/commands/export-query.md`：Claude Code 自定义 Command 定义
- 本文件 `FEATURE_EXPORT.md`

---

## 二、功能要求对照

| 作业要求 | 实现方式 |
| --- | --- |
| 导出格式支持 CSV / JSON | `export_csv()` / `export_json()`，通过 `EXPORTERS` 字典统一调度 |
| 自动化流程（一键 / 命令触发） | `export_command.py` + Claude Code 自定义 Command `export-query` |
| 用户交互（AI 主动询问导出） | 交互模式下查询后询问 `csv/json/n`；缺格式时 Agent 主动追问 |

---

## 三、代码库理解与扩展（切入点）

原工具只负责"执行 SQL 并返回打印结果"。我的扩展切入点是：

1. 新增 `QueryResult` 数据类，把 `cursor.description`（列名）与 `fetchall()`（行）
   封装成一个可流转的对象——这是导出模块与查询模块之间的**干净接口**。
2. 新增 `export_csv` / `export_json` 两个纯函数，接收 `QueryResult`、输出路径，
   返回绝对路径。导出逻辑与查询逻辑解耦，便于单测与复用。
3. 在交互循环 `interactive()` 中，查询成功后插入"主动询问是否导出"分支——这就是
   作业要求的"AI 助手主动询问"落地位置。

关键代码（`db_query.py`）：

```python
@dataclass
class QueryResult:
    columns: list[str]
    rows: list[tuple[Any, ...]]

    def to_dicts(self) -> list[dict[str, Any]]:
        return [dict(zip(self.columns, row)) for row in self.rows]
```

```python
EXPORTERS = {"csv": export_csv, "json": export_json}

def export_result(result, fmt, output=None):
    fmt = fmt.lower()
    if fmt not in EXPORTERS:
        raise ValueError(...)
    if not output:
        output = f"export_{result.count}rows.{fmt}"
    return EXPORTERS[fmt](result, output)
```

---

## 四、AI Agent 任务分解实践

在 Claude Code 中，把"导出数据"这一复杂任务分解为若干子任务，观察 Agent 如何协调：

### 子任务拆解
1. **获取查询结果**：调用 `run_query(conn, sql)` → 得到 `QueryResult`
2. **格式化数据**：
   - CSV：`csv.writer` 写表头 + 行，`utf-8-sig` 编码保证 Excel 中文不乱码
   - JSON：`to_dicts()` → `json.dump(..., ensure_ascii=False, indent=2)`
3. **创建文件**：`open()` 写入磁盘，返回绝对路径

### Agent 协调要点（写在 `export-query.md` 中）
- 参数已齐备 → 直接 `python export_command.py "<SQL>" <fmt> [path]`
- 只给 SQL 没给格式 → **Agent 主动追问** csv 还是 json（对应作业"用户交互"点）
- SQL 语法错误 → 捕获 `sqlite3.Error`，提示并给修改建议，不中断流程

我在实际操作 Claude Code 时观察到：Agent 会先确认参数完整性，再选择导出器，
最后回显文件路径——这与上面的人工任务分解一致，验证了"把复杂任务拆成
可协调子任务"的方法是可行的。

---

## 五、工具链整合思考

| 工具 | 优势 | 在本项目中的角色 |
| --- | --- | --- |
| **Cursor** | 快速迭代、代码生成 | 用其根据注释/需求快速生成 `export_csv`/`export_json` 函数骨架 |
| **Claude Code** | 多步骤自动化、Command | 用 `/export-query` Command 把"查询+导出"固化为一键流程，并承担交互追问 |

**结合方式**：先用 Cursor 快速把导出函数写出来、跑通单测；再用 Claude Code 的
自定义 Command 把"查询→格式化→落盘"串成可复用的一键命令，并承担与用户的交互
（主动询问格式）。两者互补：Cursor 负责"写得快"，Claude Code 负责"串得顺"。

---

## 六、使用示例

```bash
# 1) 交互模式（查询后工具主动询问是否导出）
python db_query.py
SQL> SELECT * FROM employees WHERE department='Engineering'
# 返回 2 行 ...
# 需要将这次查询结果导出为 CSV 或 JSON 文件吗？(csv/json/n): csv
# ✅ 已导出到: e:\4dim\db_query\export_2rows.csv

# 2) 命令行直接查询并导出（一键）
python db_query.py query "SELECT * FROM employees WHERE salary>10000" --export json --output high_salary.json

# 3) 自动化命令入口（等价于上面的简化版）
python export_command.py "SELECT * FROM departments" csv depts.csv

# 4) Claude Code 自定义命令
/export-query SELECT * FROM employees json
```

---

## 七、提交说明

- 代码已推送至 Gitee / GitHub（见任学堂提交链接）
- 结果截图见提交附件
- 本仓库可独立运行，无需外部数据库（内置 `demo.db` 示例数据）
