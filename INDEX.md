# 商标审查 Skill - 文档索引

## 📚 快速导航

### 🚀 新手入门（5分钟）

1. **安装**: 先看 [`INSTALL.md`](INSTALL.md) - 3步完成安装
2. **快速开始**: 再看 [`QUICKSTART.md`](QUICKSTART.md) - 学会基本用法
3. **速查**: 最后看 [`CHEATSHEET.md`](CHEATSHEET.md) - 常用命令卡片

### 📖 用户文档

- [`README.md`](README.md) - **完整用户手册**（20页）
  - 功能特性、使用方式、配置说明
  - 商标类别参考、批量处理
  - 常见问题解答

- [`QUICKSTART.md`](QUICKSTART.md) - **快速上手指南**（5页）
  - 在Claude Code中使用
  - 接入自己的API
  - 批量处理示例

- [`CHEATSHEET.md`](CHEATSHEET.md) - **快速参考卡片**（1页）
  - 常用命令速查
  - 风险等级说明
  - 故障排查

### 🔧 技术文档

- [`SKILL.md`](SKILL.md) - **Claude Code技能定义**（15页）
  - 功能说明、何时使用
  - 审查维度详解
  - 接口适配设计
  - 报告结构

- [`DOCUMENTATION.md`](DOCUMENTATION.md) - **完整技术文档**（25页）
  - 技术架构、核心模块
  - API适配器开发指南
  - 数据模型、算法详解
  - 性能指标

- [`config.yaml`](config.yaml) - **配置文件**
  - 风险阈值、API配置
  - 报告样式、审查选项

### 📊 项目文档

- [`PROJECT_COMPLETE.md`](PROJECT_COMPLETE.md) - **项目完成报告**（12页）
  - 需求回顾、完成情况
  - 技术指标、实际效果
  - 已知限制、改进方向

- [`SUMMARY.md`](SUMMARY.md) - **项目总结**（10页）
  - 完成的工作、当前限制
  - 测试结果、改进建议

- [`DELIVERY.md`](DELIVERY.md) - **交付文档**（8页）
  - 交付内容清单
  - 验收标准、后续维护

- [`TEST.md`](TEST.md) - **测试文档**（5页）
  - 测试案例、功能验证
  - 性能测试、已知问题

- [`CHANGELOG.md`](CHANGELOG.md) - **更新日志**
  - 版本历史、新增功能
  - 修复问题、计划特性

### 🗂️ 法规文档

- [`references/laws/trademark_law_2026.md`](references/laws/trademark_law_2026.md)
  - 中华人民共和国商标法（2026年修订版）

- [`references/laws/trademark_regulation_2014.md`](references/laws/trademark_regulation_2014.md)
  - 商标法实施条例（2014年修订版）

- [`references/laws/collective_certification_2024.md`](references/laws/collective_certification_2024.md)
  - 集体商标、证明商标注册和管理规定（2024年版）

### 💻 代码文件

- [`scripts/review.py`](scripts/review.py) - **主审查脚本**（~500行）
  - 三维度审查引擎
  - 命令行接口
  - 批量处理

- [`scripts/report_generator.py`](scripts/report_generator.py) - **报告生成器**（~250行）
  - Word/PDF/JSON报告生成
  - 报告模板和样式

- [`references/trademark_api_adapter.py`](references/trademark_api_adapter.py) - **API适配器**（~220行）
  - 标准化接口定义
  - Mock实现、示例代码

- [`references/risk_rules.json`](references/risk_rules.json) - **风险规则库**
  - 禁用关键词库
  - 描述性词汇库
  - 风险权重配置

---

## 🎯 按使用场景查找

### 场景1: 我是新用户，想快速上手

1. [`INSTALL.md`](INSTALL.md) - 安装依赖
2. [`QUICKSTART.md`](QUICKSTART.md) - 运行第一个审查
3. [`CHEATSHEET.md`](CHEATSHEET.md) - 记住常用命令

### 场景2: 我想了解所有功能

1. [`README.md`](README.md) - 完整用户手册
2. [`SKILL.md`](SKILL.md) - 技能详细说明
3. [`TEST.md`](TEST.md) - 查看测试案例

### 场景3: 我要接入自己的商标查询API

1. [`DOCUMENTATION.md`](DOCUMENTATION.md) - 阅读"API适配器开发指南"章节
2. [`references/trademark_api_adapter.py`](references/trademark_api_adapter.py) - 查看接口定义
3. [`config.yaml`](config.yaml) - 配置适配器

### 场景4: 我想批量处理商标

1. [`README.md`](README.md) - 查看"批量审查"章节
2. [`QUICKSTART.md`](QUICKSTART.md) - 查看批量处理示例
3. [`CHEATSHEET.md`](CHEATSHEET.md) - 查看批量命令

### 场景5: 我想了解技术细节

1. [`DOCUMENTATION.md`](DOCUMENTATION.md) - 完整技术文档
2. [`scripts/review.py`](scripts/review.py) - 阅读源代码
3. [`SUMMARY.md`](SUMMARY.md) - 查看技术总结

### 场景6: 我遇到了问题

1. [`README.md`](README.md) - 查看"常见问题"章节
2. [`CHEATSHEET.md`](CHEATSHEET.md) - 查看"常见问题"
3. [`TEST.md`](TEST.md) - 查看"已知问题"

### 场景7: 我想学习商标法规

1. [`references/laws/trademark_law_2026.md`](references/laws/trademark_law_2026.md) - 商标法全文
2. [`references/laws/trademark_regulation_2014.md`](references/laws/trademark_regulation_2014.md) - 实施条例
3. [`SKILL.md`](SKILL.md) - 查看"审查维度"章节

---

## 📊 文档统计

| 类型 | 数量 | 总页数 |
|-----|------|--------|
| 用户文档 | 4份 | 31页 |
| 技术文档 | 4份 | 45页 |
| 项目文档 | 5份 | 45页 |
| 法规文档 | 3份 | ~150页 |
| **合计** | **16份** | **~271页** |

代码统计：
- Python代码: 973行（3个文件）
- 配置文件: 2个
- 总文件: 21个

---

## 🔍 关键词索引

- **安装**: INSTALL.md
- **快速开始**: QUICKSTART.md
- **API适配器**: DOCUMENTATION.md, trademark_api_adapter.py
- **批量处理**: README.md, QUICKSTART.md
- **报告生成**: README.md, report_generator.py
- **配置**: config.yaml, DOCUMENTATION.md
- **商标法**: references/laws/trademark_law_2026.md
- **风险规则**: risk_rules.json
- **测试**: TEST.md
- **常见问题**: README.md, CHEATSHEET.md
- **已知限制**: SUMMARY.md, PROJECT_COMPLETE.md
- **改进计划**: CHANGELOG.md, SUMMARY.md

---

## 📞 获取帮助

### 按优先级

1. **先看**: QUICKSTART.md（5分钟快速上手）
2. **再看**: README.md（完整功能说明）
3. **需要时**: DOCUMENTATION.md（技术细节）
4. **遇到问题**: CHEATSHEET.md（常见问题）

### 按问题类型

| 问题类型 | 查看文档 |
|---------|---------|
| 如何安装？ | INSTALL.md |
| 如何使用？ | QUICKSTART.md |
| 功能详解？ | README.md, SKILL.md |
| 技术细节？ | DOCUMENTATION.md |
| API开发？ | DOCUMENTATION.md |
| 遇到Bug？ | CHEATSHEET.md, TEST.md |
| 改进建议？ | CHANGELOG.md |

---

**Skill版本**: v1.0.0  
**最后更新**: 2026-10-28  
**文档总计**: 16份，~271页
