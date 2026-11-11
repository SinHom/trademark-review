#!/usr/bin/env bash
# 重新生成 references/laws/examination_guideline_2021.md
#
# 优先路径：下载结构化转录的 43 章 Markdown 并合并（秒级，文本干净）
# 备用路径：官方 PDF 是 422 页扫描件，需 pdftoppm + tesseract OCR（约 10 分钟，有误识）
#
# 用法：
#   bash scripts/fetch_guideline.sh          # 默认走转录版
#   bash scripts/fetch_guideline.sh --ocr    # 强制走 OCR 版

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/references/laws/examination_guideline_2021.md"
MODE="${1:-md}"

if [ "$MODE" = "--ocr" ]; then
  WORK="$(mktemp -d)"
  PDF_URL="https://sbj.cnipa.gov.cn/upload/shangbiaoju/static/sbj/zcwj/202112/W020231026360188451411.pdf"
  echo "==> 下载官方 PDF"
  curl -L -A "Mozilla/5.0" --max-time 300 "$PDF_URL" -o "$WORK/guide.pdf"
  echo "==> 渲染 (200dpi)"
  mkdir -p "$WORK/pages"
  pdftoppm -r 200 -png "$WORK/guide.pdf" "$WORK/pages/p"
  echo "==> OCR (chi_sim, 8 并发)"
  mkdir -p "$WORK/ocr"
  ls "$WORK"/pages/*.png | xargs -P 8 -I{} sh -c \
    'b=$(basename "{}" .png); tesseract "{}" "'"$WORK"'/ocr/$b" -l chi_sim --psm 6 >/dev/null 2>&1'
  echo "==> 合并 OCR 文本"
  python3 - "$WORK/ocr" "$OUT" <<'PY'
import re, sys, pathlib
ocr_dir, out_path = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
parts = []
for i, p in enumerate(sorted(ocr_dir.glob('p-*.txt')), 1):
    lines = [s for s in (l.strip() for l in p.read_text(encoding='utf-8', errors='ignore').splitlines())
             if s and not re.fullmatch(r'\d{1,3}', s) and s not in ('商标审查审理编', '形式审查和事务工作编')]
    parts.append(f"\n<!-- p{i} -->\n" + '\n'.join(lines))
header = ("# 商标审查审理指南（2021年版，OCR）\n\n"
          "> 由官方 422 页扫描版经 Tesseract OCR 生成，未逐字校对；引用以官方 PDF 为准。\n\n---\n\n")
out_path.write_text(header + '\n'.join(parts) + '\n', encoding='utf-8')
print(f"written: {out_path}")
PY
  rm -rf "$WORK"
  exit 0
fi

WORK="$(mktemp -d)"
BASE="https://raw.githubusercontent.com/cat-xierluo/trademark-assistant.skill/main/references/trademark-examination-and-adjudication-guidelines"

echo "==> 下载 43 章结构化文本"
mkdir -p "$WORK/ch"
for i in $(seq -w 1 43); do
  curl -sL --max-time 60 "$BASE/chapter-$i.md" -o "$WORK/ch/chapter-$i.md"
done

echo "==> 合并并生成目录"
python3 - "$WORK/ch" "$OUT" <<'PY'
import re, sys, pathlib
src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
titles, parts, toc = {}, [], []
for i in range(1, 44):
    text = (src / f'chapter-{i:02d}.md').read_text(encoding='utf-8')
    m = re.search(r'^## (.+)$', text, re.M)
    titles[i] = m.group(1).strip() if m else f'第{i}章'
    body = re.sub(r'^# .*\n', '', text, count=1)
    body = re.sub(r'^- 上下文.*\n?', '', body, flags=re.M)
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    parts.append(f"\n\n---\n\n<!-- chapter {i} -->\n\n{body}\n")
    toc.append(f"- {titles[i]}（chapter-{i:02d}）")

header = """# 商标审查审理指南（2021年版）

> 发布机关：国家知识产权局（公告第462号）
> 施行日期：2022-01-01
> 官方公告：https://sbj.cnipa.gov.cn/zcwj/2026/0829/40022.html
> 官方 PDF：https://sbj.cnipa.gov.cn/upload/shangbiaoju/static/sbj/zcwj/202112/W020231026360188451411.pdf
> 文本来源：结构化转录（cat-xierluo/trademark-assistant.skill），已与官方 PDF 抽查核对。
> 如发现疑义，以官方 PDF 为准。

## 目录

""" + '\n'.join(toc) + "\n\n## 重点章节\n\n- 下编第三章 不得作为商标标志的审查审理 → chapter 27\n- 下编第四章 商标显著特征的审查审理 → chapter 28\n- 下编第五章 商标相同、近似的审查审理 → chapter 29\n- 下编第九章 集体商标、证明商标的审查审理 → chapter 33\n"
out.write_text(header + ''.join(parts), encoding='utf-8')
print(f"written: {out}")
PY

rm -rf "$WORK"
echo "==> 完成"
