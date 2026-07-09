---
name: Bug Report
about: 报告 content-factory 的 bug · compliance 误判 / 脚本失败 / 文档错误
title: "[BUG] "
labels: bug
---

## 复现步骤

<!-- 详细描述怎么触发这个 bug -->

1. 跑了哪条命令(`uv run cf create ...`、`bin/cf-new.sh ...` ...)
2. 用了哪篇文章 / 哪个数据源
3. 期望结果是什么

## 实际结果

<!-- 错误日志 / 截图 / traceback -->

```
<paste error here>
```

## 环境

- Python 版本:`python3 --version` 结果
- content-factory 版本:`uv run python -c "import content_factory_core; print(content_factory_core.__version__)"`
- 操作系统:macOS / Linux / Windows
- 已配置的 token:`TUSHARE` / `WECHAT` / `DATABASE_URL`(哪个有就列哪个,值用 `<set>` 占位)

## 建议优先级

- [ ] Blocker(完全不能用)
- [ ] High(主流程受影响)
- [ ] Medium(边缘场景 / 文档)
- [ ] Low(typo / nicety)
