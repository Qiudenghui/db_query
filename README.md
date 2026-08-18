# 智能数据库查询工具（含数据导出功能）

基于 Python + SQLite 的轻量级命令行数据库查询工具，支持将查询结果导出为
**CSV / JSON**，并可通过一键命令完成"查询 + 导出"。

## 快速开始

```bash
# 需要 Python 3.8+
python db_query.py                 # 进入交互模式
python db_query.py query "SELECT * FROM employees" --export csv --output out.csv
python export_command.py "SELECT * FROM employees" json out.json
```

内置 `demo.db`（employees / departments 两张示例表），首次运行自动初始化。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `db_query.py` | 核心：查询、CSV/JSON 导出、交互式主动询问 |
| `export_command.py` | 一键查询并导出入口 |
| `.claude/commands/export-query.md` | Claude Code 自定义 Command |
| `FEATURE_EXPORT.md` | 功能说明文档（作业交付物） |

详见 `FEATURE_EXPORT.md`。
