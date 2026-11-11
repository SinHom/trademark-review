#!/usr/bin/env bash
# 一键重放示例：生成 examples/ 下全部示例产物
#
# 用法：bash scripts/demo.sh
# 产物：
#   examples/case-01-clean.txt      干净商标（9/42 类）
#   examples/case-02-geographic.txt 地名条件性风险（北京烤鸭 30 类）
#   examples/case-03-hard-block.txt 欺骗性标志硬阻断（特供产品 35 类）
#   examples/case-04-national.txt   含国名的例外判断（中国移动 38 类）
#   examples/case-05-generic.txt    通用名称高风险（苹果 31 类）
#   examples/sample-report.docx     Word 报告
#
# 本脚本不含任何凭据、不联网（未配置数据源时在先商标显示"未检索"）。

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
OUT="$ROOT/examples"
mkdir -p "$OUT"

run_case() {
  local file="$1"; shift
  "$PY" scripts/review.py "$@" > "$OUT/$file" 2>&1
  echo "  ✓ examples/$file"
}

echo "生成示例产物"
run_case "case-01-clean.txt"      "云图智能" --class 9,42
run_case "case-02-geographic.txt" "北京烤鸭" --class 30
run_case "case-03-hard-block.txt" "特供产品" --class 35
run_case "case-04-national.txt"   "中国移动" --class 38
run_case "case-05-generic.txt"    "苹果" --class 31

rm -f "$OUT/sample-report.docx"
"$PY" scripts/review.py "云图智能" --class 9,42 \
      --report --format docx --output "$OUT/sample-report.docx" > /dev/null 2>&1
echo "  ✓ examples/sample-report.docx"

echo "完成：docs 里可直接引用 examples/ 下的真实产物"
