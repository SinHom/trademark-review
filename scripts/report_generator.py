#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商标审查报告生成器

报告中的法条引用全部来自审查结果中的 article 字段（其源头是
references/article_map.json），本文件不硬编码任何条号。
"""

from datetime import datetime
from typing import List, Dict


def generate_report(results: List[Dict], output_path: str, format: str = "docx"):
    if format == "docx":
        generate_docx_report(results, output_path)
    elif format == "pdf":
        generate_pdf_report(results, output_path)
    elif format == "json":
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    else:
        raise ValueError(f"不支持的格式: {format}")


def _add_lines(doc, text: str, style=None):
    para = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    para.add_run(text)
    return para


def generate_docx_report(results: List[Dict], output_path: str):
    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        raise SystemExit("需要安装 python-docx：pip install python-docx")

    doc = Document()

    title = doc.add_heading("商标合规审查报告", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    law = results[0].get("law", {})
    # 不能用 strftime('%Y年%m月%d日')：Python 3.9 在 Windows 上会用系统 locale
    # 编码格式串，英文系统（cp1252）编不出"年"而抛 UnicodeEncodeError。
    # 手工拼接日期，与 locale 无关。
    _today = datetime.now()
    _add_lines(doc, f"生成日期：{_today.year}年{_today.month:02d}月{_today.day:02d}日")
    _add_lines(doc, f"审查商标数量：{len(results)}")
    _add_lines(doc, f"审查依据：{law.get('label','')}（{law.get('effective_from','')} 施行，现行有效）")
    _add_lines(
        doc,
        f"版本说明：括号内并列标注 {law.get('counterpart_label','')} 条号；"
        f"该修订版自 {law.get('counterpart_effective_from','')} 起施行，本报告结论不以其为依据。")

    provenance = results[0].get("data_provenance") or {}
    if provenance:
        _add_lines(
            doc,
            "数据来源：规则库 v{r}（更新于 {u}），条号映射截至 {a}；"
            "规则文件摘要 {h}。本报告结论基于上述版本，规则更新后需重新审查。".format(
                r=provenance.get("rules_version", "?"),
                u=provenance.get("rules_updated", "?"),
                a=provenance.get("article_map_as_of", "?"),
                h=(provenance.get("risk_rules") or {}).get("sha256_8", "?")))
    doc.add_paragraph("")

    for idx, result in enumerate(results, 1):
        doc.add_heading(f"{idx}. {result['trademark_name']}", level=1)
        overall = result["overall"]

        doc.add_heading("结论摘要", level=2)
        table = doc.add_table(rows=6, cols=2)
        table.style = 'Light Grid Accent 1'
        rows = [
            ("商标名称", result['trademark_name']),
            ("指定类别", ", ".join(map(str, result['classes']))),
            ("审查结论", overall.get("verdict", overall.get("risk_level", ""))),
            ("预估成功率", "不适用（命中禁用条款）" if overall.get("success_rate") is None
             and overall.get("verdict") == "不得注册"
             else ("不适用（结论未决）" if overall.get("success_rate") is None
                   else f"{overall['success_rate']}%（启发式估算，非统计数据）")),
            ("结论完整性", "完整" if overall.get("completeness") == "complete" else "不完整（在先商标未检索）"),
            ("规则库版本", f"v{(result.get('data_provenance') or {}).get('rules_version', '?')}"),
        ]
        for i, (k, v) in enumerate(rows):
            table.rows[i].cells[0].text = k
            table.rows[i].cells[1].text = str(v)

        _add_lines(doc, f"建议：{overall.get('recommendation','')}")
        doc.add_paragraph("")

        # 1. 禁用标志
        prohibited = result["prohibited_check"]
        first_article = ""
        if prohibited.get("violations"):
            first_article = prohibited["violations"][0].get("article", "")
        doc.add_heading(f"1. 禁用标志审查{'（' + first_article + '）' if first_article else ''}", level=2)

        if not prohibited["violations"]:
            _add_lines(doc, "✅ 未命中禁用标志条款。")
        else:
            for v in prohibited["violations"]:
                _add_lines(doc, f"• {v['description']}", style='List Bullet')
                _add_lines(doc, f"依据：{v['article']}", style='List Bullet 2')
                _add_lines(doc, f"法律后果：{v.get('consequence','需人工确认')}", style='List Bullet 2')

        # 2. 显著特征
        distinctive = result["distinctiveness_check"]
        art = distinctive["issues"][0].get("article", "") if distinctive.get("issues") else ""
        doc.add_heading(f"2. 显著特征审查{'（' + art + '）' if art else ''}", level=2)

        if not distinctive["issues"]:
            _add_lines(doc, "✅ 规则层面未发现显著特征问题。")
        else:
            for issue in distinctive["issues"]:
                _add_lines(doc, f"• {issue['description']}", style='List Bullet')
                _add_lines(doc, f"依据：{issue['article']}", style='List Bullet 2')
            if distinctive.get("note"):
                _add_lines(doc, f"备注：{distinctive['note']}")

        ai = distinctive.get("ai_analysis")
        if ai:
            _add_lines(doc, f"AI 辅助评估：{ai.get('ai_assessment','')}")
            _add_lines(doc, f"AI 理由：{ai.get('reasoning','')}")

        # 3. 在先商标
        sim = result["similarity_check"]
        doc.add_heading("3. 在先商标检索", level=2)
        status = sim.get("status", "ok")

        if status == "ok":
            marks = sim.get("similar_marks", [])
            if not marks:
                _add_lines(doc, "✅ 检索完成，未发现相同或近似商标。")
            else:
                _add_lines(doc, f"发现 {len(marks)} 条可能冲突的在先商标。")
                t = doc.add_table(rows=len(marks) + 1, cols=5)
                t.style = 'Light Grid Accent 1'
                for i, h in enumerate(["商标名称", "注册号", "状态", "类别", "申请人"]):
                    t.rows[0].cells[i].text = h
                for i, m in enumerate(marks, 1):
                    t.rows[i].cells[0].text = str(m.get("name", ""))
                    t.rows[i].cells[1].text = str(m.get("registration_number", ""))
                    t.rows[i].cells[2].text = str(m.get("status", ""))
                    t.rows[i].cells[3].text = ", ".join(map(str, m.get("classes", [])))
                    t.rows[i].cells[4].text = str(m.get("applicant", ""))
                if sim.get("article"):
                    _add_lines(doc, f"依据：{sim['article']}")
        elif status == "skipped":
            _add_lines(doc, "⏭️ 已在本次审查中跳过在先商标检索，结论不含冲突判断。")
        elif status == "not_configured":
            _add_lines(doc, "⚠️ 未配置商标数据源，未执行在先商标检索。")
            _add_lines(doc, "本报告结论不包含在先商标冲突判断，请另行委托专业检索。")
        else:
            _add_lines(doc, f"❌ 在先商标检索失败：{sim.get('error','未知错误')}")
            _add_lines(doc, "本报告结论不包含在先商标冲突判断。")

        # 4. 结论边界
        coverage = result.get("coverage")
        if coverage:
            doc.add_heading("4. 本次检查范围", level=2)
            _add_lines(doc, "已执行：")
            for item in coverage.get("checked", []):
                _add_lines(doc, f"• {item}", style='List Bullet')
            _add_lines(doc, "未执行（本报告结论不含以下判断）：")
            for item in coverage.get("not_checked", []):
                _add_lines(doc, f"• {item}", style='List Bullet')

        caveats = overall.get("caveats") or []
        if caveats:
            doc.add_heading("5. 结论边界", level=2)
            for c in caveats:
                _add_lines(doc, f"• {c}", style='List Bullet')

        if overall.get("ai_alternatives"):
            doc.add_heading("6. AI 修改建议", level=2)
            for i, alt in enumerate(overall["ai_alternatives"], 1):
                _add_lines(doc, f"{i}. {alt}")

        if idx < len(results):
            doc.add_page_break()

    doc.add_page_break()
    doc.add_heading("免责声明", level=1)
    _add_lines(
        doc,
        "本报告基于公开法规文本与内置规则库进行技术性比对，用于申请前的风险预筛，"
        "不构成法律意见，也不能替代商标代理机构的正式检索与专业判断。")
    _add_lines(
        doc,
        "商标审查包含审查员的主观判断，且个案情况可能不同；实际审查结果可能与本报告结论存在差异。"
        "涉及重要商标的注册决策，请咨询依法设立的商标代理机构或执业律师。")
    _add_lines(
        doc,
        "规则库未覆盖全部法条与全部商品/服务类别；报告仅在已执行且已列明的检查项范围内作出结论。")

    doc.save(output_path)


def generate_pdf_report(results: List[Dict], output_path: str):
    try:
        from docx2pdf import convert
    except ImportError:
        docx_path = output_path.rsplit('.', 1)[0] + '.docx'
        generate_docx_report(results, docx_path)
        print("⚠️  未安装 docx2pdf，已改为生成 Word 版本。")
        print("    安装后可生成 PDF：pip install docx2pdf（Windows 需本机安装 Word）")
        print(f"✅ Word 版本: {docx_path}")
        return

    import tempfile, os
    fd, docx_path = tempfile.mkstemp(suffix='.docx')
    os.close(fd)
    generate_docx_report(results, docx_path)
    try:
        convert(docx_path, output_path)
    finally:
        try:
            os.unlink(docx_path)
        except OSError:
            pass


if __name__ == "__main__":
    demo = {
        "trademark_name": "示例",
        "classes": [9],
        "review_date": "2026-11-11",
        "law": {"version": "2019", "label": "2019年修正",
                "effective_from": "2019-11-01",
                "counterpart_label": "2026年修订",
                "counterpart_effective_from": "2027-01-01"},
        "prohibited_check": {"violations": [], "hard_block": False},
        "distinctiveness_check": {"issues": []},
        "similarity_check": {"status": "not_configured"},
        "overall": {"verdict": "低风险", "risk_level": "低风险", "success_rate": 90,
                    "completeness": "partial",
                    "caveats": ["在先商标未检索：未配置数据源，本结论不含冲突判断。"],
                    "recommendation": "规则层面未发现明显障碍"},
    }
    generate_report([demo], "demo_report.docx", format="docx")
    print("demo_report.docx")
