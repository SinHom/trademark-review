# 商标审查 Skill 使用指南

## 在Claude Code中使用

当你在与我对话时提到商标审查相关的需求，我会自动调用这个skill来帮你：

### 触发场景

- "帮我审查商标 XXX"
- "这个商标能注册吗？"
- "评估商标注册成功率"
- "生成商标审查报告"

### 示例对话

```
你: 我想注册"云智能"这个商标，用于软件开发服务，帮我评估一下

我会:
1. 调用 /trademark-review skill
2. 审查商标法合规性
3. 评估风险等级
4. 给出建议

你: 生成一份完整的审查报告

我会:
调用报告生成功能，输出Word文档
```

## 直接调用skill

```bash
# 方式1: 在对话中
/trademark-review "华为云" --class 9,42

# 方式2: 直接运行脚本
cd ~/.claude/skills/trademark-review
python scripts/review.py "华为云" --class 9,42 --report
```

## 接入你的商标API

### 步骤1: 创建适配器

在你的项目中创建 `my_trademark_api.py`:

```python
import sys
sys.path.append('/path/to/.claude/skills/trademark-review/references')

from trademark_api_adapter import TrademarkAPIAdapter
import requests

class MyCompanyAPI(TrademarkAPIAdapter):
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.mycompany.com/trademark"
    
    def search_similar(self, trademark_name, classes):
        response = requests.post(
            f"{self.base_url}/search",
            json={
                "keyword": trademark_name,
                "nice_classes": classes
            },
            headers={"X-API-Key": self.api_key}
        )
        
        # 转换为标准格式
        results = []
        for item in response.json()["data"]:
            results.append({
                "name": item["tm_name"],
                "registration_number": item["reg_no"],
                "status": item["status"],
                "classes": item["classes"],
                "applicant": item["applicant"],
                "application_date": item["apply_date"],
                "similarity_score": item.get("similarity", 0.5)
            })
        return results
```

### 步骤2: 配置

编辑 `~/.claude/skills/trademark-review/config.yaml`:

```yaml
trademark_review:
  api:
    adapter_class: "my_trademark_api.MyCompanyAPI"
```

设置环境变量:

```bash
export TRADEMARK_API_KEY="your_api_key_here"
```

### 步骤3: 使用

```bash
python scripts/review.py "测试商标" --class 9,42
# 会自动使用你的API进行近似性检索
```

## 批量处理

### 创建商标列表文件

`brands.txt`:
```
云图智能
智图云
图智云
云智图
智云图
```

### 批量审查

```bash
python scripts/review.py --batch brands.txt --class 9,42 --output results.json
```

### 批量生成报告

```bash
python scripts/review.py --batch brands.txt --class 9,42 --report --format docx
```

会为每个商标生成一份独立的审查报告。

## 常见用例

### 1. 品牌命名阶段

你有多个候选品牌名称，想选出最有可能注册成功的：

```bash
python scripts/review.py "候选1" "候选2" "候选3" --class 35,42 --output comparison.json
```

查看 `comparison.json`，对比各个候选的成功率。

### 2. 正式申请前预检

在提交正式申请前，做一次全面审查：

```bash
python scripts/review.py "最终品牌名" --class 9,35,42 --report --format docx
```

将生成的报告提供给代理机构参考。

### 3. 风险扫描

已经在使用某个品牌，但未注册，想评估被抢注的风险：

```bash
python scripts/review.py "当前品牌" --class 35 --report
```

查看是否有近似商标已注册。

### 4. 国际化品牌评估

评估中英文品牌组合：

```bash
python scripts/review.py "品牌名" "BrandName" --class 9,35,42 --report
```

分别评估中英文版本的注册可行性。

## 限制说明

### 当前支持

- ✅ 文字商标审查
- ✅ 禁用条款检查
- ✅ 显著性评估
- ✅ 近似性检索（需要API）
- ✅ Word报告生成

### 暂不支持

- ❌ 图形商标审查（需要图像识别）
- ❌ 声音商标审查（需要音频分析）
- ❌ 三维标志审查（需要3D模型分析）
- ❌ 颜色组合审查
- ❌ 动态标志审查（2026新增，规则尚未完善）

### 准确性说明

- **法规合规性**：准确率高（基于明确法条）
- **近似性判断**：依赖API质量
- **主观性问题**：商标审查员的判断可能不同

**建议**: 将本工具作为初筛工具，重要商标仍需人工复核。

## 故障排查

### 问题1: 提示"未配置商标查询API"

**原因**: 未设置API适配器  
**解决**: 
- 暂时使用 `--skip-similarity` 跳过近似性检索
- 或配置自己的API适配器

### 问题2: 报告生成失败

**原因**: 缺少依赖库  
**解决**: 
```bash
pip install python-docx
```

### 问题3: 法规文本加载失败

**原因**: 文件路径问题  
**解决**: 
```bash
cd ~/.claude/skills/trademark-review
ls references/laws/
# 确认文件存在
```

## 技术支持

如有问题，请：
1. 检查 `README.md` 中的常见问题
2. 查看 `SKILL.md` 中的详细说明
3. 提交Issue到项目仓库

---

**快速开始**: `python scripts/review.py "你的商标" --class 9,42`
