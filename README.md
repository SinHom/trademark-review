# trademark-review

> 提交商标注册前，先花 10 秒知道它卡在哪一条法——以及哪些事这个工具**没有**查。

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![verify](https://github.com/SinHom/trademark-review/actions/workflows/verify.yml/badge.svg)](https://github.com/SinHom/trademark-review/actions/workflows/verify.yml)
[![Tests](https://img.shields.io/badge/tests-25%2F25-brightgreen)](tests/test_review.py)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Law](https://img.shields.io/badge/依据-商标法2019现行版%20%7C%202026版并列标注-informational)](references/article_map.json)

输入商标名和类别，输出四件事：**能不能注册、卡在哪一条法、依据原文是什么、哪些必须人工确认**。

它不猜成功率，不假装检索过在先商标，也不会把"含中国"一律判成不得注册——
没做的事会明确写"未执行"，模棱两可的事会说"需确认"而不是编一个分数。

## 30 秒看到结果

```bash
git clone https://github.com/SinHom/trademark-review.git && cd trademark-review
pip install -r requirements.txt
python scripts/review.py "北京烤鸭" --class 30
```

真实输出（`examples/case-02-geographic.txt`，未编辑）：

```text
结论: 条件性风险（需人工确认）
预估成功率: 55%（启发式估算，非统计）

逐项结果:
  ❌ 禁用标志: 1 项
     - 含有省级行政区名称「北京」
       依据: 《商标法》（2019年修正）第十条第二款〔2026年修订：第十六条〕
  ✅ 显著特征: 未发现规则层问题
  ⚠️  在先商标: 未检索（未配置数据源）

📋 本次检查范围:
  ✅ 禁用标志（国家名称/国家象征/欺骗性/政治敏感/民族宗教）
  ✅ 显著性（描述性词汇、尼斯分类 1-45 类通用名称）
  ✅ 县级以上行政区划地名（省级/地级/县级）
  ⛔ 在先商标近似检索：未执行（未配置数据源）
  ⛔ 图形、声音、三维、动态商标
  ⛔ 跨类别近似与类似商品/服务判定

🗂  规则库: v2.1.0（更新于 2026-11-11），条号映射截至 2026-11-11
```

五个典型案例的完整输出在 [`examples/`](examples/)，由 `bash scripts/demo.sh` 一键重放。

## 为什么值得装，而不是直接问 Agent

直接问大模型"这个商标能不能注册"，你会得到一段读起来很顺、条号经常编错的回答。
这个工具的价值在**可复核**：

| | 直接问 Agent | 本工具 |
|---|---|---|
| 条号来源 | 模型记忆，会编 | `article_map.json` 单一事实来源，测试校验条号能在法规原文中定位 |
| 同一输入 | 每次可能不同 | 确定性输出，可 diff、可留档 |
| 检索了什么 | 说不清 | 报告里逐条列出"已执行 / 未执行" |
| 法规版本 | 可能混淆 | 2019 现行版出结论，括号并列 2026 修订版条号 |
| 离线 | 不能 | 完全离线，规则与法规原文都在仓库里 |

## 触发方式

在 Claude Code / Codex / OpenCode / OpenClaw 等支持 Skill 的 runtime 中，直接说：

- "帮我查一下「云图智能」这个商标能不能注册，类别 9 和 42"
- "这几个品牌名帮我筛一下：云图智能、智图云、图智云"
- "申请前先自查一下，出个报告"
- "这个商标有没有违反禁用条款"
- "苹果在第31类能注册吗"

非 Claude 环境直接调用 CLI 即可，功能完全一致。

## 它和同类有什么不同

| | 本工具 | cat-xierluo/trademark-assistant | nickschuetz/chktm | jordanteague/TMrex | W0ff/trademark-tools |
|---|---|---|---|---|---|
| 法域 | 中国 | 中国 | 美国 | 美国 | 未限定 |
| 法条依据 | **逐条映射 + 条文原文入库** | 依赖指南摘要 | 无 | DuPont 因素说明 | 无 |
| 条号双版本 | **2019 现行 / 2026 修订并列** | 提示时点，未做映射 | — | — | — |
| 在先商标 | 可插拔数据源（未配置则明示"未检索"） | 类别规划 + 初筛 | USPTO 本地全量库 | USPTO 80GB 本地库 | 网页搜索 |
| 形态 | CLI + Skill，零依赖运行 | Skill 集合 | CLI / Web / MCP | Skill + Python | 插件三件套 |
| 输出 | 结论 + 条号 + 检查范围清单 | 报告 | HIGH/MEDIUM/LOW | 报告 | 报告 |
| 公开活跃度 | 新 | 126 安装 / 788 star | 2 star | 12 star | 0 star，已停更 |

不吹"替代代理机构"。它做的是把明显不合规的名字挡在提交之前，并把"没查什么"写清楚。

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
references/risk_rules.json        关键词库 + 尼斯分类 1-45 类通用名称
references/geographic_names.json  全国行政区划：34 省级 / 333 地级 / 2942 县级
references/trademark_api_adapter.py  数据源接口（不内置任何商业 API）
references/laws/
  trademark_law_2019.md           现行有效（2019-11-01 施行）
  trademark_law_2026.md           2027-01-01 施行（并列标注用）
  trademark_regulation_2014.md    商标法实施条例
  collective_certification_2024.md 集体商标、证明商标规定
  examination_guideline_2021.md   商标审查审理指南（43 章结构化全文，22.5 万字）
tests/test_review.py              25 个回归测试
scripts/verify.sh                 三层验证（l0/l1/l2）
scripts/demo.sh                   重新生成 examples/ 下全部示例产物
scripts/fetch_guideline.sh        指南全文重建
scripts/fetch_geodata.sh          行政区划库重建
examples/                         真实运行产物（case-01..05 + Word 报告）
```

## 验证与测试

```bash
bash scripts/verify.sh l0    # 语法 + JSON/YAML（秒级）
bash scripts/verify.sh l1    # 25 项回归测试
bash scripts/verify.sh l2    # 全量 + 5 个门禁 + 条号一致性 + 配置自洽 + 密钥扫描
```

覆盖：条号与法规原文一致性、禁用条款硬阻断、国家名称分档、省级/县级地名、常见词地名不误伤、
45 类通用名称覆盖、描述性/通用名称、分隔符与简繁绕过、子串重复报告、
未配置数据源的诚实标注、跳过检索的声明、空名与非法类别拒绝、CLI 直跑、批量、Word 报告。

关键回归门（改代码必须保持）：

| 输入 | 必须得到 |
|---|---|
| 中国制造 / 9 类 | 不得注册，成功率"不适用" |
| 特供产品 / 35 类 | 不得注册，条号含"第十五条第一款第八项" |
| 北京烤鸭 / 30 类 | 条件性风险，不是低风险 |
| 沙县小吃 / 43 类 | 命中县级地名"沙县" |
| 东方甄选 / 35 类 | 低风险（"东方"为常见词，仅低置信提示） |
| 苹果 / 31 类 | 高风险（缺乏显著特征） |
| 苹果 / 9 类 | 不触发通用名称误报 |
| 未配置数据源的任意名 | 在先商标显示"未检索"，且不出现任何近似商标 |

## 已知边界

- 仅文字商标；图形、声音、三维、动态标志不支持
- 通用名称库覆盖 1-45 类，但每类只收录常见通用名称，不是穷举
- 地名库覆盖 34 省级 / 333 地级 / 2942 县级；同一名称是否"具有其他含义"仍需人工判断
- 近似判断的质量取决于你接入的数据源
- 审查审理指南为结构化转录文本，已与官方 PDF 抽查核对；正式引用建议回查官方原文
- 成功率是启发式估算，没有统计样本支撑

## 法规版本

默认按 **2019 年修正版**（现行有效）出结论，括号内并列标注 **2026 年修订版** 条号。
2026 版自 **2027-01-01** 起施行，届时用 `--law-version 2026` 切换。

## License

MIT
