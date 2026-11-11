#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商标审查回归测试

测试修复后的审查引擎是否正确工作
"""

import sys
import os
from pathlib import Path

# 添加父目录到path，支持多种运行方式
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(parent_dir / "scripts"))

# 设置工作目录（确保能找到config.yaml等文件）
os.chdir(parent_dir)

from scripts.review import TrademarkReviewer


def test_descriptive_detection():
    """测试描述性词汇检测（BUG修复1）"""
    reviewer = TrademarkReviewer()
    result = reviewer.review("优质服务", classes=[35])

    # 应该检测到"优质"这个描述性词汇
    assert not result["distinctiveness_check"]["passed"], "应该检测到描述性词汇"
    assert len(result["distinctiveness_check"]["issues"]) > 0, "应该有显著性问题"
    assert result["overall"]["risk_score"] > 0, "风险分数应该>0"
    print("✅ 测试1通过: 描述性词汇检测正常")


def test_political_high_risk():
    """测试政治敏感词高风险判定（BUG修复2）"""
    reviewer = TrademarkReviewer()
    result = reviewer.review("中国制造", classes=[9])

    # 应该判定为高风险
    assert result["overall"]["risk_level"] == "高风险", "含国家名称应判定为高风险"
    assert result["overall"]["success_rate"] <= 30, f"成功率应<=30%，实际{result['overall']['success_rate']}%"
    assert result["prohibited_check"]["risk_score"] >= 0.9, "禁用条款风险应>=0.9"
    print("✅ 测试2通过: 政治敏感词正确判定为高风险")


def test_geographic_detection():
    """测试地名检测覆盖（BUG修复3）"""
    reviewer = TrademarkReviewer()

    # 测试省级地名
    result1 = reviewer.review("浙江餐饮", classes=[43])
    assert not result1["prohibited_check"]["passed"], "应该检测到省级地名"

    # 测试地级市
    result2 = reviewer.review("杭州美食", classes=[30])
    assert not result2["prohibited_check"]["passed"], "应该检测到地级市地名"

    print("✅ 测试3通过: 地名检测覆盖正常")


def test_combined_issues():
    """测试组合问题"""
    reviewer = TrademarkReviewer()
    result = reviewer.review("中国优质服务", classes=[35])

    # 应该同时检测到政治敏感词和描述性词汇
    assert not result["prohibited_check"]["passed"], "应该检测到政治敏感词"
    assert not result["distinctiveness_check"]["passed"], "应该检测到描述性词汇"
    assert result["overall"]["risk_level"] == "高风险", "组合问题应判定为高风险"
    print("✅ 测试4通过: 组合问题检测正常")


def test_clean_trademark():
    """测试正常商标"""
    reviewer = TrademarkReviewer()
    result = reviewer.review("云图智能", classes=[9, 42])

    # 应该通过所有检查（如果没有近似商标）
    assert result["prohibited_check"]["passed"], "正常商标应通过禁用条款"
    assert result["distinctiveness_check"]["passed"], "正常商标应通过显著性检查"
    assert result["overall"]["risk_level"] == "低风险", "正常商标应为低风险"
    print("✅ 测试5通过: 正常商标判定正确")


def test_misleading_keywords():
    """测试误导性词汇"""
    reviewer = TrademarkReviewer()
    result = reviewer.review("特供产品", classes=[35])

    assert not result["prohibited_check"]["passed"], "应该检测到误导性词汇"
    violations = result["prohibited_check"]["violations"]
    assert any(v["type"] == "misleading" for v in violations), "应该标记为误导性"
    print("✅ 测试6通过: 误导性词汇检测正常")


def test_multiple_descriptive_terms():
    """测试多个描述性词汇"""
    reviewer = TrademarkReviewer()
    result = reviewer.review("优质高效服务", classes=[35])

    # 应该检测到"优质"和"高效"两个描述性词汇
    issues = result["distinctiveness_check"]["issues"]
    assert len(issues) >= 2, f"应该检测到至少2个描述性词汇，实际{len(issues)}个"
    # 多个描述性词汇的风险分数应该>=0.5（显著性维度）
    assert result["distinctiveness_check"]["risk_score"] >= 0.5, \
        f"多个描述性词汇风险应>=0.5，实际{result['distinctiveness_check']['risk_score']}"
    print("✅ 测试7通过: 多描述性词汇检测正常")


def test_short_trademark():
    """测试过短商标"""
    reviewer = TrademarkReviewer()
    result = reviewer.review("A", classes=[9])

    # 应该检测到长度问题
    issues = result["distinctiveness_check"]["issues"]
    assert any(i["type"] == "too_short" for i in issues), "应该检测到长度过短"
    print("✅ 测试8通过: 长度检测正常")


def test_national_symbols():
    """测试国家象征检测"""
    reviewer = TrademarkReviewer()
    result = reviewer.review("国旗品牌", classes=[25])

    assert not result["prohibited_check"]["passed"], "应该检测到国家象征"
    assert result["overall"]["risk_level"] == "高风险", "国家象征应判定为高风险"
    print("✅ 测试9通过: 国家象征检测正常")


def test_batch_processing():
    """测试批量处理"""
    reviewer = TrademarkReviewer()
    trademarks = ["云图智能", "中国制造", "优质服务"]
    results = []

    for tm in trademarks:
        result = reviewer.review(tm, classes=[9])
        results.append(result)

    assert len(results) == 3, "应该返回3个结果"
    assert results[0]["overall"]["risk_level"] == "低风险", "云图智能应为低风险"
    assert results[1]["overall"]["risk_level"] == "高风险", "中国制造应为高风险"
    assert not results[2]["distinctiveness_check"]["passed"], "优质服务应有显著性问题"
    print("✅ 测试10通过: 批量处理正常")


if __name__ == "__main__":
    print("开始运行回归测试...")
    print("=" * 60)

    try:
        test_descriptive_detection()
        test_political_high_risk()
        test_geographic_detection()
        test_combined_issues()
        test_clean_trademark()
        test_misleading_keywords()
        test_multiple_descriptive_terms()
        test_short_trademark()
        test_national_symbols()
        test_batch_processing()

        print("=" * 60)
        print("✅ 所有测试通过！")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
