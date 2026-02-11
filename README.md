# A股股票数据拉取程序

该仓库提供了一个可直接运行的 Python 脚本，用于：

1. 从东方财富公开接口拉取 A 股实时行情快照。
2. 将拉取结果写入 SQLite 数据库，便于后续分析。

## 环境准备

仅需 Python 3.10+（使用标准库，无需额外依赖）。

## 使用方式

```bash
python a_share_data_fetcher.py --db data/a_share_stock.db --page-size 5000
```

参数说明：

- `--db`: SQLite 数据库文件路径（默认：`data/a_share_stock.db`）
- `--page-size`: 单次拉取上限（默认：`5000`）

## 数据表结构

脚本会自动创建表 `a_share_quotes`，主要字段包含：

- `fetched_at`：拉取时间（UTC ISO 格式）
- `symbol`：股票代码
- `name`：股票名称
- `latest_price`：最新价
- `change_percent`：涨跌幅
- `change_amount`：涨跌额
- `volume`：成交量
- `turnover`：成交额
- `open_price/high_price/low_price/pre_close`：开高低昨
- `volume_ratio`：量比
- `turnover_rate`：换手率
- `pe_ratio`：市盈率

## 验证数据

```bash
sqlite3 data/a_share_stock.db 'SELECT symbol,name,latest_price,change_percent FROM a_share_quotes LIMIT 10;'
```
