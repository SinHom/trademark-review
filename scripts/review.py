#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商标注册成功率审查脚本

基于中国商标法规进行合规性审查，评估注册成功率
"""

import sys
import os
import argparse
import yaml
from pathlib import Path
from typing import List, Dict, Optional
import re

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 导入AI分析器
try:
    from ai_analyzer import AITrademarkAnalyzer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


class TrademarkReviewer:
    """商标审查器"""

    def __init__(self, config_path: Optional[str] = None):
        """初始化审查器"""
        self.skill_dir = Path(__file__).parent.parent

        # 加载配置
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = self.skill_dir / "config.yaml"

        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # 加载风险规则
        self.load_risk_rules()

        # 加载法律法规（后续实现）
        self.laws = {}

        # 初始化AI分析器
        self.ai_analyzer = None
        if AI_AVAILABLE:
            ai_config = self.config.get("trademark_review", {}).get("ai_analysis", {})
            if ai_config.get("enabled", False):
                self.ai_analyzer = AITrademarkAnalyzer(ai_config)
                if self.ai_analyzer.enabled:
                    print("✨ AI辅助分析已启用")

    def load_risk_rules(self):
        """加载风险评估规则"""
        rules_file = self.skill_dir / "references" / "risk_rules.json"
        if rules_file.exists():
            import json
            with open(rules_file, 'r', encoding='utf-8') as f:
                self.risk_rules = json.load(f)
        else:
            # 默认规则
            self.risk_rules = {
                "prohibited_keywords": {
                    "political": ["中国", "中华", "国家", "中央", "全国"],
                    "geographic": [],  # 动态加载县级以上地名
                    "ethnic": ["民族歧视", "宗教"],
                    "misleading": ["特供", "专供", "特制"]
                },
                "descriptive_terms": ["优质", "高级", "顶级", "最好"],
                "generic_terms": []  # 各类别通用名称
            }

    def check_prohibited_clause(self, trademark_name: str) -> Dict:
        """
        检查禁用条款（商标法第十条）

        Returns:
            {
                "passed": bool,
                "violations": List[Dict],  # 违反的条款
                "risk_score": float  # 0-1
            }
        """
        violations = []

        # 1. 检查政治敏感词
        for keyword in self.risk_rules["prohibited_keywords"]["political"]:
            if keyword in trademark_name:
                violations.append({
                    "type": "political",
                    "keyword": keyword,
                    "article": "商标法第十条第一款第一项",
                    "description": "与国家名称相同或近似",
                    "severity": "high"
                })

        # 1.5. 检查国家象征
        national_symbols = self.risk_rules.get("prohibited_keywords", {}).get("national_symbols", [])
        for keyword in national_symbols:
            if keyword in trademark_name:
                violations.append({
                    "type": "national_symbol",
                    "keyword": keyword,
                    "article": "商标法第十条第一款第一项",
                    "description": "与国家象征相同或近似",
                    "severity": "high"
                })

        # 2. 检查地名（县级以上行政区划）
        # 从配置文件读取完整地名列表
        geographic_keywords = []
        prohibited_kw = self.risk_rules.get("prohibited_keywords", {})
        geographic_keywords.extend(prohibited_kw.get("geographic_provincial", []))
        geographic_keywords.extend(prohibited_kw.get("geographic_major_cities", []))

        for keyword in geographic_keywords:
            if keyword in trademark_name:
                violation = {
                    "type": "geographic",
                    "keyword": keyword,
                    "article": "商标法第十条第二款",
                    "description": "含有县级以上行政区划地名",
                    "severity": "medium",
                    "note": "除非地名具有其他含义或作为集体/证明商标"
                }

                # AI辅助分析：判断地名是否有其他含义
                if self.ai_analyzer and self.ai_analyzer.enabled:
                    ai_result = self.ai_analyzer.analyze_geographic_name(trademark_name, keyword)
                    if ai_result.get("has_other_meaning"):
                        violation["ai_analysis"] = ai_result
                        violation["note"] = f"AI分析：{ai_result['explanation']} (置信度: {ai_result['confidence']:.2f})"
                        if ai_result["confidence"] > 0.7:
                            # 高置信度判定有其他含义，降低严重度
                            violation["severity"] = "low"

                violations.append(violation)

        # 3. 检查误导性词汇
        for keyword in self.risk_rules["prohibited_keywords"]["misleading"]:
            if keyword in trademark_name:
                violations.append({
                    "type": "misleading",
                    "keyword": keyword,
                    "article": "商标法第十条第一款第七项",
                    "description": "带有欺骗性，容易使公众对商品产生误认",
                    "severity": "high"
                })

        # 计算风险分数
        if not violations:
            risk_score = 0.0
        else:
            high_count = sum(1 for v in violations if v["severity"] == "high")
            medium_count = sum(1 for v in violations if v["severity"] == "medium")

            # 特殊处理：政治敏感词/国家象征直接判定为高风险
            has_political = any(v["type"] == "political" for v in violations)
            has_national_symbol = any(v.get("keyword") in ["国旗", "国徽", "国歌", "军旗", "军徽", "勋章"]
                                     for v in violations)

            if has_political or has_national_symbol:
                risk_score = 1.0  # 含国家名称/国家象征 → 直接高风险
            elif high_count >= 2:
                risk_score = 1.0  # 2个以上高严重度违规 → 高风险
            elif high_count == 1:
                risk_score = min(1.0, 0.75 + medium_count * 0.1)  # 1个高严重度
            else:
                risk_score = min(0.7, medium_count * 0.35)  # 仅中等严重度

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "risk_score": risk_score
        }

    def check_distinctiveness(self, trademark_name: str, classes: List[int]) -> Dict:
        """
        检查显著性（商标法第十一条）

        Returns:
            {
                "passed": bool,
                "issues": List[Dict],
                "risk_score": float
            }
        """
        issues = []

        # 1. 检查是否为纯描述性词汇
        descriptive_count = 0
        descriptive_terms = self.risk_rules.get("descriptive_terms", {})

        # 如果是字典（嵌套结构），遍历所有分类的词汇
        if isinstance(descriptive_terms, dict):
            all_terms = []
            for category_terms in descriptive_terms.values():
                if isinstance(category_terms, list):
                    all_terms.extend(category_terms)
        else:
            # 如果是列表（扁平结构），直接使用
            all_terms = descriptive_terms

        for term in all_terms:
            if term in trademark_name:
                descriptive_count += 1
                issues.append({
                    "type": "descriptive",
                    "term": term,
                    "article": "商标法第十一条第一款第二项",
                    "description": "仅直接表示商品特点，缺乏显著性",
                    "severity": "medium"
                })

        # 2. 检查长度和组合
        if len(trademark_name) < 2:
            issues.append({
                "type": "too_short",
                "article": "商标法第十一条第一款第三项",
                "description": "过于简单，缺乏显著特征",
                "severity": "medium"
            })

        # 计算风险分数
        if not issues:
            risk_score = 0.0
        elif descriptive_count >= 2:
            risk_score = 0.7  # 多个描述性词汇组合，风险较高（提升从0.6到0.7）
        elif descriptive_count == 1:
            risk_score = 0.4  # 单个描述性词汇（提升从0.2到0.4）
        else:
            risk_score = min(0.5, len(issues) * 0.25)  # 其他问题

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "risk_score": risk_score,
            "note": "如能证明经过使用获得显著特征，仍可注册",
            "ai_analysis": self._ai_analyze_distinctiveness(trademark_name, classes, issues) if self.ai_analyzer else None
        }

    def _ai_analyze_distinctiveness(self, trademark_name: str, classes: List[int], issues: List[Dict]) -> Optional[Dict]:
        """AI辅助显著性分析"""
        if not self.ai_analyzer or not self.ai_analyzer.enabled:
            return None

        try:
            result = self.ai_analyzer.analyze_distinctiveness(trademark_name, classes, issues)
            return result
        except Exception as e:
            print(f"⚠️  AI显著性分析失败: {e}")
            return None

    def check_similarity(self, trademark_name: str, classes: List[int]) -> Dict:
        """
        检查相同/近似商标（商标法第三十条、三十一条）
        需要接入商标查询API

        Returns:
            {
                "passed": bool,
                "similar_marks": List[Dict],
                "risk_score": float
            }
        """
        skip_check = self.config.get("trademark_review", {}).get("review", {}).get("skip_similarity_check", False)

        if skip_check:
            return {
                "passed": True,
                "similar_marks": [],
                "risk_score": 0.0,
                "note": "已跳过近似性检索"
            }

        # 尝试加载API适配器
        try:
            from references.trademark_api_adapter import load_adapter
            adapter = load_adapter(self.config.get("trademark_review", {}))

            similar_marks = adapter.search_similar(trademark_name, classes)

            # 分析近似程度
            high_risk_marks = [m for m in similar_marks if m.get("similarity_score", 0) > 0.8]
            medium_risk_marks = [m for m in similar_marks if 0.6 < m.get("similarity_score", 0) <= 0.8]

            if high_risk_marks:
                risk_score = 0.8
                passed = False
            elif medium_risk_marks:
                risk_score = 0.5
                passed = False
            elif similar_marks:
                risk_score = 0.3
                passed = True
            else:
                risk_score = 0.0
                passed = True

            return {
                "passed": passed,
                "similar_marks": similar_marks[:10],  # 只返回前10个
                "high_risk_count": len(high_risk_marks),
                "medium_risk_count": len(medium_risk_marks),
                "risk_score": risk_score
            }

        except Exception as e:
            print(f"⚠️  商标近似性检索失败: {e}")
            return {
                "passed": None,
                "similar_marks": [],
                "risk_score": 0.0,
                "error": str(e),
                "note": "无法完成近似性检索，建议人工复核"
            }

    def review(self, trademark_name: str, classes: Optional[List[int]] = None) -> Dict:
        """
        完整审查流程

        Args:
            trademark_name: 商标名称
            classes: 商标类别，如 [9, 42]

        Returns:
            完整的审查报告数据
        """
        if classes is None:
            classes = self.config.get("trademark_review", {}).get("default_classes", [9, 35, 42])

        print(f"\n🔍 正在审查商标: {trademark_name}")
        print(f"   类别: {', '.join(map(str, classes))}")
        print("-" * 60)

        # 1. 禁用条款审查
        print("1️⃣  禁用条款审查...")
        prohibited_result = self.check_prohibited_clause(trademark_name)

        # 2. 显著性审查
        print("2️⃣  显著性审查...")
        distinctiveness_result = self.check_distinctiveness(trademark_name, classes)

        # 3. 近似性审查
        print("3️⃣  近似性审查...")
        similarity_result = self.check_similarity(trademark_name, classes)

        # 综合评估
        # 特殊处理：如果禁用条款风险极高（政治敏感/国家象征），直接判高风险
        if prohibited_result["risk_score"] >= 0.9:
            total_risk_score = 1.0
        else:
            total_risk_score = (
                prohibited_result["risk_score"] * 0.4 +
                distinctiveness_result["risk_score"] * 0.3 +
                similarity_result["risk_score"] * 0.3
            )

        # 判断总体风险等级
        thresholds = self.config.get("trademark_review", {}).get("risk_threshold", {})
        high_threshold = thresholds.get("high", 0.7)
        medium_threshold = thresholds.get("medium", 0.4)

        if total_risk_score >= high_threshold:
            risk_level = "高风险"
            recommendation = "不建议注册，存在严重合规问题或高冲突风险"
        elif total_risk_score >= medium_threshold:
            risk_level = "中风险"
            recommendation = "建议修改后注册，或寻求专业代理机构评估"
        else:
            risk_level = "低风险"
            recommendation = "可以注册，但仍建议进行专业检索确认"

        # 计算预估注册成功率
        success_rate = max(0, min(100, int((1 - total_risk_score) * 100)))

        # AI生成修改建议（如果启用且存在问题）
        ai_alternatives = []
        all_issues = (
            prohibited_result.get("violations", []) +
            distinctiveness_result.get("issues", [])
        )
        if self.ai_analyzer and self.ai_analyzer.enabled and all_issues:
            print("🤖 AI正在生成修改建议...")
            ai_alternatives = self.ai_analyzer.generate_alternatives(
                trademark_name, all_issues, classes
            )

        result = {
            "trademark_name": trademark_name,
            "classes": classes,
            "review_date": self._get_current_date(),
            "prohibited_check": prohibited_result,
            "distinctiveness_check": distinctiveness_result,
            "similarity_check": similarity_result,
            "overall": {
                "risk_score": round(total_risk_score, 2),
                "risk_level": risk_level,
                "success_rate": success_rate,
                "recommendation": recommendation,
                "ai_alternatives": ai_alternatives if ai_alternatives else None
            }
        }

        # 打印摘要
        self._print_summary(result)

        return result

    def _print_summary(self, result: Dict):
        """打印审查摘要"""
        print("\n" + "=" * 60)
        print(f"📊 审查结果摘要")
        print("=" * 60)

        overall = result["overall"]
        print(f"商标名称: {result['trademark_name']}")
        print(f"风险等级: {overall['risk_level']}")
        print(f"预估成功率: {overall['success_rate']}%")
        print(f"建议: {overall['recommendation']}")

        print("\n详细问题:")

        # 禁用条款
        violations = result["prohibited_check"]["violations"]
        if violations:
            print(f"  ❌ 禁用条款: 发现 {len(violations)} 个违规项")
            for v in violations[:3]:
                print(f"     - {v['description']} ({v['article']})")
        else:
            print(f"  ✅ 禁用条款: 通过")

        # 显著性
        issues = result["distinctiveness_check"]["issues"]
        if issues:
            print(f"  ⚠️  显著性: 发现 {len(issues)} 个问题")
            for i in issues[:3]:
                print(f"     - {i['description']}")
        else:
            print(f"  ✅ 显著性: 通过")

        # 近似性
        similar = result["similarity_check"]["similar_marks"]
        if similar:
            print(f"  ⚠️  近似商标: 发现 {len(similar)} 个可能冲突的商标")
            high_risk = result["similarity_check"].get("high_risk_count", 0)
            if high_risk > 0:
                print(f"     - 其中高度近似: {high_risk} 个")
        else:
            print(f"  ✅ 近似性: 未发现冲突")

        print("=" * 60)

    def _get_current_date(self) -> str:
        """获取当前日期"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="商标注册成功率审查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "华为云"
  %(prog)s "华为云" --class 9,42
  %(prog)s "华为云" "阿里云" --report
  %(prog)s --batch trademarks.txt --output report.json
        """
    )

    parser.add_argument(
        "trademarks",
        nargs="*",
        help="商标名称（可输入多个）"
    )

    parser.add_argument(
        "--class", "--classes",
        dest="classes",
        help="商标类别，用逗号分隔，如: 9,35,42"
    )

    parser.add_argument(
        "--batch",
        help="批量审查，从文件读取商标列表（每行一个）"
    )

    parser.add_argument(
        "--report",
        action="store_true",
        help="生成完整报告"
    )

    parser.add_argument(
        "--format",
        choices=["docx", "pdf", "json"],
        default="docx",
        help="报告格式（默认: docx）"
    )

    parser.add_argument(
        "--output",
        help="输出文件路径"
    )

    parser.add_argument(
        "--config",
        help="配置文件路径"
    )

    parser.add_argument(
        "--skip-similarity",
        action="store_true",
        help="跳过近似性检索"
    )

    args = parser.parse_args()

    # 准备商标列表
    trademarks = []
    if args.batch:
        with open(args.batch, 'r', encoding='utf-8') as f:
            trademarks = [line.strip() for line in f if line.strip()]
    elif args.trademarks:
        trademarks = args.trademarks
    else:
        parser.print_help()
        return

    # 解析类别
    classes = None
    if args.classes:
        classes = [int(c.strip()) for c in args.classes.split(",")]

    # 创建审查器
    reviewer = TrademarkReviewer(config_path=args.config)

    # 如果设置了跳过近似性检索
    if args.skip_similarity:
        reviewer.config.setdefault("trademark_review", {}).setdefault("review", {})["skip_similarity_check"] = True

    # 执行审查
    results = []
    for trademark in trademarks:
        result = reviewer.review(trademark, classes)
        results.append(result)

    # 生成报告
    if args.report:
        print("\n📄 正在生成报告...")
        from report_generator import generate_report

        output_path = args.output
        if not output_path:
            timestamp = result["review_date"].replace("-", "")
            output_path = f"商标审查报告_{timestamp}.{args.format}"

        generate_report(results, output_path, format=args.format)
        print(f"✅ 报告已生成: {output_path}")

    # JSON输出
    elif args.output:
        import json
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"✅ 结果已保存: {args.output}")


if __name__ == "__main__":
    main()
