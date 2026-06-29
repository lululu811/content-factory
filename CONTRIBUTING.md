# Contributing to content-factory

感谢你考虑为 **content-factory** 做出贡献!这是一套投研型公众号深度文生产流水线,基于 9 篇实战经验沉淀。

## 🎯 项目目标

让任何投研型公众号主理人(或个人投资者)都能:
- **数据精度第一** —— 从 ZsxqCrawler 原始 .md 直接读,不依赖二次总结
- **流程可执行** —— 17 步 SOP + 16 项 A1-A17b 合规检查
- **工具简单** —— 优先用 rg/jq/curl,不钻 SPA 反爬
- **可工程化** —— AI Agent 友好

## 🤝 如何贡献

### 报告 Bug

发现 SOP 错误 / 脚本 bug / 文档问题:
1. 先看 [issues](https://github.com/lululu811/content-factory/issues) 是否有重复
2. 新建 issue,标题清晰(如 "compliance-check.py A7 误判 2026/5 数据")
3. 描述:
   - 触发条件(用了哪篇文,哪条命令)
   - 期望结果
   - 实际结果
   - 错误日志 / 截图

### 提改进建议

有更好的 SOP 流程 / 新工具想法 / 数据源接入:
1. 新建 [Discussion](https://github.com/lululu811/content-factory/discussions)
2. 标签 `enhancement`
3. 描述:
   - 痛点(为什么需要)
   - 建议方案
   - 影响范围(改哪些文件)

### 提交代码

#### 改 SOP

1. 任何变动先看 [SOURCE_OF_TRUTH.md](./SOURCE_OF_TRUTH.md)
2. 改动 SOP.md 第 X 章,加 changelog 段
3. 跑 `python3 scripts/compliance-check.py --all` 确保通过
4. PR 标题:`SOP X.Y: 改 XXX`
5. PR 描述:
   - 为什么改
   - 改了什么
   - 影响哪些步骤

#### 改脚本

1. 改 `scripts/<name>.py`,遵循 PEP 8
2. 加新函数到 `compliance-check.py` 时,同步更新:
   - `templates/compliance/checklist.md`(v3 唯一权威)
   - SOP.md 对应章节
3. PR 标题:`scripts/<name>.py: <改动>`
4. PR 描述:
   - 触发场景
   - 改动详情
   - 测试方式

#### 加新数据源

1. 更新 `docs/data-source-hierarchy.md`(3 类层级)
2. 更新 SOP.md 对应章节(4.1 选题 / 4.2 研究)
3. 写一个 `scripts/<source>-search.py`(参考现有工具)
4. PR 标题:`data-source: 加 <name>`

## 📝 提交规范

### Commit 格式

```
<scope>: <subject>

<body>
```

- **scope**: SOP / scripts / docs / templates / data-source / 工程化清理
- **subject**: ≤ 50 字
- **body**: 为什么 / 改了什么 / BEFORE → AFTER 数字对比

**好例子**:
```
compliance-check.py:A17 软化 + A17b 新增 ZsxqCrawler 硬约束
```

**坏例子**:
```
fix bug
```

### Branch 命名

- `feat/<scope>-<short-desc>`(新功能)
- `fix/<scope>-<short-desc>`(修 bug)
- `docs/<scope>-<short-desc>`(文档)

## 🛠 开发环境

### 前置

- Python 3.11+
- ripgrep (`brew install ripgrep`)
- 可选:`mavis MCP` + `playwright MCP`(用于测试 TrendRadar 集成)

### 本地测试

```bash
# 跑所有合规检查
python3 scripts/compliance-check.py --all

# 验证 .gitignore 规则
git check-ignore -v <path>

# 验证 tracked 文件数
git ls-files | wc -l
```

## 🚫 不接受的贡献

- ❌ 主动抓取(SPA 反爬)—— 优先用订阅/RSS/web_search
- ❌ 物理删除内容 —— 工程化清理用 .gitignore 模式(本地保留)
- ❌ broad .gitignore pattern(伤及无辜)
- ❌ 跳过 compliance-check 的 PR(任何 FAIL 拒绝 merge)

## 📜 License

贡献的代码采用 [MIT License](./LICENSE) 发布。
贡献的内容(包括 SOP / 文档 / 工具)同样适用。

## 🙏 致谢

感谢所有早期试错者(包括 dbs-content-system 7 目录)—— 失败是开源的燃料。
