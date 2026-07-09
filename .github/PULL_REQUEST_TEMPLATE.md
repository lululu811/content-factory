## 改动说明

<!-- 简述改了什么、为什么 -->

## 关联

- Closes #(issue)
- Related to #(issue)

## 类型

- [ ] feat(新功能)
- [ ] fix(bug 修复)
- [ ] docs(文档 / 注释)
- [ ] refactor(重构,无功能变化)
- [ ] perf(性能)
- [ ] test(添加 / 完善测试)
- [ ] build / ci(构建 / CI 改动)

## 改动范围

- 涉及包:`packages/domains/<x>` / `packages/adapters/<y>` / `packages/editors/<z>` / 文档 / CI / SOP
- 公开 API 变更:是 / 否
- DB schema 变更:是 / 否
- 新增 entry point:是 / 否

## 测试

- [ ] `uv run pytest test_smoke.py` 通过
- [ ] `uv run pytest` 全量通过(包含新增 / 受影响测试)
- [ ] `uv run ruff check packages test_*.py` 0 error
- [ ] `uv run ruff format --check packages test_*.py` 0 diff
- [ ] 必要的新增测试已写(覆盖率变化趋势附后)

## 文档同步

- [ ] README.md 特性表
- [ ] docs/user-guide.md(若改了 API)
- [ ] CHANGELOG.md ## [Unreleased] 段
- [ ] packages/*/pyproject.toml version bump(若发版)
- [ ] docs/data-source-hierarchy.md(若加 / 改数据源)

## 自检

- [ ] `git status` 干净(无意外文件)
- [ ] 没有 commit `CF_*` token / 真实 access_token
- [ ] .env / drafts / publish / tracking 均 gitignored
- [ ] 新代码遵循 CONTRIBUTING.md § 提交规范(`<scope>: <subject>`)
