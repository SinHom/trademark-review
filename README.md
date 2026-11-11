# trademark-review

> 品牌名提交注册前，先花 10 秒知道它卡在哪一条法。

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-12%2F12%20passing-brightgreen)](tests/test_review.py)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Law](https://img.shields.io/badge/依据-商标法2019现行版%20%7C%202026版并列标注-informational)](references/article_map.json)

输入一个商标名和类别，输出的是：**能不能注册、卡在哪一条法、依据原文是什么、哪些必须人工确认**。

它不猜成功率，也不假装检索过在先商标——没做的事会明确写"未检索"。

---

## 你什么时候需要它

1. **品牌命名阶段**：手上有 5 个候选名，想知道哪几个连提交都不用提交。
2. **申请前自查**：代理机构报价前，先自己过一遍禁用条款和显著性问题。
3. **内部合规预审**：市场部要用的名字，法务需要一个可留档的书面结论。

## 它会交付什么

```text
商标名称: 北京烤鸭
审查依据: 2019年修正（2019-11-01 施行）
结论: 条件性风险（需人工确认）
预估成功率: 55%（启发式估算，非统计）

逐项结果:
  ❌ 禁用标志: 1 项
     - 含有县级以上行政区划名称
       依据: 《商标法》（2019年修正）第十条第二款〔2026年修订：第十六条〕
  ✅ 显著特征: 未发现规则层问题
  ⚠️  在先商标: 未检索（未配置数据源）
      → 本结论不含在先商标冲突判断
```

加 `--report --format docx` 生成 Word 报告：结论摘要表、逐条法条依据、结论边界、免责声明。

## 快速开始

```bash
git clone https://github.com/SinHom/trademark-review.git
cd trademark-review
pip install -r requirements.txt

python scripts/review.py "云图智能" --class 9,42
python scripts/review.py "北京烤鸭" --class 30
python scripts/review.py "云图智能" --class 9,42 --report --format docx
```

无个人路径依赖、无数据库、无必填密钥。未配置数据源时，在先商标一栏会显示"未检索"。

## 触发方式

在 Claude Code / Codex / OpenCode / OpenClaw 等支持 Skill 的 runtime 中，直接说：

- "帮我查一下「云图智能」这个商标能不能注册，类别 9 和 42"
- "这几个品牌名帮我筛一下：云图智能、智图云、图智云"
- "申请前先自查一下，出个报告"
- "这个商标有没有违反禁用条款"
- "苹果在第31类能注册吗"

非 Claude 环境直接调用 CLI 即可，功能完全一致。

## 它和同类有什么不同

| | 本工具 | chktm | W0ff/trademark-tools | 商业代理机构 |
|---|---|---|---|---|
| 数据源 | **可插拔，随你接** | USPTO 全量本地库 | Serper + 网页 | 官方系统 |
| 法条依据 | **逐条映射 + 条文原文** | 无 | 评分因子 | 人工判断 |
| 中国商标法 | **是** | 否（美国） | 否（美国为主） | 是 |
| 在先商标 | 依赖你接的数据源 | 内置 | 网页检索 | 官方检索 |
| 结论形式 | 不得注册 / 条件性 / 分级 | HIGH/MEDIUM/LOW | 威胁评分 | 专业意见 |
| 费用 | 开源 | 开源 | 开源 | 按件收费 |

不吹"替代代理机构"。它做的是把明显不合规的名字挡在提交之前。

## 安全边界

- 默认**不联网**；只有你配置了商标数据源或显式开启 AI 分析才发起网络请求
- 不删除、不修改任何业务文件，只写你指定的报告路径
- 不收集、不上传商标名称以外的任何信息
- AI 分析默认关闭；开启后仅发送商标名称与类别到你所选的大模型服务
- 报告是技术性预筛，**不构成法律意见**

## 文件结构

```
scripts/review.py                 审查引擎：结论分级 + 法条引用
scripts/report_generator.py       Word / JSON 报告
scripts/ai_analyzer.py            可选 AI 分析（默认关闭）
references/article_map.json       2019↔2026 条号映射（唯一事实来源）
references/risk_rules.json        关键词库 + 23 个类别的通用名称
references/trademark_api_adapter.py  数据源接口（不内置任何商业 API）
references/laws/
  trademark_law_2019.md           现行有效（2019-11-01 施行）
  trademark_law_2026.md           2027-01-01 施行（并列标注用）
  trademark_regulation_2014.md    商标法实施条例
  collective_certification_2024.md 集体商标、证明商标规定
  examination_guideline_2021.md   商标审查审理指南（OCR 全文，28.6 万字）
tests/test_review.py              12 个回归测试
```

## 验证与测试

```bash
python tests/test_review.py
```

覆盖：条号与法规原文一致性、禁用条款硬阻断、地名条件性风险、描述性/通用名称、
未配置数据源的诚实标注、跳过检索的声明、CLI 直跑、批量、Word 报告。

关键回归门（改代码必须保持）：

| 输入 | 必须得到 |
|---|---|
| 中国制造 / 9 类 | 不得注册，成功率"不适用" |
| 特供产品 / 35 类 | 不得注册，条号含"第十五条第一款第八项" |
| 北京烤鸭 / 30 类 | 条件性风险，不是低风险 |
| 苹果 / 31 类 | 高风险（缺乏显著特征） |
| 苹果 / 9 类 | 不触发通用名称误报 |
| 未配置数据源的任意名 | 在先商标显示"未检索"，且不出现任何近似商标 |

## 已知边界

- 仅文字商标；图形、声音、三维、动态标志不支持
- 通用名称库覆盖 23 个常用类别，不是全部 45 类
- 地名库为省级 + 主要地级市，未覆盖全部县级地名
- 近似判断的质量取决于你接入的数据源
- 审查审理指南为 OCR 文本，存在形近字误识；对外引用以官方 PDF 为准
- 成功率是启发式估算，没有统计样本支撑

## 法规版本

默认按 **2019 年修正版**（现行有效）出结论，括号内并列标注 **2026 年修订版** 条号。
2026 版自 **2027-01-01** 起施行，届时用 `--law-version 2026` 切换。

## License

MIT
