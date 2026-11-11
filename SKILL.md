---
name: trademark-review
description: 中国商标注册前合规审查。输入商标名称与类别，逐条比对现行《商标法》及其实施条例、审查审理指南，给出"不得注册/条件性风险/风险分级"结论、法条原文依据、以及必须人工确认的清单。不绑定商标数据源，可接入任意查询接口。适用于品牌命名预筛、批量候选评估、申请前风险自查。
origin: Custom
version: 1.3.3
---

# 商标合规审查

> 结论先给"能不能注册、卡在哪一条法"，再给依据原文；不给没有数据支撑的虚假成功率。

## 何时使用

用户提到以下场景时使用：

- "这个商标能注册吗 / 帮我查一下商标 / 评估注册成功率"
- "帮我筛一下这几个品牌名"（一次给多个候选）
- "申请前先自查一下"
- 需要一份带法条依据的商标预审报告（Word）

不适用：图形商标近似判断、商标交易估值、侵权诉讼分析。

## 核心约定（必须遵守）

1. **法条引用只从 `references/article_map.json` 取**，不得凭记忆写条号。
2. **禁用标志分两档**：整体即国家名称、国家象征、欺骗性标志 = 不得注册（不参与打分，不给成功率）；仅含国家名称、政治敏感词、民族宗教元素、县级以上地名 = 条件性风险（需人工确认）。
3. **未配置商标数据源时，先在先商标检索状态为"未检索"**，不得输出"未发现冲突"。
4. **成功率是启发式估算**，必须标注"非统计"；未做在先检索时上限 80%；结论未决（含国家名称待判断例外）时不给数字。
5. **法规版本**：默认按现行有效的 **2019 年修正版** 出结论，括号并列标注 2026 年修订版条号；2026 版自 2027-01-01 施行。

## 快速执行

```bash
# 单个商标
python scripts/review.py "云图智能" --class 9,42

# 多个候选（批量对比）
python scripts/review.py "云图智能" "智图云" "图智云" --class 9,42

# 生成 Word 报告
python scripts/review.py "云图智能" --class 9,42 --report --format docx

# 按 2026 修订版条号出结论
python scripts/review.py "云图智能" --class 9 --law-version 2026
```

工作目录：本 skill 根目录（脚本用相对路径定位 `references/`，不依赖任何个人绝对路径）。

## 审查流程

```
输入：商标名称 + 尼斯类别（未给类别时用 config 默认 [9,35,42]）

1. 禁用标志审查
   - 国家名称/国家象征 → 不得注册
   - 欺骗性词汇 → 不得注册
   - 县级以上地名 → 条件性风险（需确认是否有其他含义）
   依据：article_map → national_name / misleading / geographic_name

2. 显著特征审查
   - 按类别的通用名称（尼斯分类 1-45 类内置）
   - 描述性词汇
   - 整体由通用/描述词构成 → 高风险（缺乏显著特征）
   依据：article_map → distinctiveness_generic / _descriptive / _lack

3. 在先商标检索（需数据源）
   - config.yaml → trademark_review.api.adapter_class
   - 未配置 → 状态 not_configured，结论标注"不含冲突判断"
   - 接口异常 → 状态 error，原样暴露错误

4. 结论
   - 不得注册 / 高风险（缺乏显著特征）/ 条件性风险（需人工确认）/ 高·中·低风险
   - 附结论边界（哪些检查没做）
```

## 输出示例

```
商标名称: 北京烤鸭
审查依据: 2019年修正（2019-11-01 施行）
结论: 条件性风险（需人工确认）
预估成功率: 55%（启发式估算，非统计）
建议: 含地名，须确认其是否具有其他含义；无其他含义则不得注册。

逐项结果:
  ❌ 禁用标志: 1 项
     - 含有县级以上行政区划名称
       依据: 《商标法》（2019年修正）第十条第二款〔2026年修订：第十六条〕
  ✅ 显著特征: 未发现规则层问题
  ⚠️  在先商标: 未检索（未配置数据源）
      → 本结论不含在先商标冲突判断
```

## 接入商标数据源

实现 `references/trademark_api_adapter.py` 中的 `TrademarkAPIAdapter.search_similar()`，
然后在 `config.yaml` 配置类路径：

```yaml
trademark_review:
  api:
    adapter_class: "my_package.MyAdapter"   # 未配置则不检索，不会返回虚构数据
```

API 密钥通过环境变量 `TRADEMARK_API_KEY` 注入，不写进配置文件。
演示可用 `references.trademark_api_adapter.MockTrademarkAPI`，但必须显式配置。

## 失败模式与处理

| 现象 | 含义 | 处理 |
|---|---|---|
| `在先商标: 未检索（未配置数据源）` | 没接数据源 | 结论不含冲突判断，需另行专业检索 |
| `在先商标: 检索失败（...）` | 接口或网络异常 | 原样暴露错误，不重试超过 1 次 |
| `未登记条号: xxx` | article_map 缺映射 | 补 `references/article_map.json`，不要在代码里硬编码 |
| Word 报告生成失败 | 缺 python-docx | `pip install python-docx` |
| PDF 生成失败 | 缺 docx2pdf 或本机无 Word | 自动回退为 Word 版本 |

## 安全边界

- 不访问网络（除非用户配置了数据源或启用 AI 分析）
- 不写入、不删除除输出报告外的任何文件
- 不发送任何数据到外部服务；AI 分析默认关闭，开启后仅发送商标名称与类别
- 报告为技术性预筛，不构成法律意见

## 文件结构

```
SKILL.md                     本文件
README.md                    用户文档
config.yaml                  配置（版本、阈值、数据源、AI）
scripts/review.py            审查引擎（结论 + 法条引用）
scripts/report_generator.py  Word/JSON 报告
scripts/ai_analyzer.py       可选 AI 分析（默认关闭）
references/article_map.json  条号映射（唯一事实来源）
references/risk_rules.json   关键词库 + 尼斯分类 1-45 类通用名称
references/geographic_names.json  全国 34 省级 / 333 地级 / 2942 县级地名
references/trademark_api_adapter.py  数据源适配器接口
references/laws/             法规原文
  trademark_law_2019.md        现行有效
  trademark_law_2026.md        2027-01-01 施行
  trademark_regulation_2014.md 实施条例
  collective_certification_2024.md 集体/证明商标规定
  examination_guideline_2021.md 审查审理指南（43 章结构化全文）
tests/test_review.py         25 个回归测试
scripts/verify.sh            三层验证（l0/l1/l2）
```

## 能力边界（必须向用户如实说明）

- 仅文字商标；图形、声音、三维、动态标志不支持
- 通用名称库覆盖 1-45 类，但每类仅收录常见通用名称，非穷举
- 地名库覆盖 34 省级 / 333 地级 / 2942 县级；"是否具有其他含义"仍需人工判断
- 近似判断依赖外部数据源的质量与召回
- 审查指南为结构化转录，正式引用建议回查官方 PDF
