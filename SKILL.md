---
name: trademark-review
description: 基于中国商标法和审查条例，评估商标注册成功率，生成专业审查报告
origin: Custom
version: 1.0.0
---

# 商标注册成功率评估 Skill

根据《中华人民共和国商标法》（2026年修订）、《商标法实施条例》和《商标审查审理指南》，对商标名称进行合规性审查，评估注册成功率，并生成专业的 Word/PDF 报告。

## 核心功能

1. **法规合规性审查**：基于完整的商标法规体系进行审查
2. **多维度风险评估**：禁用条款、显著性、近似性等维度分析
3. **可插拔接口设计**：不绑定特定商标数据 API
4. **专业报告生成**：输出 Word/PDF 格式的审查报告

## 何时使用

- 企业需要评估商标注册可行性
- 品牌设计阶段的商标合规预检
- 需要批量评估多个商标候选方案
- 生成正式的商标审查分析报告

## 使用方式

### 基础用法

```bash
# 单个商标审查
/trademark-review "华为云"

# 批量审查
/trademark-review "华为云" "阿里云" "腾讯云"

# 指定商标类别
/trademark-review "华为云" --class 9,42

# 生成完整报告
/trademark-review "华为云" --report --format docx
```

### 可选参数

- `--class`：指定商标国际分类（1-45类），多个类别用逗号分隔
- `--report`：生成完整的审查报告
- `--format`：报告格式，支持 `docx`（默认）、`pdf`
- `--api-provider`：指定商标查询接口（需要自行配置）
- `--skip-similarity`：跳过近似性检索（仅做合规性分析）

## 审查维度

### 1. 禁用条款审查（《商标法》第十条）

检查商标是否违反法律禁止性规定：

- **政治性禁用**：国旗、国徽、国歌、军旗、军徽等相同或近似
- **地理标志**：县级以上行政区划地名（除非有其他含义或作为集体/证明商标）
- **民族/宗教**：带有民族歧视性、有害宗教感情的标志
- **欺骗性**：容易使公众对商品质量、特点或产地产生误认
- **不良影响**：有害社会主义道德风尚或其他不良影响

### 2. 显著性审查（《商标法》第十一条）

评估商标是否具备识别功能：

- **通用名称**：仅有商品通用名称、图形、型号
- **描述性**：仅直接表示商品质量、主要原料、功能、用途等特点
- **缺乏显著特征**：其他不具备区分来源功能的标志

### 3. 非功能性审查（《商标法》第十八条）

针对三维标志、声音、动态标志等特殊商标类型：

- 仅由商品自身性质产生的形状/声音
- 为获得技术效果而需有的形状/声音
- 使商品具有实质性价值的形状

### 4. 相同/近似审查（《商标法》第三十条、三十一条）

检索在先商标权利（需接入商标数据接口）：

- 同一商品/类似商品上的相同/近似商标
- 驰名商标保护（跨类别保护）
- 在先著作权、企业名称权等其他权利冲突

## 接口适配设计

### 为什么不写死接口？

不同场景下可用的商标查询接口不同：

- **官方接口**：国家知识产权局商标局（需要资质）
- **商业平台**：知识产权服务平台（如标库网、权大师等）
- **国际接口**：WIPO、USPTO 等国际商标数据库
- **企业内部系统**：已集成的知识产权管理系统

### 适配方式

skill 提供标准化的接口规范，由使用方自行实现：

```python
# references/trademark_api_adapter.py 中定义的接口规范

class TrademarkAPIAdapter:
    """商标查询接口适配器基类"""
    
    def search_similar(self, trademark_name: str, classes: list[int]) -> list[dict]:
        """
        查询近似商标
        
        Args:
            trademark_name: 商标名称
            classes: 商标类别列表
            
        Returns:
            [
                {
                    "name": "商标名称",
                    "registration_number": "注册号",
                    "status": "注册状态",
                    "classes": [9, 42],
                    "applicant": "申请人",
                    "similarity_score": 0.85  # 0-1之间，可选
                },
                ...
            ]
        """
        raise NotImplementedError("需要实现具体的商标查询接口")
    
    def get_trademark_detail(self, registration_number: str) -> dict:
        """获取商标详细信息（可选实现）"""
        raise NotImplementedError()
```

### 使用示例

```python
# 实现自己的适配器
from trademark_api_adapter import TrademarkAPIAdapter

class MyCompanyTrademarkAPI(TrademarkAPIAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.mycompany.com/trademark"
    
    def search_similar(self, trademark_name: str, classes: list[int]) -> list[dict]:
        # 调用公司内部或第三方接口
        response = requests.post(
            f"{self.base_url}/search",
            json={"name": trademark_name, "classes": classes},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()["results"]

# 配置到环境变量或配置文件
export TRADEMARK_API_ADAPTER=mycompany.adapters.MyCompanyTrademarkAPI
export TRADEMARK_API_KEY=your_api_key
```

## 报告结构

生成的审查报告包含以下部分：

### 1. 执行摘要

- 商标名称及类别
- 总体评估结论（高风险/中风险/低风险/可注册）
- 核心风险点摘要
- 建议措施

