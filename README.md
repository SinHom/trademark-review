# 商标注册成功率评估 Skill

基于《中华人民共和国商标法》（2026年修订）及配套法规，为商标名称提供合规性审查、风险评估和专业报告生成服务。

## 快速开始

### 安装依赖

```bash
cd ~/.claude/skills/trademark-review
pip install -r requirements.txt
```

### 基础使用

```bash
# 在Claude Code中调用
/trademark-review "华为云"

# 指定类别
/trademark-review "华为云" --class 9,42

# 生成Word报告
/trademark-review "华为云" --report --format docx
```

### 直接运行脚本

```bash
# 单个商标审查
python scripts/review.py "测试商标"

# 批量审查
python scripts/review.py "商标A" "商标B" "商标C" --class 9,35,42

# 生成报告
python scripts/review.py "测试商标" --report --format docx --output report.docx
```

## 功能特性

### ✅ 完整的法规合规性审查

- **禁用条款**：政治敏感、地理标志、欺骗性等（商标法第十条）
- **显著性**：通用名称、描述性、缺乏显著特征（商标法第十一条）
- **非功能性**：特殊商标类型的功能性限制（商标法第十八条）
- **在先权利**：相同/近似商标检索（商标法第三十条、三十一条）

### 🔌 可插拔接口设计

不绑定特定商标查询API，支持：

- 官方API（国家知识产权局）
- 商业平台（标库网、权大师等）
- 企业内部系统
- 国际数据库（WIPO、USPTO）

### 📊 专业报告生成

生成包含以下内容的Word/PDF报告：

1. **执行摘要**：风险等级、预估成功率、核心建议
2. **法律合规性分析**：逐条对照法规条款
3. **在先权利检索**：相同/近似商标列表与分析
4. **综合评估**：风险因素排序、规避方案建议

### 📚 内置完整法规文本

- 中华人民共和国商标法（2026年修订，2027-01-01施行）
- 商标法实施条例（2014年修订）
- 商标审查审理指南（2021年版）
- 集体商标、证明商标注册和管理规定（2024年版）

## 配置说明

### 基础配置 (`config.yaml`)

```yaml
trademark_review:
  # 风险阈值
  risk_threshold:
    high: 0.7
    medium: 0.4
  
  # 默认类别
  default_classes: [9, 35, 42]
  
  # 报告配置
  report:
    language: zh-CN
    include_legal_text: true
  
  # API配置
  api:
    adapter_class: null  # 自定义适配器类路径
    timeout: 30
```

### 接入商标查询API

#### 1. 实现适配器

在 `references/trademark_api_adapter.py` 中查看接口规范，创建自己的适配器：

```python
from references.trademark_api_adapter import TrademarkAPIAdapter

class MyTrademarkAPI(TrademarkAPIAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.example.com"
    
    def search_similar(self, trademark_name: str, classes: list) -> list:
        # 调用你的API
        response = requests.post(
            f"{self.base_url}/search",
            json={"name": trademark_name, "classes": classes},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        # 返回标准格式
        return response.json()["results"]
```

#### 2. 配置适配器

```bash
# 方式1: 环境变量
export TRADEMARK_API_KEY="your_api_key"

# 方式2: 修改config.yaml
api:
  adapter_class: "mypackage.adapters.MyTrademarkAPI"
```

#### 3. 使用

```bash
python scripts/review.py "测试商标"
# 将自动使用配置的API进行近似性检索
```

### 跳过API检索

如果暂时没有商标查询API，可以只进行合规性分析：

```bash
python scripts/review.py "测试商标" --skip-similarity
```

## 审查维度说明

### 1. 禁用条款审查（商标法第十条）

检查是否违反绝对禁止注册的情形：

- ❌ **政治性禁用**：与国旗、国徽、军旗等相同或近似
- ❌ **地理标志**：县级以上行政区划地名（除非有其他含义）
- ❌ **民族/宗教**：带有歧视性或损害宗教感情
- ❌ **欺骗性**：容易使公众对商品产生误认
- ❌ **不良影响**：有害道德风尚

