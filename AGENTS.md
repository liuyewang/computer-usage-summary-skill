# Computer Usage Summary Skill — 项目规则

## 接续与开发

- 开发检查及按问题检索的经验见 [CONTRIBUTING.md](CONTRIBUTING.md)；恢复任务先读 [现有检查点](docs/superpowers/checkpoints/2026-11-10-computer-usage-summary-optimization.md)，再核对 Git 和外部状态。历史设计/计划是证据，不是新授权。
- 保留 `skills/computer-usage-summary/scripts/activitywatch_summary.py` 入口与兼容导出；实现位于同级 `summary_core/`，运行逻辑使用标准库（时区数据依赖见 `requirements.txt`）。

## 隐私与输出口径

- 数据边界以 [PRIVACY.md](PRIVACY.md)、[SECURITY.md](SECURITY.md) 和技能输出契约为准：仅本地 loopback ActivityWatch，禁止将真实活动数据放入仓库、测试或发布包；不把前台区间说成启动次数或连续工作。

## 发布渠道

- 提交、推送、平台更新、部署分别核对授权和结果；平台限于 Awesome Codex Plugins、HOL Registry、skills.sh、SkillsMP、LobeHub、ClawHub、Cursor Directory，不向 OpenAI 平台投稿。目录镜像交由上游 generator，不手工复制包。
