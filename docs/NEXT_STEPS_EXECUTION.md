# Next Steps (Execution)

## 已确认执行顺序
1. 完善版本控制边界（.gitignore）
2. 报告流水线后写回推送状态（`finalize_push_state.py`）
3. 接入真实推送动作（基于 OpenClaw 渠道）
4. 增加重试队列消费（失败后补发）
5. 云端部署（cron/systemd + missed_run_recovery）

## 当前状态
- 1、2、3、4 已落地（通过 webhook 推送与重试队列）
- 5 待迁移到云服务器时实施

## 环境变量
- `FEISHU_WEBHOOK_URL` 或 `FEISHU_BOT_WEBHOOK`
- 未设置时：自动进入重试队列，不会中断流水线
