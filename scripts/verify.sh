#!/usr/bin/env bash
# 三层验证：l0 静态 / l1 回归测试 / l2 全量 + 门禁 + 一致性
# 用法：bash scripts/verify.sh [l0|l1|l2]
# 纪律：成功只输出一行摘要；失败输出定位信息。

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
LEVEL="${1:-l0}"
PY="${PYTHON:-python3}"

fail() { echo "❌ verify $LEVEL 失败: $1"; exit 1; }

# ---------- L0 静态 ----------
if ! "$PY" - <<'PY'
import json, pathlib, sys
try:
    import yaml
except ImportError:
    print("缺少 PyYAML"); sys.exit(1)
files = list(pathlib.Path('scripts').glob('*.py')) + list(pathlib.Path('tests').glob('*.py')) \
        + list(pathlib.Path('references').glob('*.py'))
for f in files:
    compile(f.read_text(encoding='utf-8'), str(f), 'exec')
for f in pathlib.Path('references').rglob('*.json'):
    json.loads(f.read_text(encoding='utf-8'))
yaml.safe_load(pathlib.Path('config.yaml').read_text(encoding='utf-8'))
json.loads(pathlib.Path('test-prompts.json').read_text(encoding='utf-8'))
PY
then
  fail "静态检查（语法/JSON/YAML）"
fi

if [ "$LEVEL" = "l0" ]; then echo "✅ verify l0 通过（语法 + JSON/YAML 解析）"; exit 0; fi

# ---------- L1 回归测试 ----------
OUT="$("$PY" tests/test_review.py 2>&1)"
echo "$OUT" | tail -1 | grep -q "所有测试通过" || { echo "$OUT" | tail -20; fail "回归测试"; }

if [ "$LEVEL" = "l1" ]; then echo "✅ verify l1 通过（15 项回归测试）"; exit 0; fi

# ---------- L2 门禁 + 一致性 ----------
if ! "$PY" - <<'PY'
import subprocess, sys, re, pathlib
gates = {
    ("中国制造", 9): "不得注册",
    ("北京烤鸭", 30): "条件性风险（需人工确认）",
    ("沙县小吃", 43): "条件性风险（需人工确认）",
    ("东方甄选", 35): "低风险",
    ("苹果", 31): "高风险（缺乏显著特征）",
}
for (name, cls), expect in gates.items():
    out = subprocess.run([sys.executable, "scripts/review.py", name, "--class", str(cls)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    m = re.search(r"^结论: (.+)$", out, re.M)
    assert m, f"{name} 无结论输出"
    assert m.group(1).strip() == expect, f"{name}: 期望 {expect}，实际 {m.group(1).strip()}"

# 版本一致性
skill = pathlib.Path("SKILL.md").read_text(encoding="utf-8")
ver = re.search(r"^version: (.+)$", skill, re.M).group(1).strip()
tp = __import__("json").loads(pathlib.Path("test-prompts.json").read_text(encoding="utf-8"))["version"]
assert ver == tp, f"SKILL.md {ver} != test-prompts {tp}"

# 条号映射可定位
from scripts.review import TrademarkReviewer
r = TrademarkReviewer()
laws = {k: pathlib.Path(f"references/laws/trademark_law_{k}.md").read_text(encoding="utf-8") for k in ("2019","2026")}
for key, m in r.article_map["mapping"].items():
    for v, num in m.items():
        if not num or v not in laws: continue
        art = num.split("第",1)[1].split("条")[0]
        assert f"第{art}条" in laws[v], f"{key}/{v} 找不到 第{art}条"

# 权重与阈值必须自洽（改坏会让分级静默失真）
import json as _json
_rules = _json.loads(pathlib.Path("references/risk_rules.json").read_text(encoding="utf-8"))
_w = _rules.get("risk_weights", {})
assert abs(sum(_w.values()) - 1.0) < 1e-6, f"risk_weights 之和应为 1.0，实际 {sum(_w.values())}"
_t = _rules.get("similarity_thresholds", {})
assert _t["medium_risk"] < _t["high_risk"], "相似度阈值必须递增"
for _k in ("political",):
    assert _k not in _rules.get("prohibited_keywords", {}), f"遗留旧键 {_k}"

# 关键词表不得含空串/null（空串会恒真命中，导致全盘误判）
for _cat, _words in _rules.get("prohibited_keywords", {}).items():
    assert all(isinstance(w, str) and w.strip() for w in _words), f"关键词表 {_cat} 含空值"

# 代码内不得硬编码条号（唯一事实来源是 article_map.json）
import re as _re
_art = _re.compile(r"第[一二三四五六七八九十百零]+条")
for _f in list(pathlib.Path("scripts").glob("*.py")) + [pathlib.Path("references/trademark_api_adapter.py")]:
    for _i, _line in enumerate(_f.read_text(encoding="utf-8").splitlines(), 1):
        if _line.lstrip().startswith("#"):
            continue
        assert not _art.search(_line), f"{_f}:{_i} 硬编码条号，应从 article_map.json 取"
PY
then
  fail "门禁或一致性检查"
fi

# 密钥扫描
if grep -rInE "(sk-[A-Za-z0-9]{10,}|gho_[A-Za-z0-9]{10,}|api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9]{8,})" \
   --include="*.py" --include="*.md" --include="*.yaml" --include="*.json" . 2>/dev/null \
   | grep -v "your_api_key\|your_key\|api_key\": null\|api_key\s*:\s*null" >/dev/null; then
  fail "发现疑似硬编码密钥"
fi

echo "✅ verify l2 通过（回归 + 5 个门禁 + 版本/条号一致性 + 密钥扫描）"
