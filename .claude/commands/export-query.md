---
description: 执行一条 SQL 查询并将结果一键导出为 CSV 或 JSON
argument-hint: <SQL语句> [csv|json] [输出路径]
---

# 查询并导出命令

你要帮我完成"执行查询 + 导出结果"的一键自动化流程。

## 任务分解（子任务）

请按以下顺序协调处理：

1. **获取查询结果**：使用 `db_query.py` 的 `run_query` 连接到 `demo.db`，执行用户提供的 SQL：
   `$ARGUMENTS`（第一个空格前为 SQL，可含空格；第二个 token 为格式 csv/json；第三个可选为输出路径）。

2. **格式化数据**：根据指定格式，将 `QueryResult` 转换为
   - CSV：表头 + 数据行（utf-8-sig 编码，兼容 Excel）
   - JSON：对象数组（`ensure_ascii=False` 保留中文）

3. **创建文件**：调用 `export_result()` 写入磁盘，并打印绝对路径。

## 执行方式

如果参数已齐备，直接运行：
```
python export_command.py "<SQL>" <csv|json> [输出路径]
```

如果用户只给了 SQL 没给格式，主动询问要导出为 CSV 还是 JSON。
如果 SQL 有误（sqlite3.Error），提示错误并给出修改建议，不要中断。