**示例**：
- "中国制造" → ❌ 含有国家名称
- "北京烤鸭" → ⚠️ 含有地名（需判断是否有其他含义）
- "特供" → ❌ 欺骗性、容易误导

### 2. 显著性审查（商标法第十一条）

评估是否具备区分来源的功能：

- ❌ **通用名称**：如"手机"用于手机
- ❌ **描述性**：如"优质"、"高级"
- ⚠️ **缺乏显著性**：过于简单或常见

**示例**：
- "苹果"用于电子产品 → ✅ 具有显著性（非商品本身）
- "苹果"用于水果 → ❌ 通用名称
- "优质茶叶" → ❌ 仅描述商品特点

**例外**：经过使用获得显著性的可以注册（需提供使用证据）

### 3. 近似性审查（商标法第三十条）

检索在先商标，评估冲突风险：

- **相同商标**：同一类别的完全相同商标
- **近似商标**：容易造成混淆的相似商标
- **驰名商标**：跨类别保护

**风险等级**：
- 高风险（相似度>0.8）：大概率被驳回
- 中风险（相似度0.6-0.8）：可能被异议
- 低风险（相似度<0.6）：冲突可能性较小

## 报告示例

### 控制台输出

```
🔍 正在审查商标: 测试商标
   类别: 9, 42
------------------------------------------------------------
1️⃣  禁用条款审查...
2️⃣  显著性审查...
3️⃣  近似性审查...

============================================================
📊 审查结果摘要
============================================================
商标名称: 测试商标
风险等级: 低风险
预估成功率: 85%
建议: 可以注册，但仍建议进行专业检索确认

详细问题:
  ✅ 禁用条款: 通过
  ✅ 显著性: 通过
  ⚠️  近似商标: 发现 3 个可能冲突的商标
============================================================
```

### Word报告结构

1. **封面**：商标审查报告标题、生成日期
2. **执行摘要**：风险等级、成功率、关键建议
3. **法律合规性分析**：
   - 禁用条款审查结果
   - 显著性审查结果
   - 法条原文引用
4. **在先权利检索**：
   - 近似商标列表（表格）
   - 相似度分析
   - 冲突风险评估
5. **综合评估与建议**：
   - 注册成功率评估
   - 风险因素分析
   - 规避方案建议
6. **免责声明**

## 命令行参数

```
usage: review.py [-h] [--class CLASSES] [--batch BATCH] [--report]
                 [--format {docx,pdf,json}] [--output OUTPUT]
                 [--config CONFIG] [--skip-similarity]
                 [trademarks ...]

商标注册成功率审查工具

positional arguments:
  trademarks            商标名称（可输入多个）

optional arguments:
  -h, --help            显示帮助信息
  --class CLASSES       商标类别，用逗号分隔，如: 9,35,42
  --batch BATCH         批量审查，从文件读取商标列表（每行一个）
  --report              生成完整报告
  --format {docx,pdf,json}
                        报告格式（默认: docx）
  --output OUTPUT       输出文件路径
  --config CONFIG       配置文件路径
  --skip-similarity     跳过近似性检索
```

## 批量审查

### 准备文件

创建 `trademarks.txt`：

```
云图智能
智图云
图智云
```

### 执行批量审查

```bash
# 批量审查并生成JSON
python scripts/review.py --batch trademarks.txt --output results.json

# 批量审查并生成报告
python scripts/review.py --batch trademarks.txt --report --format docx
```

## 商标类别参考

常用国际分类（尼斯分类）：

- **第9类**：计算机软件、电子设备
- **第35类**：广告、商业管理
- **第38类**：通讯服务
- **第41类**：教育、培训
- **第42类**：科技服务、软件开发
- **第45类**：法律服务、安全服务

