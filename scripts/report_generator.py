#!/usr/bin/env python3
"""
商标审查报告生成器

生成Word或PDF格式的专业商标审查报告
"""

from pathlib import Path
from typing import List, Dict
from datetime import datetime


def generate_report(results: List[Dict], output_path: str, format: str = "docx"):
    """
    生成审查报告

    Args:
        results: 审查结果列表
        output_path: 输出文件路径
        format: 报告格式 docx/pdf/html
    """
    if format == "docx":
        generate_docx_report(results, output_path)
    elif format == "pdf":
        generate_pdf_report(results, output_path)
    elif format == "json":
        generate_json_report(results, output_path)
    else:
        raise ValueError(f"不支持的格式: {format}")


def generate_docx_report(results: List[Dict], output_path: str):
    """生成Word格式报告"""
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        print("❌ 需要安装 python-docx: pip install python-docx")
        return

    doc = Document()

    # 设置标题
    title = doc.add_heading("商标注册成功率审查报告", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 报告信息
    doc.add_paragraph(f"生成日期: {datetime.now().strftime('%Y年%m月%d日')}")
    doc.add_paragraph(f"审查商标数量: {len(results)}")
    doc.add_paragraph("")

    # 遍历每个商标
    for idx, result in enumerate(results, 1):
        # 商标标题
        doc.add_heading(f"{idx}. {result['trademark_name']}", level=1)

        # 执行摘要
        doc.add_heading("执行摘要", level=2)

        overall = result["overall"]
        summary_table = doc.add_table(rows=4, cols=2)
        summary_table.style = 'Light Grid Accent 1'

        summary_data = [
            ("商标名称", result['trademark_name']),
            ("指定类别", ", ".join(map(str, result['classes']))),
            ("风险等级", overall['risk_level']),
            ("预估成功率", f"{overall['success_rate']}%"),
        ]

        for i, (key, value) in enumerate(summary_data):
            summary_table.rows[i].cells[0].text = key
            summary_table.rows[i].cells[1].text = str(value)

        # 风险等级颜色标注
        risk_para = doc.add_paragraph()
        risk_para.add_run(f"总体评估: {overall['risk_level']} | ")
        risk_para.add_run(f"建议: {overall['recommendation']}")

        doc.add_paragraph("")

        # 1. 禁用条款审查
        doc.add_heading("1. 禁用条款审查（商标法第十条）", level=2)

        prohibited = result['prohibited_check']
        if prohibited['passed']:
            p = doc.add_paragraph()
            p.add_run("✅ 通过").bold = True
            p.add_run(" - 未发现违反禁用条款的情形")
        else:
            p = doc.add_paragraph()
            p.add_run(f"❌ 未通过").bold = True
            p.add_run(f" - 发现 {len(prohibited['violations'])} 个违规项")

            for violation in prohibited['violations']:
                doc.add_paragraph(
                    f"• {violation['description']}",
                    style='List Bullet'
                )
                doc.add_paragraph(
                    f"  法律依据: {violation['article']}",
                    style='List Bullet 2'
                )
                if 'note' in violation:
                    doc.add_paragraph(
                        f"  说明: {violation['note']}",
                        style='List Bullet 2'
                    )

        # 2. 显著性审查
        doc.add_heading("2. 显著性审查（商标法第十一条）", level=2)

        distinctiveness = result['distinctiveness_check']
        if distinctiveness['passed']:
            p = doc.add_paragraph()
            p.add_run("✅ 通过").bold = True
            p.add_run(" - 具备显著特征，便于识别")
        else:
            p = doc.add_paragraph()
            p.add_run(f"⚠️  存在问题").bold = True
            p.add_run(f" - 发现 {len(distinctiveness['issues'])} 个显著性问题")

            for issue in distinctiveness['issues']:
                doc.add_paragraph(
                    f"• {issue['description']}",
                    style='List Bullet'
                )

            if 'note' in distinctiveness:
                doc.add_paragraph(f"备注: {distinctiveness['note']}")

        # 3. 近似性检索
        doc.add_heading("3. 在先权利检索（商标法第三十条、三十一条）", level=2)

        similarity = result['similarity_check']
        similar_marks = similarity.get('similar_marks', [])

        if 'error' in similarity:
            doc.add_paragraph(f"⚠️  检索失败: {similarity['error']}")
            doc.add_paragraph(f"说明: {similarity.get('note', '')}")
        elif not similar_marks:
            p = doc.add_paragraph()
            p.add_run("✅ 通过").bold = True
            p.add_run(" - 未发现相同或近似的在先商标")
        else:
            high_risk = similarity.get('high_risk_count', 0)
            medium_risk = similarity.get('medium_risk_count', 0)

            p = doc.add_paragraph()
            if high_risk > 0:
                p.add_run(f"❌ 高风险").bold = True
            else:
                p.add_run(f"⚠️  存在冲突").bold = True
            p.add_run(f" - 发现 {len(similar_marks)} 个近似商标")

            if high_risk > 0:
                doc.add_paragraph(f"其中高度近似: {high_risk} 个")
            if medium_risk > 0:
                doc.add_paragraph(f"中度近似: {medium_risk} 个")

            # 近似商标列表
            doc.add_heading("近似商标列表", level=3)

            if similar_marks:
                table = doc.add_table(rows=len(similar_marks) + 1, cols=5)
                table.style = 'Light Grid Accent 1'

                # 表头
                headers = ['商标名称', '注册号', '状态', '类别', '申请人']
                for i, header in enumerate(headers):
                    table.rows[0].cells[i].text = header

                # 数据
                for i, mark in enumerate(similar_marks, 1):
                    table.rows[i].cells[0].text = mark.get('name', '')
                    table.rows[i].cells[1].text = mark.get('registration_number', '')
                    table.rows[i].cells[2].text = mark.get('status', '')
                    table.rows[i].cells[3].text = ", ".join(map(str, mark.get('classes', [])))
                    table.rows[i].cells[4].text = mark.get('applicant', '')

        # 4. 综合建议
        doc.add_heading("4. 综合评估与建议", level=2)

        doc.add_paragraph(f"基于以上审查结果，该商标的注册成功率评估为: {overall['success_rate']}%")
        doc.add_paragraph(f"风险等级: {overall['risk_level']}")
        doc.add_paragraph(f"建议措施: {overall['recommendation']}")

        # 分隔线
        if idx < len(results):
            doc.add_page_break()

    # 免责声明
    doc.add_page_break()
    doc.add_heading("免责声明", level=1)
    doc.add_paragraph(
        "本报告基于《中华人民共和国商标法》及相关法规进行技术性分析，仅供参考，不构成法律意见。"
        "商标注册存在审查的主观性和案例的不确定性，实际审查结果可能与本报告评估存在差异。"
        "重要商标注册决策建议咨询专业知识产权代理机构或律师。"
    )

    # 保存文档
    doc.save(output_path)


def generate_pdf_report(results: List[Dict], output_path: str):
    """生成PDF格式报告"""
    # 先生成docx，再转换为PDF（需要额外的库）
    try:
        from docx2pdf import convert
    except ImportError:
        print("❌ PDF生成需要安装 docx2pdf")
        print("   可选方案1: pip install docx2pdf")
        print("   可选方案2: 先生成docx，手动转换为PDF")
        # 回退到生成docx
        docx_path = output_path.replace('.pdf', '.docx')
        generate_docx_report(results, docx_path)
        print(f"✅ 已生成Word版本: {docx_path}")
        return

    # 先生成临时docx
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        docx_path = tmp.name

    generate_docx_report(results, docx_path)

    # 转换为PDF
    try:
        convert(docx_path, output_path)
        Path(docx_path).unlink()  # 删除临时文件
    except Exception as e:
        print(f"❌ PDF转换失败: {e}")
        print(f"   已保留Word版本: {docx_path}")


def generate_json_report(results: List[Dict], output_path: str):
    """生成JSON格式报告"""
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 测试报告生成
    test_result = {
        "trademark_name": "测试商标",
        "classes": [9, 42],
        "review_date": "2026-10-28",
        "prohibited_check": {
            "passed": False,
            "violations": [
                {
                    "type": "geographic",
                    "keyword": "北京",
                    "article": "商标法第十条第二款",
                    "description": "含有县级以上行政区划地名",
                    "severity": "medium"
                }
            ],
            "risk_score": 0.2
        },
        "distinctiveness_check": {
            "passed": True,
            "issues": [],
            "risk_score": 0.0
        },
        "similarity_check": {
            "passed": True,
            "similar_marks": [],
            "risk_score": 0.0
        },
        "overall": {
            "risk_score": 0.06,
            "risk_level": "低风险",
            "success_rate": 94,
            "recommendation": "可以注册，但建议确认地名是否具有其他含义"
        }
    }

    generate_report([test_result], "test_report.docx", format="docx")
    print("✅ 测试报告已生成: test_report.docx")
