# content-factory Examples

每个示例都可直接 `uv run python examples/<name>.py` 运行,无需任何 API token(token 缺失时自动降级 mock)。

| 示例 | 演示什么 | 命令 |
|---|---|---|
| `quickstart_e2e.py` | 一键跑完整流水线:discover_topics → research → write → compliance → publish | `uv run python examples/quickstart_e2e.py` |
| `ab_test_run.py` | A/B 测试:严肃派 vs 犀利派 并行产出同一选题,展示 `parallel_draft` 用法 | `uv run python examples/ab_test_run.py` |
| `compliance_strict_demo.py` | 合规检查阻断演示:展示一篇缺 frontmatter 的草稿被 FAIL 拒绝 | `uv run python examples/compliance_strict_demo.py` |
| `multi_tenant_demo.py` | 多租户数据隔离:两个租户的运行记录完全分离 | `uv run python examples/multi_tenant_demo.py` |
| `data_source_fallback.py` | 数据源 fallback 演示:无 token 也能跑,但实时 token 让数据更准 | `uv run python examples/data_source_fallback.py` |

## 公共约定

- 所有示例都从 `discover_components()` 拿组件,不直接 import 适配器
- 任何外部依赖缺失(`httpx` / `fastapi` / `tushare` / `temporalio`)时优雅降级到 mock,不会报错
- 想接真实数据,把对应 token 写进 shell 环境变量(`CF_TUSHARE_TOKEN` / `CF_WECHAT_APPID` 等),样例见 [`.env.example`](../.env.example)
