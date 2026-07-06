# 整改项跟踪清单

## 🔴 高优先级

### 1. 完善合规检查（16+ 项）
- [ ] 迁移原项目 16 项检查逻辑
- [ ] 适配新的 SPI 接口
- [ ] 添加单元测试

### 2. 真实数据源适配器
- [ ] 实现真实 tushare API 调用
- [ ] 迁移 cninfo 适配器
- [ ] 添加 bibigpt 适配器

### 3. Temporal Workflow 编排
- [ ] docker-compose 搭建 Temporal Server
- [ ] 实现 ArticleProductionWorkflow
- [ ] 支持断点续跑、重试、人工审批
- [ ] Worker 多实例部署

## 🟡 中优先级

### 4. 多编辑风格扩展
- [ ] 实现 xi-li-pai（犀利派）
- [ ] 实现 shu-ju-pai（数据派）
- [ ] 风格指纹学习机制

### 5. 多租户数据隔离
- [ ] PostgreSQL 持久化
- [ ] Schema 级别租户隔离
- [ ] 租户配额和限流

### 6. 可观测性
- [ ] OpenTelemetry 全链路追踪
- [ ] Prometheus 指标暴露
- [ ] Grafana 监控面板

## 🟢 低优先级

### 7. CLI 改造
- [ ] 基于新 API 重写 CLI
- [ ] 支持 run create/list/status 命令

### 8. Web UI 管理后台
- [ ] 工作流可视化
- [ ] 租户管理
- [ ] 编辑风格配置

### 9. 旧代码清理
- [ ] 验证新架构覆盖旧功能
- [ ] 删除 src/ 和 scripts/
- [ ] 更新文档

### 10. A/B 测试和数据回流
- [ ] 多编辑并行产出
- [ ] 发布数据回流
- [ ] 风格优化反馈闭环

## 进度统计
- 总项数：10
- 已完成：3（#1 合规检查、#4 多编辑风格、#7 CLI 改造）
- 进行中：0
- 待开始：7
