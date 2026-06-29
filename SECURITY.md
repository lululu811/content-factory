# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | ✅ 完整支持        |
| 0.3.x   | ⚠️ 仅严重安全更新 |
| < 0.3   | ❌ 不再支持        |

## Reporting a Vulnerability

**请勿在 GitHub issues 公开披露安全漏洞。**

请通过以下方式私下报告:
1. **GitHub Security Advisories**: https://github.com/lululu811/content-factory/security/advisories/new
2. **Email**: (请在 SECURITY.md 后续版本添加)

报告内容请包含:
- 漏洞类型(脚本注入 / 命令执行 / 路径遍历 / etc.)
- 受影响文件 + 行号
- 触发条件(输入示例)
- 潜在影响(数据泄露 / 代码执行 / etc.)
- 修复建议(可选)

## Response Time

- **48 小时内**确认收到
- **7 天内**评估严重性
- **30 天内**发布修复(高危漏洞优先)

## Security Considerations

### 本项目安全风险面

content-factory 是**本地工具 + 文档仓库**,不是网络服务,所以风险面有限:

1. **脚本执行风险**:`scripts/*.py / *.sh` 会在你机器上运行
   - ⚠️ 不要直接 `curl ... | bash` 跑未审计脚本
   - ✅ 跑前先 `cat` 看一下,确认无 `os.system` / `subprocess` 可疑调用

2. **数据源风险**:抓 myMCP / cninfo / TrendRadar 时
   - ⚠️ 不要把 API token 写进 frontmatter(用环境变量)
   - ✅ 内部 API token 用 `~/.bashrc` / `~/.zshrc` 注入

3. **Git 提交安全**:
   - ⚠️ 不要 commit `.env` / API key / 个人信息
   - ✅ 已有 `.gitignore` 保护(OS/Node/Python cache/secrets)

### 已知安全配置

```gitignore
# .gitignore 已保护
.env
.env.local
*.local
```

## Best Practices

### 1. 跑脚本前先看

```bash
# 总是这样:
cat scripts/<name>.py | head -50
python3 scripts/<name>.py --help
```

### 2. API token 用环境变量

```python
# 好
import os
API_TOKEN = os.environ.get('MY_API_TOKEN')

# 坏
API_TOKEN = "sk-abc123..."  # 会进 .git 历史
```

### 3. 配置文件不进 .git

```bash
# 放 ~/.config/ 不放项目里
~/.config/content-factory/config.yaml
```

### 4. 定期审计依赖

```bash
pip list --outdated
pip install --upgrade <package>
```

## Disclosure Policy

- 收到漏洞报告后,我们会先修复,再发版
- 安全公告发到 GitHub Security Advisories
- 严重漏洞会发 [GitHub Security Advisory](https://github.com/lululu811/content-factory/security/advisories)

## Acknowledgments

感谢所有负责任披露漏洞的研究者。
