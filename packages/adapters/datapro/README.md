# content-factory-datapro

dataPro 专业数据检索适配器，为投研内容 AI 编辑部提供多域专业搜索能力。

## 覆盖数据域

- **学术文献** — CNKI / 万方 / 维普
- **企业工商** — 基础档案 / 股东 / 专利
- **企业风险** — 司法 / 失信 / 负面舆情
- **股票金融** — 行情 / 财务 / 指标
- **新闻资讯**

## 配置

```bash
export CF_DATAPRO_TOKEN=your-api-token
```

未设置 `CF_DATAPRO_TOKEN` 时，适配器以 **mock 模式** 运行，返回占位结果，方便本地开发与测试。
