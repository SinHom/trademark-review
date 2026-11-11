# 商标审查 Skill - 安装指南

## 系统要求

- **Python**: 3.7+
- **操作系统**: Windows / Linux / macOS
- **依赖库**: 见 requirements.txt

## 安装步骤

### 1. 确认skill已安装

```bash
cd ~/.claude/skills/trademark-review
ls -la
```

应该看到以下文件结构：
```
trademark-review/
├── SKILL.md
├── README.md
├── config.yaml
├── requirements.txt
├── scripts/
├── references/
└── templates/
```

### 2. 安装Python依赖

```bash
# 使用pip安装
pip install -r requirements.txt

# 或使用pip3
pip3 install -r requirements.txt
```

**核心依赖**：
- `PyYAML` - 配置文件解析
- `python-docx` - Word文档生成

**可选依赖**（按需安装）：
- `docx2pdf` - PDF转换（Windows可能需要Microsoft Word）
- `requests` - 如果需要调用外部API

### 3. 验证安装

```bash
python scripts/review.py --help
```

应该看到命令行帮助信息。

### 4. 运行测试

```bash
# 测试基本功能
python scripts/review.py "测试商标" --class 9,42 --skip-similarity
```

应该看到审查结果输出。

## 配置（可选）

### 基础配置

`config.yaml` 包含默认配置，一般无需修改。

### 接入商标查询API（可选）

如果你有商标查询API，可以配置：

1. 创建自己的适配器（参考 `DOCUMENTATION.md`）
2. 修改 `config.yaml`:
   ```yaml
   trademark_review:
     api:
       adapter_class: "your_module.YourAdapter"
   ```
3. 设置环境变量:
   ```bash
   export TRADEMARK_API_KEY="your_api_key"
   ```

### 跳过API检索

如果暂时不需要近似性检索：

```bash
python scripts/review.py "商标" --skip-similarity
```

## 在Claude Code中使用

安装完成后，在对话中直接使用：

```
你: 帮我审查"云图智能"这个商标

Claude: [调用skill进行审查并展示结果]
```

或显式调用：

```
/trademark-review "云图智能" --class 9,42
```

## 常见问题

### 问题1: ModuleNotFoundError: No module named 'yaml'

**解决**:
```bash
pip install PyYAML
```

### 问题2: 报告生成失败

**解决**:
```bash
pip install python-docx
```

### 问题3: Windows上Unicode编码错误

**解决**: 已在v1.0.0中修复，确保使用最新版本。

### 问题4: 找不到law文件

**解决**: 确认 `references/laws/` 目录下有法规文件：
```bash
ls references/laws/
```

应该看到：
- trademark_law_2026.md
- trademark_regulation_2014.md
- collective_certification_2024.md

## 卸载

```bash
rm -rf ~/.claude/skills/trademark-review
```

## 更新

从skill仓库拉取最新版本：

```bash
cd ~/.claude/skills/trademark-review
git pull origin main  # 如果是从git仓库安装
```

或重新安装新版本覆盖旧版本。

## 技术支持

- 📖 查看 `README.md` - 用户手册
- 🚀 查看 `QUICKSTART.md` - 快速开始
- 📚 查看 `DOCUMENTATION.md` - 技术文档
- 🧪 查看 `TEST.md` - 测试说明

---

**安装日期**: 2026-10-28  
**Skill版本**: v1.0.0
