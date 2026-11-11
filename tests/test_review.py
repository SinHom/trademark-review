#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商标审查回归测试

覆盖：禁用条款硬阻断、显著性、按类别通用名称、地名条件性风险、
未配置数据源时的诚实标注、条号映射与法规原文一致性。
"""

import sys
import os
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from scripts.review import TrademarkReviewer


def R():
    return TrademarkReviewer()


def test_article_map_consistency():
    """条号映射必须能在对应法规原文中定位到。"""
    reviewer = R()
    law_2026 = (ROOT / "references/laws/trademark_law_2026.md").read_text(encoding="utf-8")
    law_2019 = (ROOT / "references/laws/trademark_law_2019.md").read_text(encoding="utf-8")

    for key, mapping in reviewer.article_map["mapping"].items():
        for ver, num in mapping.items():
            if not num or ver not in ("2019", "2026"):
                continue
            text = law_2019 if ver == "2019" else law_2026
            # 取条号中的“第X条”部分验证存在
            art = num.split("第", 1)[1].split("条")[0] if "条" in num else None
            assert art is not None, f"{key} 条号格式异常: {num}"
            assert f"第{art}条" in text, f"{key} 在 {ver} 版法规中找不到 第{art}条"
    print("✅ 条号映射与法规原文一致")


def test_hard_block_political():
    r = R()
    res = r.review("中国制造", classes=[9])
    assert res["prohibited_check"]["hard_block"] is True
    assert res["overall"]["verdict"] == "不得注册"
    assert res["overall"]["success_rate"] is None
    assert "第十五条" in res["prohibited_check"]["violations"][0]["article"]
    print("✅ 政治敏感词 → 硬阻断，且并列标注 2026 版第十五条")


def test_hard_block_misleading():
    r = R()
    res = r.review("特供产品", classes=[35])
    assert res["prohibited_check"]["hard_block"] is True
    assert res["overall"]["verdict"] == "不得注册"
    assert "第十五条第一款第八项" in res["prohibited_check"]["violations"][0]["article"]
    print("✅ 欺骗性标志 → 硬阻断，条号映射正确")


def test_geographic_conditional():
    r = R()
    res = r.review("北京烤鸭", classes=[30])
    assert res["prohibited_check"]["manual_review_required"] is True
    assert res["overall"]["verdict"] == "条件性风险（需人工确认）"
    assert res["overall"]["risk_level"] in ("中风险", "高风险")
    assert res["overall"]["success_rate"] is not None
    assert res["overall"]["success_rate"] < 90, "地名条件下不应给出 86% 这种偏高成功率"
    assert "第十六条" in res["prohibited_check"]["violations"][0]["article"]
    print("✅ 地名 → 条件性风险，不再误判为低风险")


def test_county_level_geographic():
    """县级地名也要命中。"""
    r = R()
    res = r.review("沙县小吃", classes=[43])
    keys = [v.get("keyword") for v in res["prohibited_check"]["violations"]]
    assert "沙县" in keys, f"应命中县级地名沙县，实际: {keys}"
    assert res["prohibited_check"]["manual_review_required"] is True
    print("✅ 县级地名命中（沙县）")


def test_common_word_not_inflated():
    """常见词形的县级地名按低置信处理，不抬高结论。"""
    r = R()
    res = r.review("东方甄选", classes=[35])
    assert res["overall"]["verdict"] == "低风险", res["overall"]["verdict"]
    lows = [v for v in res["prohibited_check"]["violations"] if v.get("severity") == "low"]
    assert lows, "应保留低置信提示"
    print("✅ 常见词地名不抬高结论（东方甄选仍为低风险）")


def test_all_45_classes_covered():
    r = R()
    assert len(r.risk_rules["generic_terms_by_class"]) == 45
    assert len(r.risk_rules["class_titles"]) == 45
    print("✅ 通用名称覆盖 45/45 类")


def test_descriptive():
    r = R()
    res = r.review("优质服务", classes=[35])
    assert res["distinctiveness_check"]["passed"] is False
    assert res["distinctiveness_check"]["risk_score"] > 0
    assert "第十七条第一款第二项" in res["distinctiveness_check"]["issues"][0]["article"]
    print("✅ 描述性词汇被检出，条号映射到 2026 版第十七条")


def test_generic_by_class():
    r = R()
    res = r.review("苹果", classes=[31])
    assert res["distinctiveness_check"]["passed"] is False
    types = [i["check_key"] for i in res["distinctiveness_check"]["issues"]]
    assert "distinctiveness_generic" in types
    # 同一名称在类别 9 不应触发 31 类的通用名称
    res9 = r.review("苹果", classes=[9])
    types9 = [i["check_key"] for i in res9["distinctiveness_check"]["issues"]]
    assert "distinctiveness_generic" not in types9
    print("✅ 通用名称按类别匹配（31类命中，9类不误伤）")


def test_clean_mark():
    r = R()
    res = r.review("云图智能", classes=[9, 42])
    assert res["prohibited_check"]["hard_block"] is False
    assert res["distinctiveness_check"]["passed"] is True
    print("✅ 正常商标未被误伤")


def test_similarity_not_configured_honest():
    r = R()
    res = r.review("测试商标XYZ", classes=[9])
    sim = res["similarity_check"]
    assert sim["status"] == "not_configured", f"实际状态: {sim['status']}"
    assert sim["similar_marks"] == [], "未配置数据源时不得返回任何近似商标"
    assert res["overall"]["completeness"] == "partial"
    assert any("未检索" in c or "未配置" in c for c in res["overall"]["caveats"])
    print("✅ 未配置数据源：如实标注未检索，不返回虚构近似商标")


def test_skip_similarity_declared():
    r = R()
    r.config.setdefault("trademark_review", {}).setdefault("review", {})["skip_similarity_check"] = True
    res = r.review("云图智能", classes=[9])
    assert res["similarity_check"]["status"] == "skipped"
    assert res["overall"]["completeness"] == "partial"
    print("✅ 跳过检索时明确声明，不谎报为已检索")


def test_cli_direct_run():
    """按 README 的直接调用方式必须能跑通。"""
    out = subprocess.run(
        [sys.executable, "scripts/review.py", "云图智能", "--class", "9", "--skip-similarity"],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert out.returncode == 0, out.stderr
    assert "审查结果摘要" in out.stdout
    assert "No module named" not in out.stderr
    print("✅ 按 README 直接运行 scripts/review.py 通过")


def test_batch_and_json():
    import tempfile
    r = R()
    names = ["云图智能", "中国制造", "优质服务"]
    classes = [9]
    results = [r.review(n, classes) for n in names]
    assert len(results) == 3
    assert results[1]["overall"]["verdict"] == "不得注册"
    assert results[2]["distinctiveness_check"]["passed"] is False
    json.dumps(results, ensure_ascii=False)
    print("✅ 批量审查与 JSON 序列化正常")


def test_report_generation():
    import tempfile, os
    r = R()
    res = r.review("北京烤鸭", classes=[30])
    tmp = Path(tempfile.mkdtemp()) / "report.docx"
    from scripts.report_generator import generate_report
    generate_report([res], str(tmp), format="docx")
    assert tmp.exists() and tmp.stat().st_size > 1000
    print("✅ Word 报告生成正常")


def test_national_name_tiers():
    """国家名称分档：整体即国名→不得注册；仅含国名→条件性（指南第三章例外）。"""
    r = R()
    assert r.review("中国", classes=[9])["overall"]["verdict"] == "不得注册"
    for name, cls in (("中华铅笔", 16), ("中国移动", 38)):
        res = r.review(name, classes=[cls])
        assert res["overall"]["verdict"] == "条件性风险（需人工确认）", f"{name}: {res['overall']['verdict']}"
        # 建议文案必须按命中的检查项生成，不能写死"含地名"
        assert "国家名称" in res["overall"]["recommendation"], res["overall"]["recommendation"]
        assert "地名" not in res["overall"]["recommendation"], "含国名的建议不得误写成地名"
        # 结论未决时不给成功率数字
        assert res["overall"]["success_rate"] is None, "含国名未决时不应给成功率"
    # 产地误导仍按欺骗性硬阻断
    assert r.review("中国制造", classes=[9])["overall"]["verdict"] == "不得注册"
    print("✅ 国家名称分档正确（含国名不再一律硬阻断，建议文案按命中项生成）")


def test_violation_dedup():
    """关键词互为子串时不得重复报（中华人民共和国 ≠ 国名+中华+共和县）。"""
    r = R()
    res = r.review("中华人民共和国", classes=[9])
    vs = res["prohibited_check"]["violations"]
    assert len(vs) == 1, f"应只报 1 条，实际 {[(v['keyword'], v['check_key']) for v in vs]}"
    assert vs[0]["keyword"] == "中华人民共和国"
    # 欺骗性整体命中时不再重复报国家名称条件项
    res2 = r.review("中国制造", classes=[9])
    keys = [(v["keyword"], v["check_key"]) for v in res2["prohibited_check"]["violations"]]
    assert len(keys) == 1 and keys[0][1] == "misleading", keys
    print("✅ 子串重复与跨条款重复已消除")


def test_normalization_bypass():
    """分隔符 / 全角 / 简繁不得绕过禁用词检测。"""
    r = R()
    for name in ("中 国", "中·国", "中-国", "中国。", "中國"):
        verdict = r.review(name, classes=[9])["overall"]["verdict"]
        assert verdict == "不得注册", f"{name} 绕过了国名检测：{verdict}"
    print("✅ 分隔符/简繁归一化生效")


def test_hard_block_and_manual_review_not_confused():
    """地名 consequence 同时含"需确认"与"不得注册"，不得被误判成硬阻断。"""
    r = R()
    res = r.review("北京烤鸭", classes=[30])
    assert res["prohibited_check"]["hard_block"] is False
    assert res["prohibited_check"]["manual_review_required"] is True
    print("✅ 硬阻断与条件性判定未串味")


def test_review_api_rejects_empty():
    """空名防护必须在 API 层，不能只在 CLI 层。"""
    r = R()
    for name in ("", " ", "\t"):
        try:
            r.review(name, [9])
        except ValueError:
            continue
        raise AssertionError(f"{name!r} 未被拦截")
    print("✅ 空名在 API 层被拦截")


def test_ethnic_religious_is_conditional():
    """民族宗教元素 → 条件性风险，不能静默落在低风险。"""
    r = R()
    res = r.review("清真牛肉", classes=[29])
    assert res["prohibited_check"]["manual_review_required"] is True
    assert res["overall"]["verdict"] == "条件性风险（需人工确认）", res["overall"]["verdict"]
    print("✅ 民族宗教词触发条件性风险")


def test_single_char_not_falsely_flagged():
    """单字商标（郎/雕等）不得被自造的"名称过短"规则误伤。"""
    r = R()
    res = r.review("郎", classes=[33])
    assert not any("过短" in i["description"] for i in res["distinctiveness_check"]["issues"])
    assert res["overall"]["verdict"] == "低风险"
    print("✅ 单字商标不再误报缺乏显著特征")


def test_cli_rejects_bad_input():
    """空名与越界类别必须被拒绝，而不是给出结论。"""
    import subprocess
    for args in (["   ", "--class", "9"], ["云图智能", "--class", "0"],
                 ["云图智能", "--class", "46"], ["云图智能", "--class", "abc"]):
        out = subprocess.run([sys.executable, "scripts/review.py", *args], cwd=str(ROOT),
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert out.returncode != 0, f"{args} 应被拒绝"
        assert "Traceback" not in out.stderr, f"{args} 不应抛堆栈"
        assert "结论" not in out.stdout, f"{args} 不应输出结论"
    print("✅ 非法输入被友好拒绝")


def test_ai_config_keys():
    """config.yaml 的 ai_analysis 键名必须能真正打开 AI 分析。"""
    import types
    fake = types.ModuleType("anthropic")
    fake.Anthropic = lambda **kw: object()
    sys.modules.setdefault("anthropic", fake)
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
    from scripts.ai_analyzer import AITrademarkAnalyzer
    assert AITrademarkAnalyzer({"enabled": True, "provider": "anthropic"}).enabled is True
    assert AITrademarkAnalyzer({"enabled": False}).enabled is False
    print("✅ AI 配置键名生效")


def test_adapter_minimal_implementation():
    """按文档只实现 search_similar 的适配器必须能被加载。"""
    from references.trademark_api_adapter import TrademarkAPIAdapter, load_adapter

    class Minimal(TrademarkAPIAdapter):
        def search_similar(self, name, classes):
            return []

    import references.trademark_api_adapter as mod
    original = getattr(mod, "Minimal", None)
    mod.Minimal = Minimal
    try:
        adapter = load_adapter({"api": {"adapter_class": "references.trademark_api_adapter.Minimal"}})
        assert adapter is not None
    finally:
        if original is None:
            delattr(mod, "Minimal")
    print("✅ 最小适配器可直接加载")


if __name__ == "__main__":
    print("开始运行回归测试...")
    print("=" * 60)
    tests = [
        test_article_map_consistency,
        test_hard_block_political,
        test_hard_block_misleading,
        test_geographic_conditional,
        test_county_level_geographic,
        test_common_word_not_inflated,
        test_all_45_classes_covered,
        test_descriptive,
        test_generic_by_class,
        test_clean_mark,
        test_similarity_not_configured_honest,
        test_skip_similarity_declared,
        test_cli_direct_run,
        test_batch_and_json,
        test_report_generation,
        test_national_name_tiers,
        test_violation_dedup,
        test_normalization_bypass,
        test_hard_block_and_manual_review_not_confused,
        test_review_api_rejects_empty,
        test_ethnic_religious_is_conditional,
        test_single_char_not_falsely_flagged,
        test_cli_rejects_bad_input,
        test_ai_config_keys,
        test_adapter_minimal_implementation,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"❌ {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            import traceback
            print(f"❌ {t.__name__} 运行错误: {e}")
            traceback.print_exc()
    print("=" * 60)
    if failed:
        print(f"❌ {failed} 个测试失败")
        sys.exit(1)
    print("✅ 所有测试通过")
