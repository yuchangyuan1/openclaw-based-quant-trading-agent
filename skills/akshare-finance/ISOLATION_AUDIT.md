# akshare-finance 隔离验收报告

日期：2026-03-07
安装方式：`npx clawhub@latest install akshare-finance`
来源：ClawHub

## 1) 安装结果
- 已安装到：`skills/akshare-finance`
- 当前未纳入主流程自动调用（仅候选数据源）

## 2) 静态检查（脚本层）
检查范围：`skills/akshare-finance/scripts/*.py`

已检查模式：
- `subprocess`
- `os.system`
- `eval(` / `exec(`
- `pickle`
- `socket`
- `ctypes`
- `powershell` / `cmd.exe`
- `Invoke-WebRequest` / `wget` / `curl`

结果：未发现上述高风险执行模式。

## 3) 依赖与备注
- 需安装：`akshare`、`pandas`
- 数据来源为公开网站聚合，字段口径需二次校验

## 4) 结论
- 可作为备选数据源保留。
- 若进入主链路，建议先做 3 项验收：
  1. 字段稳定性（列名、类型、缺失率）
  2. 更新频率与延迟
  3. 与 Tushare 数据交叉一致性