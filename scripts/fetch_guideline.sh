#!/usr/bin/env bash
# 重新生成 references/laws/examination_guideline_2021.md
#
# 依赖：curl、pdftoppm、tesseract（含 chi_sim 语言包）
# 用法：bash scripts/fetch_guideline.sh
#
# 说明：官方 PDF 是 422 页扫描件（无文字层），必须先渲染为图片再 OCR。
#       OCR 结果未做人工逐字校对，引用条文请以官方 PDF 为准。

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
PDF_URL="https://sbj.cnipa.gov.cn/upload/shangbiaoju/static/sbj/zcwj/202112/W020231026360188451411.pdf"
OUT="$ROOT/references/laws/examination_guideline_2021.md"

echo "==> 下载官方 PDF"
curl -L -A "Mozilla/5.0" --max-time 300 "$PDF_URL" -o "$WORK/guide.pdf"

echo "==> 渲染为图片 (200dpi)"
mkdir -p "$WORK/pages"
pdftoppm -r 200 -png "$WORK/guide.pdf" "$WORK/pages/p"

echo "==> OCR (chi_sim, 8 并发)"
mkdir -p "$WORK/ocr"
ls "$WORK"/pages/*.png | xargs -P 8 -I{} sh -c \
  'b=$(basename "{}" .png); tesseract "{}" "'"$WORK"'/ocr/$b" -l chi_sim --psm 6 >/dev/null 2>&1'

echo "==> 合并"
python3 - "$WORK/ocr" "$OUT" <<'PY'
import re, sys, pathlib, hashlib
ocr_dir, out_path = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
pages = sorted(ocr_dir.glob('p-*.txt'))
parts = []
for i, p in enumerate(pages, 1):
    lines = []
    for line in p.read_text(encoding='utf-8', errors='ignore').splitlines():
        s = line.strip()
        if not s or re.fullmatch(r'\d{1,3}', s):
            continue
        if s in ('商标审查审理编', '形式审查和事务工作编'):
            continue
        lines.append(s)
    parts.append(f"\n<!-- p{i} -->\n" + '\n'.join(lines))
body = '\n'.join(parts)
header = (
    "# 商标审查审理指南（2021年版）\n\n"
    "> 发布机关：国家知识产权局（公告第462号）  \n"
    "> 施行日期：2022-01-01  \n"
    "> 官方 PDF：https://sbj.cnipa.gov.cn/upload/shangbiaoju/static/sbj/zcwj/202112/W020231026360188451411.pdf  \n"
    "> 生成方式：官方扫描版 PDF，Tesseract（chi_sim, 200dpi）逐页 OCR 后合并。  \n"
    "> **OCR 未做逐字人工校对，存在形近字误识；对外引用条文以官方 PDF 原文为准。**  \n"
    f"> 页数：{len(pages)}；`<!-- pN -->` 对应官方 PDF 第 N 页。\n\n---\n\n")
out_path.write_text(header + body + '\n', encoding='utf-8')
print(f"written: {out_path} ({len(body)} chars)")
PY

rm -rf "$WORK"
echo "==> 完成"
