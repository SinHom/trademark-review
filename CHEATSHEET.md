# 商标审查 Skill - 快速参考卡片

## 🚀 一分钟上手

```bash
# 进入目录
cd ~/.claude/skills/trademark-review

# 安装依赖（首次使用）
pip install PyYAML python-docx

# 审查单个商标
python scripts/review.py "云图智能" --class 9,42 --skip-similarity

# 生成Word报告
python scripts/review.py "云图智能" --report --format docx
```

## 📋 常用命令

### 基础审查

```bash
# 单个商标
python scripts/review.py "商标名称"

# 指定类别
python scripts/review.py "商标名称" --class 9,35,42

# 跳过近似性检索（无API时）
python scripts/review.py "商标名称" --skip-similarity
```

### 批量处理

```bash
# 命令行批量
python scripts/review.py "商标A" "商标B" "商标C" --class 9,42

# 文件批量
python scripts/review.py --batch trademarks.txt --class 9,42

# 批量生成报告
python scripts/review.py --batch trademarks.txt --report
```

### 报告生成

```bash
# Word报告
python scripts/review.py "商标" --report --format docx

# JSON输出
python scripts/review.py "商标" --output result.json

# 指定输出路径
python scripts/review.py "商标" --report --output ~/report.docx
```

## 📊 审查维度

| 维度 | 法律依据 | 检查内容 |
|-----|---------|---------|
| **禁用条款** | 商标法第十条 | 政治敏感、地名、误导性 |
| **显著性** | 商标法第十一条 | 通用名称、描述性 |
| **近似性** | 商标法第三十条 | 在先商标冲突 |

## 🎯 风险等级

| 等级 | 成功率 | 说明 |
|-----|--------|------|
| 🟢 **低风险** | >60% | 可以注册 |
| 🟡 **中风险** | 40-60% | 建议修改 |
| 🔴 **高风险** | <40% | 不建议注册 |

## 🔌 接入自己的API

### 1. 创建适配器

```python
# my_api.py
from references.trademark_api_adapter import TrademarkAPIAdapter

class MyAPI(TrademarkAPIAdapter):
    def search_similar(self, trademark_name, classes):
        # 调用你的API
        return results
```

### 2. 配置

```yaml
# config.yaml
trademark_review:
  api:
    adapter_class: "my_api.MyAPI"
```

```bash
# 环境变量
export TRADEMARK_API_KEY="your_key"
```

### 3. 使用

```bash
python scripts/review.py "商标" --class 9,42
# 自动使用你的API
```

## 📁 文件路径

```
~/.claude/skills/trademark-review/
├── scripts/review.py          # 主脚本
├── config.yaml                # 配置文件
├── references/
│   ├── laws/                  # 法规文档
│   └── trademark_api_adapter.py  # API接口
└── [文档].md                  # 各种文档
```

## 💡 常见问题

### Q: 提示 "未配置商标查询API"

**A**: 使用 `--skip-similarity` 跳过近似性检索

### Q: 报告生成失败

**A**: 安装依赖 `pip install python-docx`

### Q: 找不到yaml模块

**A**: 安装依赖 `pip install PyYAML`

## 📚 完整文档

- **快速开始**: `QUICKSTART.md`
- **用户手册**: `README.md`
- **技术文档**: `DOCUMENTATION.md`
- **安装指南**: `INSTALL.md`

## 🎓 商标类别参考

| 类别 | 说明 | 示例 |
|-----|------|------|
| 9 | 计算机软件、电子设备 | App、软件 |
| 35 | 广告、商业管理 | 电商、广告 |
| 38 | 通讯服务 | 即时通讯 |
| 42 | 科技服务、软件开发 | SaaS、云服务 |

完整45类参考: http://sbj.cnipa.gov.cn/

## ⚠️ 重要提示

✅ **适合**: 品牌筛选、批量评估、内部预审  
❌ **不适合**: 替代专业检索、法律依据、正式报告

**免责**: 本工具仅供参考，不构成法律意见。重要决策请咨询专业机构。

---

**Skill版本**: v1.0.0  
**更新日期**: 2026-10-28
