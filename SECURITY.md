# Security Policy

## 支持版本

| 版本 | 支持状态 |
|---|---|
| `1.0.x` | ✅ 完整支持(安全更新 + 兼容性修复) |
| `0.3.x` | ⚠️ 仅严重安全更新 |
| `< 0.3` | ❌ 不再支持 |

## 漏洞报告

`content-factory` 是投研类内容生产工具,**可能涉及微信公众号 access_token / 数据源 token 等敏感凭证**。如果你发现安全漏洞,请通过 [GitHub Security Advisories](https://github.com/lululu811/content-factory/security/advisories) 私下提交,**不要**在公开 issue 里披露细节。

报告应包含:

- 漏洞位置(文件路径 / 行号)
- 触发条件(请求样本 / 输入数据)
- 影响范围(数据泄露 / 越权 / RCE 等)
- 复现步骤

## 响应承诺

| 阶段 | 时间 |
|---|---|
| 初步确认 | 48 小时内 |
| 严重漏洞修复 | 30 天内(高危优先) |
| 一般漏洞修复 | 下一发布周期 |
| 漏洞公告 | 修复发布后 7 天内 |

## 已知信任边界

`content-factory` 默认在本地运行,**不直接暴露公网**。生产部署请参考 [docs/user-guide.md §生产部署](docs/user-guide.md),务必:

- 反向代理(Nginx / Caddy)套 TLS
- `CF_DATABASE_URL` 强密码 + 内网访问
- 微信公众号 AppID / Secret 走环境变量,**不**入 `.env` 提交
- `CF_TRACE_CONSOLE` 生产环境务必设为 `0`,trace 可能含 token 拼接

## 已禁用的危险操作

- ❌ `scripts/*.sh` / `bin/*.sh` 不应 `curl ... | bash` 直接跑,务必先 `cat` 一遍
- ❌ `.gitignore` 已屏蔽 `.env` / `*.local` / `drafts/` / `publish/` / `tracking/` / `logs/`,不要绕过
- ❌ 公告 PDF 文件大(单篇 100KB-5MB),仅 commit JSON 元数据,PDF 自动忽略
- ❌ 不要把真实数据源 token commit 到 `templates/` / `docs/` / `examples/`

## 致谢

重大漏洞报告者将在修复发布说明致谢(除非要求匿名)。详见 [CHANGELOG.md](CHANGELOG.md)。