### 2. 法律法规合规性分析

- **禁用条款审查结果**
  - 各项禁用条款逐一比对
  - 风险等级标注
  - 法律依据引用
  
- **显著性审查结果**
  - 是否具备固有显著性
  - 是否可通过使用获得显著性
  - 改进建议

### 3. 在先权利检索结果（如已接入API）

- 相同/近似商标列表
- 相似度分析
- 驳回风险评估
- 异议风险评估

### 4. 综合评估与建议

- **注册成功率评估**：百分比估算
- **主要风险因素**：按优先级排序
- **规避方案建议**：
  - 商标修改建议
  - 类别调整建议
  - 使用策略建议
- **后续行动计划**

### 5. 附件

- 完整法律法规条款摘录
- 在先商标详细信息（如有）
- 审查依据索引

## 法律法规参考

skill 内置完整的法律法规文本（存储在 `references/laws/` 目录）：

1. **中华人民共和国商标法**（2026年修订，2027年1月1日施行）
2. **商标法实施条例**（2014年修订）
3. **商标审查审理指南**（2021年版，2022年1月1日施行）
4. **集体商标、证明商标注册和管理规定**（2024年版）

## 技术栈

- **文档处理**：`python-docx`（Word）、`reportlab`/`WeasyPrint`（PDF）
- **法律文本检索**：基于关键词和语义的混合检索
- **评分模型**：规则引擎 + 风险权重计算

## 限制与免责

1. **法律意见**：本 skill 提供的是基于法规的技术性分析，不构成法律意见
2. **实时性**：法律法规可能更新，需定期同步最新版本
3. **接口依赖**：近似性检索依赖外部商标数据接口的准确性
4. **人工复核**：重要商标注册决策应由专业知识产权代理机构复核

## 配置文件

skill 支持通过配置文件自定义行为（`config.yaml`）：

```yaml
# 商标审查配置
trademark_review:
  # 风险阈值
  risk_threshold:
    high: 0.7      # 高风险阈值
    medium: 0.4    # 中风险阈值
  
  # 默认商标类别（如未指定）
  default_classes: [9, 35, 42]
  
  # 报告配置
  report:
    language: zh-CN
    include_legal_text: true
    logo_path: null  # 可指定企业logo
  
  # API配置
  api:
    adapter_class: null  # 自定义适配器类路径
    timeout: 30
    retry: 3
  
  # 法规更新检查
  law_update_check:
    enabled: true
    check_url: "https://flk.npc.gov.cn/api/check"
```

## 维护与更新

### 法规更新流程

1. 监控国家知识产权局、全国人大法律法规数据库的更新公告
2. 下载最新版法律文本
3. 更新 `references/laws/` 目录下的文件
4. 运行 `scripts/validate_laws.py` 验证文本完整性
5. 更新 `CHANGELOG.md` 记录变更

### 已知问题

- 动态标志商标（2026年商标法新增）的审查规则尚在细化中
- 声音商标的非功能性判断需要更多案例积累

## 示例场景

### 场景1：创业公司品牌评估

```bash
# 评估3个候选商标
/trademark-review "云图智能" "智图云" "图智云" --class 9,42 --report --format pdf
```

生成包含3个商标对比分析的PDF报告，帮助选择注册成功率最高的方案。

### 场景2：已注册商标风险扫描

```bash
# 检查已注册商标是否存在被撤销风险
/trademark-review "我的品牌" --class 25 --check-invalidation-risk
```

### 场景3：批量预审

```bash
# 从文件读取商标列表批量审查
/trademark-review --batch trademarks.csv --output-dir ./reports/
```

## 开发指南

### 目录结构

```
trademark-review/
├── SKILL.md                 # 本文件
├── README.md                # 用户手册
├── config.yaml              # 配置文件
├── requirements.txt         # Python依赖
├── scripts/
│   ├── review.py           # 主审查脚本
│   ├── report_generator.py # 报告生成器
│   └── validate_laws.py    # 法规验证脚本
├── references/
│   ├── laws/               # 法律法规文本
│   │   ├── trademark_law_2026.md
│   │   ├── trademark_regulation_2014.md
│   │   ├── examination_guideline_2021.pdf
│   │   └── collective_certification_regulation_2024.md
│   ├── trademark_api_adapter.py  # API适配器接口定义
│   └── risk_rules.json     # 风险评估规则
├── templates/
│   ├── report_template.docx  # Word报告模板
│   └── report_template.html  # PDF报告模板（HTML）
└── tests/
    ├── test_compliance.py
    └── test_report.py
```

### 扩展指南

1. **添加新的审查维度**：在 `scripts/review.py` 中添加新的检查函数
2. **自定义报告样式**：修改 `templates/` 下的模板文件
3. **接入新的API**：实现 `TrademarkAPIAdapter` 接口
4. **更新法规**：替换 `references/laws/` 下的文件

## 联系与贡献

- 法规更新建议：提交 Issue 附上官方公告链接
- 功能改进：提交 PR 附上测试用例
- Bug反馈：提供商标名称、类别、错误日志

---

**最后更新**：2026-10-28  
**适用法规版本**：商标法2026修订版（2027.1.1施行）