完整45类分类请参考：[商标局官网](http://sbj.cnipa.gov.cn/)

## 限制与免责

### ⚠️ 重要提示

1. **非法律意见**：本工具提供技术性分析，不构成法律意见
2. **实时性限制**：法规可能更新，需定期同步最新版本
3. **接口依赖**：近似性检索准确性取决于商标数据库的完整性
4. **主观性**：商标审查存在主观判断，实际结果可能有差异

### 建议

- ✅ 用于品牌设计阶段的初步筛选
- ✅ 用于批量评估多个候选方案
- ✅ 用于内部决策参考
- ❌ 不能替代专业代理机构的正式检索
- ❌ 不能作为法律诉讼的依据

**重要商标注册建议咨询专业知识产权代理机构或律师。**

## 常见问题

### Q1: 为什么近似性检索返回空结果？

**A**: 可能原因：
1. 未配置商标查询API（使用了Mock数据）
2. API配置错误或密钥无效
3. 确实没有近似商标

检查方式：
```bash
# 查看是否有"使用Mock数据"提示
python scripts/review.py "测试商标"
```

### Q2: 如何提高审查准确性？

**A**: 
1. 接入权威商标数据库API
2. 定期更新法规文本
3. 根据实际案例调整风险规则
4. 结合人工专家复核

### Q3: 可以审查图形商标吗？

**A**: 
当前版本主要支持文字商标的合规性审查。图形商标需要：
1. 图像识别技术（OCR提取文字部分）
2. 图形相似度算法
3. 更复杂的API接口

可作为后续版本的扩展功能。

### Q4: 报告生成失败怎么办？

**A**: 
1. 确认已安装 `python-docx`：`pip install python-docx`
2. PDF生成需要额外库：`pip install docx2pdf`
3. 可以先生成JSON格式：`--format json`

### Q5: 如何更新法规文本？

**A**: 
1. 从官方渠道下载最新法规（全国人大、国家知识产权局）
2. 保存为Markdown格式
3. 替换 `references/laws/` 目录下的对应文件
4. 更新 `config.yaml` 中的版本信息

## 技术支持

### 文件结构

```
trademark-review/
├── SKILL.md                 # 技能说明（Claude Code加载）
├── README.md                # 本文件
├── config.yaml              # 配置文件
├── requirements.txt         # Python依赖
├── scripts/
│   ├── review.py           # 主审查脚本
│   ├── report_generator.py # 报告生成器
│   └── validate_laws.py    # 法规验证脚本（TODO）
├── references/
│   ├── laws/               # 法律法规文本
│   │   ├── trademark_law_2026.md
│   │   ├── trademark_regulation_2014.md
│   │   └── collective_certification_2024.md
│   ├── trademark_api_adapter.py  # API适配器接口
│   └── risk_rules.json     # 风险评估规则
├── templates/
│   └── report_template.docx  # Word报告模板（TODO）
└── tests/
    └── test_review.py      # 单元测试（TODO）
```

### 依赖库

核心依赖：
- `PyYAML`: 配置文件解析
- `python-docx`: Word文档生成
- `requests`: HTTP请求（API调用）

可选依赖：
- `docx2pdf`: PDF转换
- `pandas`: 数据处理（批量审查）
- `jinja2`: 模板渲染

### 扩展开发

#### 添加新的审查规则

编辑 `references/risk_rules.json`：

```json
{
  "prohibited_keywords": {
    "new_category": ["关键词1", "关键词2"]
  }
}
```

在 `scripts/review.py` 中添加检查逻辑。

#### 自定义报告样式

修改 `scripts/report_generator.py` 中的 `generate_docx_report()` 函数。

## 更新日志

### v1.0.0 (2026-10-28)

- ✅ 初始版本发布
- ✅ 支持文字商标合规性审查
- ✅ 可插拔API适配器设计
- ✅ Word报告生成
- ✅ 内置完整法规文本（2026商标法）

### 计划功能

- [ ] 图形商标审查支持
- [ ] 声音商标审查
- [ ] 动态标志商标审查（2026商标法新增）
- [ ] AI辅助分析（基于LLM）
- [ ] Web界面
- [ ] 历史审查记录管理
- [ ] 案例库集成

## 许可证

本skill为内部工具，仅供参考使用。法规文本版权归原发布机构所有。

---

**最后更新**: 2026-10-28  
**适用法规**: 商标法2026修订版（2027-01-01施行）  
**技术支持**: 提交Issue或联系开发团队
