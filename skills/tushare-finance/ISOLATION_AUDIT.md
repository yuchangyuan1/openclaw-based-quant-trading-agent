# tushare-finance 隔离验收报告

日期：2026-03-07
安装方式：`npx clawhub@latest install tushare-finance --force`
来源：ClawHub（标记为 suspicious）

## 1) 安装结果
- 已安装到：`skills/tushare-finance`
- 当前未纳入主流程自动调用（仅隔离评估）

## 2) 静态检查（脚本层）
检查范围：`skills/tushare-finance/scripts/*.py`

已检查高风险模式：
- `subprocess`
- `os.system`
- `eval(` / `exec(`
- `pickle`
- `socket`
- `ctypes`
- `powershell` / `cmd.exe`
- `Invoke-WebRequest` / `wget` / `curl`

结果：未发现上述高风险执行模式。

## 3) 权限与依赖
- skill 声明工具：`Bash(python:*)`、`Read`
- 依赖：`tushare`、`pandas`、`openpyxl`
- 必需环境变量：`TUSHARE_TOKEN`

## 4) 运行验证
- 模块加载测试失败：当前环境未安装 `tushare`（`ModuleNotFoundError: No module named 'tushare'`）
- 结论：需在隔离 Python 环境安装依赖后再做接口联通测试。

## 5) 风险结论
- 代码层面未发现明显命令执行型恶意模式。
- 但由于来源被标记 suspicious，仍需保持隔离使用并最小权限运行。

## 6) 下一步（建议）
1. 使用独立虚拟环境安装依赖：
   - `python -m venv .venv-tushare`
   - `.venv-tushare\Scripts\pip install -r skills/tushare-finance/requirements.txt`
2. 仅配置只读数据 Token（不要复用其他敏感密钥）。
3. 先跑最小接口 smoke test（`stock_basic`、`daily`）并记录日志。
4. 通过后再接入 `market_snapshot` 生成链路。