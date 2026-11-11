#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商标合规审查引擎

设计原则：
1. 法条引用唯一来源 = references/article_map.json，代码内不硬编码条号。
2. 结论分级：不得注册（硬阻断） / 条件性风险（需人工确认） / 风险分级（启发式）。
3. 未执行的检查必须显式标注"未执行"，不得输出"未发现冲突"。
4. 成功率是启发式估算，不是统计数据；命中禁用条款时不给出成功率。
"""

import sys
import os
import json
import re
import unicodedata
import argparse
from pathlib import Path
from typing import List, Dict, Optional

# 保证以 `python scripts/review.py` 直接运行时也能导入 references 包
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import yaml

# 设置 Windows 控制台 UTF-8 编码
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        pass

try:
    from scripts.ai_analyzer import AITrademarkAnalyzer
    AI_AVAILABLE = True
except ImportError:
    try:
        from ai_analyzer import AITrademarkAnalyzer
        AI_AVAILABLE = True
    except ImportError:
        AI_AVAILABLE = False


class TrademarkReviewer:
    """商标合规审查器"""

    def __init__(self, config_path: Optional[str] = None):
        self.skill_dir = _PROJECT_ROOT

        config_file = Path(config_path) if config_path else self.skill_dir / "config.yaml"
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f) or {}

        cfg = self.config.get("trademark_review", {})
        self.law_version = cfg.get("law", {}).get("version") or "2019"

        self.article_map = self._load_article_map()
        self.risk_rules = self._load_risk_rules()

        self.ai_analyzer = None
        if AI_AVAILABLE:
            ai_config = cfg.get("ai_analysis", {})
            # 兼容历史键名 enable_ai_analysis
            if ai_config.get("enabled", ai_config.get("enable_ai_analysis", False)):
                self.ai_analyzer = AITrademarkAnalyzer(ai_config)
                if self.ai_analyzer.enabled:
                    print("✨ AI辅助分析已启用")

    # ---------- 资源加载 ----------

    def _load_article_map(self) -> Dict:
        path = self.skill_dir / "references" / "article_map.json"
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_risk_rules(self) -> Dict:
        path = self.skill_dir / "references" / "risk_rules.json"
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_geo(self) -> Dict:
        path = self.skill_dir / "references" / "geographic_names.json"
        if not path.exists():
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ---------- 文本归一化 ----------

    _SEPARATOR_RE = re.compile(r"[\s·・.。\-_—/\\|、，,()（）\[\]【】{}<>《》\"'“”‘’]+")

    # 禁用词检测用的繁→简映射（只覆盖禁用/敏感词涉及的字，不做全文转换）
    _TRAD_TO_SIMP = str.maketrans({
        "國": "国", "華": "华", "黨": "党", "軍": "军", "會": "会",
        "聯": "联", "紅": "红", "爾": "尔", "醫": "医", "學": "学",
        "體": "体", "區": "区", "縣": "县", "鎮": "镇", "鄉": "乡",
        "員": "员", "長": "长", "門": "门", "東": "东", "廣": "广",
        "臺": "台", "灣": "湾", "慶": "庆", "濟": "济", "陽": "阳",
        "鐵": "铁", "銀": "银", "龍": "龙", "鳳": "凤", "馬": "马",
    })

    @classmethod
    def normalize_name(cls, name: str) -> str:
        """
        归一化商标名称后再做关键词匹配，防止"中 国""中·国""中国。"
        "中國"等分隔符 / 全角半角 / 简繁混写绕过禁用词检测。
        """
        if not name:
            return ""
        s = unicodedata.normalize("NFKC", name).strip().translate(cls._TRAD_TO_SIMP)
        return cls._SEPARATOR_RE.sub("", s)

    # ---------- 法条引用 ----------

    def cite(self, check_key: str) -> Dict[str, str]:
        """
        返回某检查项在现行版与 2026 版的条号。

        返回：
          {"current": "《商标法》（2019年修正）第十条第一款第一项",
           "counterpart": "《商标法》（2026年修订，2027-01-01施行）第十五条第一款第二项",
           "display": "《商标法》（2019年修正）第十条第一款第一项〔2026年修订：第十五条第一款第二项〕"}
        """
        versions = self.article_map["versions"]
        mapping = self.article_map["mapping"].get(check_key)
        if not mapping:
            return {"current": f"未登记条号:{check_key}", "counterpart": "", "display": f"未登记条号:{check_key}"}

        cur_v = self.law_version
        other_v = "2026" if cur_v == "2019" else "2019"
        cur_num = mapping.get(cur_v)
        other_num = mapping.get(other_v)

        cur_label = versions[cur_v]["label"]
        other_label = versions[other_v]["label"]
        other_eff = versions[other_v]["effective_from"]

        current = f"《商标法》（{cur_label}）{cur_num}" if cur_num else ""
        counterpart = f"《商标法》（{other_label}，{other_eff}施行）{other_num}" if other_num else ""

        if current and counterpart:
            display = f"{current}〔{other_label}：{other_num}〕"
        elif current:
            display = current
        else:
            display = counterpart

        return {"current": current, "counterpart": counterpart, "display": display}

    def _violation(self, check_key: str, **kwargs) -> Dict:
        cite = self.cite(check_key)
        v = {
            "check_key": check_key,
            "article_current": cite["current"],
            "article_counterpart": cite["counterpart"],
            "article": cite["display"],
        }
        v.update(kwargs)
        return v

    # ---------- 审查项 ----------

    def check_prohibited_clause(self, trademark_name: str) -> Dict:
        """
        禁用标志审查，分三档：

        1. 绝对障碍（不得注册）：名称整体即国家名称，或与国家名称/国家象征
           高度接近，或属欺骗性标志。
        2. 条件性障碍（需人工确认）：含国家名称但整体不构成近似（指南第三章
           列举了描述客观事物、报刊名称、经批准的企事业简称等例外）、含政治
           敏感词、含民族宗教元素、含县级以上地名。
        3. 低置信提示：常见词形式的县级地名，不改变结论。
        """
        violations = []
        kw_rules = self.risk_rules.get("prohibited_keywords", {})
        normalized = self.normalize_name(trademark_name)

        # 国家名称：仅"整体即国名"构成绝对障碍；其余一律条件性。
        # 指南第三章：含国家名称但整体不构成近似的，存在描述客观事物、
        # 报刊名称、经批准的企事业单位简称等例外（如中国移动、中华铅笔）。
        national_terms = [k for k in kw_rules.get("national_name", []) if k and k in normalized]
        # 最长匹配优先：命中"中华人民共和国"时不再重复报"中国""中华"
        longest = max(national_terms, key=len) if national_terms else None
        for keyword in national_terms:
            if keyword != longest:
                continue
            if normalized == keyword:
                violations.append(self._violation(
                    "national_name", keyword=keyword,
                    description=f"与我国国家名称「{keyword}」相同",
                    severity="high", consequence="不得注册"))
            else:
                violations.append(self._violation(
                    "national_name", keyword=keyword,
                    description=f"含有国家名称「{keyword}」，整体是否构成近似需人工判断",
                    severity="medium", consequence="需确认是否整体近似或落入法定例外",
                    note="指南第三章：描述客观事物、报刊/期刊名称、经批准的企事业单位简称等情形一般不适用禁用条款"))

        for keyword in kw_rules.get("national_symbols", []):
            if keyword in normalized:
                violations.append(self._violation(
                    "national_name", keyword=keyword,
                    description="与国家象征相同或近似",
                    severity="high", consequence="不得注册"))

        for keyword in kw_rules.get("misleading", []):
            if keyword and keyword in normalized:
                violations.append(self._violation(
                    "misleading", keyword=keyword,
                    description="带有欺骗性，容易使公众产生误认",
                    severity="high", consequence="不得注册"))

        # 已被欺骗性条款整体命中的（如"中国制造"命中"中国"），
        # 不再重复计国家名称条件项——避免同一标识报两条不同依据
        misleading_keywords = [k for k in kw_rules.get("misleading", [])
                               if k and k in normalized]
        violations = [v for v in violations
                      if not (v.get("check_key") == "national_name"
                              and v.get("consequence") != "不得注册"
                              and any(v.get("keyword", "") in mk
                                      for mk in misleading_keywords))]

        # 政治敏感词：不等于国家名称，不构成绝对禁用
        for keyword in kw_rules.get("political_sensitive", []):
            if keyword in normalized:
                violations.append(self._violation(
                    "public_order", keyword=keyword,
                    description=f"含有政治敏感词「{keyword}」，需判断是否损害国家尊严或造成误认",
                    severity="medium", consequence="需确认是否构成不良影响"))

        for keyword in kw_rules.get("ethnic_religious", []):
            if keyword in normalized:
                violations.append(self._violation(
                    "ethnic_discrimination", keyword=keyword,
                    description=f"含有民族/宗教元素「{keyword}」，需判断是否构成民族歧视或不良影响",
                    severity="medium", consequence="需确认是否带有民族歧视性或不良影响"))

        # 地名：属条件性障碍（具有其他含义的除外）
        geo = self._load_geo()
        geo_hits = {}   # keyword -> (severity, kind)
        # 已被国家名称整体覆盖的部分不再参与地名匹配
        # （如"中华人民共和国"中的"共和"不是县级地名"共和县"）
        geo_scope = normalized
        for hit in national_terms:
            geo_scope = geo_scope.replace(hit, "")

        if geo:
            for name in geo.get("provinces", []):
                if name and name in geo_scope:
                    geo_hits[name] = ("medium", "省级行政区")
            for name in geo.get("prefecture_cities", []):
                if name and name in geo_scope:
                    geo_hits.setdefault(name, ("medium", "地级行政区"))
            for name in geo.get("counties_full", []):
                if name and name in geo_scope:
                    geo_hits.setdefault(name, ("medium", "县级行政区"))
            common_bare = set(geo.get("common_bare", []))
            for name in geo.get("counties_bare", []):
                if len(name) < 2:
                    continue
                if name in geo_scope:
                    if name in common_bare:
                        geo_hits.setdefault(name, ("low", "县级行政区（常见词，低置信）"))
                    else:
                        geo_hits.setdefault(name, ("medium", "县级行政区"))
        else:
            for name in kw_rules.get("geographic_provincial", []) + kw_rules.get("geographic_major_cities", []):
                if name in trademark_name:
                    geo_hits[name] = ("medium", "省级/地级行政区")

        for keyword, (severity, kind) in geo_hits.items():
            if severity == "low":
                consequence = "低置信提示：可能含县级地名，不改变结论"
            else:
                consequence = "需确认是否具有其他含义；无其他含义则不得注册"

            v = self._violation(
                "geographic_name", keyword=keyword,
                description=f"含有{kind}名称「{keyword}」",
                severity=severity,
                consequence=consequence)

            if self.ai_analyzer and self.ai_analyzer.enabled:
                ai_result = self.ai_analyzer.analyze_geographic_name(trademark_name, keyword)
                v["ai_analysis"] = ai_result
                if ai_result.get("has_other_meaning") and ai_result.get("confidence", 0) > 0.7:
                    v["severity"] = "low"
                    v["consequence"] = "AI判断具有其他含义（需人工复核）"

            violations.append(v)

        # 含国家名称但非整体相同：结论未决（取决于能否落入法定例外）
        pending_national = any(
            v.get("check_key") == "national_name"
            and str(v.get("consequence", "")).startswith("需确认")
            for v in violations)

        hard_block = any(v["consequence"] == "不得注册" for v in violations)
        manual_review = any(v["consequence"].startswith("需确认") for v in violations)
        if hard_block:
            risk_score = 1.0
        elif manual_review:
            risk_score = 0.5
        elif violations:
            risk_score = 0.3
        else:
            risk_score = 0.0

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "hard_block": hard_block,
            "manual_review_required": manual_review,
            "pending_national": pending_national,
            "risk_score": risk_score,
        }

    def check_distinctiveness(self, trademark_name: str, classes: List[int]) -> Dict:
        """显著特征审查（含按类别的通用名称匹配）。"""
        issues = []
        descriptive_count = 0

        # 1. 描述性词汇
        descriptive_terms = self.risk_rules.get("descriptive_terms", {})
        all_terms = []
        if isinstance(descriptive_terms, dict):
            for category_terms in descriptive_terms.values():
                if isinstance(category_terms, list):
                    all_terms.extend(category_terms)
        else:
            all_terms = descriptive_terms

        for term in all_terms:
            if not term:
                continue
            if len(term) == 1 and trademark_name != term:
                # 单字词噪声过大，只在整名相同时提示
                continue
            if term in trademark_name:
                descriptive_count += 1
                issues.append(self._violation(
                    "distinctiveness_descriptive", term=term,
                    description=f"含描述性词汇「{term}」，可能仅直接表示商品特点",
                    severity="medium"))

        # 2. 按类别的通用名称
        generic_by_class = self.risk_rules.get("generic_terms_by_class", {})
        for cls in classes:
            for term in generic_by_class.get(str(cls), []):
                if not term or term not in trademark_name:
                    continue
                if len(term) == 1:
                    # 单字通用词噪声过大，仅在同名时提示
                    if trademark_name != term:
                        continue
                if trademark_name == term:
                    severity = "high"
                    desc = f"与第{cls}类商品/服务的通用名称「{term}」完全相同"
                else:
                    severity = "medium"
                    desc = f"含第{cls}类通用名称「{term}」"
                issues.append(self._violation(
                    "distinctiveness_generic", term=term, class_no=cls,
                    description=desc, severity=severity))

        if not issues:
            risk_score = 0.0
        else:
            high = sum(1 for i in issues if i["severity"] == "high")
            if high:
                risk_score = 0.9
            elif descriptive_count >= 2:
                risk_score = 0.7
            elif descriptive_count == 1:
                risk_score = 0.4
            else:
                risk_score = min(0.6, len(issues) * 0.3)

        # 判断是否"整体仅由通用名称/描述性词汇构成"
        residual = trademark_name
        for issue in issues:
            term = issue.get("term")
            if term:
                residual = residual.replace(term, "")
        whole_descriptive = bool(issues) and residual.strip() == ""

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "risk_score": risk_score,
            "whole_descriptive": whole_descriptive,
            "note": "经使用取得显著特征并便于识别的，仍可注册；需提供使用证据。",
            "ai_analysis": self._ai_analyze_distinctiveness(trademark_name, classes, issues) if self.ai_analyzer else None,
        }

    def _ai_analyze_distinctiveness(self, trademark_name, classes, issues):
        if not self.ai_analyzer or not self.ai_analyzer.enabled:
            return None
        try:
            return self.ai_analyzer.analyze_distinctiveness(trademark_name, classes, issues)
        except Exception as e:
            print(f"⚠️  AI显著性分析失败: {e}")
            return None

    def check_similarity(self, trademark_name: str, classes: List[int]) -> Dict:
        """
        在先商标检索。

        status 取值：
          ok              检索完成
          skipped         用户显式跳过
          not_configured  未配置数据源（不返回任何虚构结果）
          error           检索异常（必须显式暴露）
        """
        skip_check = (self.config.get("trademark_review", {})
                      .get("review", {}).get("skip_similarity_check", False))
        if skip_check:
            return {"status": "skipped", "passed": None, "similar_marks": [],
                    "risk_score": 0.0, "note": "用户已跳过近似性检索"}

        try:
            from references.trademark_api_adapter import load_adapter
        except ImportError as e:
            return {"status": "error", "passed": None, "similar_marks": [],
                    "risk_score": 0.0, "error": f"适配器模块导入失败: {e}"}

        try:
            adapter = load_adapter(self.config.get("trademark_review", {}))
        except Exception as e:
            return {"status": "error", "passed": None, "similar_marks": [],
                    "risk_score": 0.0, "error": f"适配器加载失败: {e}"}

        if adapter is None:
            return {"status": "not_configured", "passed": None, "similar_marks": [],
                    "risk_score": 0.0,
                    "error": "未配置商标数据源（config.yaml → trademark_review.api.adapter_class）"}

        try:
            marks = adapter.search_similar(trademark_name, classes) or []
        except Exception as e:
            return {"status": "error", "passed": None, "similar_marks": [],
                    "risk_score": 0.0, "error": f"接口调用失败: {e}"}

        thresholds = self.risk_rules.get("similarity_thresholds", {})
        high_threshold = thresholds.get("high_risk", 0.8)
        medium_threshold = thresholds.get("medium_risk", 0.6)

        high = [m for m in marks
                if m.get("similarity_score", 0) > high_threshold]
        medium = [m for m in marks
                  if medium_threshold < m.get("similarity_score", 0) <= high_threshold]

        if high:
            risk_score, passed = 0.8, False
        elif medium:
            risk_score, passed = 0.5, False
        elif marks:
            risk_score, passed = 0.3, True
        else:
            risk_score, passed = 0.0, True

        return {
            "status": "ok",
            "passed": passed,
            "similar_marks": marks[:10],
            "high_risk_count": len(high),
            "medium_risk_count": len(medium),
            "risk_score": risk_score,
            "article": self.cite("similar_marks")["display"],
        }

    # ---------- 主流程 ----------

    def review(self, trademark_name: str, classes: Optional[List[int]] = None) -> Dict:
        if not trademark_name or not trademark_name.strip():
            raise ValueError("商标名称不能为空或仅含空白字符")
        trademark_name = trademark_name.strip()
        if classes is None:
            classes = (self.config.get("trademark_review", {})
                       .get("default_classes", [9, 35, 42]))

        print(f"\n🔍 正在审查商标: {trademark_name}")
        print(f"   类别: {', '.join(map(str, classes))}")
        print(f"   依据版本: {self.article_map['versions'][self.law_version]['label']}")
        print("-" * 60)

        print("1️⃣  禁用标志审查...")
        prohibited = self.check_prohibited_clause(trademark_name)
        print("2️⃣  显著特征审查...")
        distinctive = self.check_distinctiveness(trademark_name, classes)
        print("3️⃣  在先商标检索...")
        similarity = self.check_similarity(trademark_name, classes)

        hard_block = prohibited["hard_block"]
        manual_review = prohibited["manual_review_required"]
        pending_national = prohibited.get("pending_national", False)
        sim_status = similarity["status"]
        completeness = "complete" if sim_status == "ok" else "partial"

        if hard_block:
            verdict = "不得注册"
            risk_level = "高风险"
            total_risk_score = 1.0
            success_rate = None
            recommendation = "命中禁用标志条款，不得注册；建议更换名称。"
        else:
            weights = self.risk_rules.get("risk_weights", {})
            w_prohibited = weights.get("prohibited_clause", 0.4)
            w_distinctive = weights.get("distinctiveness", 0.3)
            w_similarity = weights.get("similarity", 0.3)
            total_risk_score = (
                prohibited["risk_score"] * w_prohibited +
                distinctive["risk_score"] * w_distinctive +
                similarity["risk_score"] * w_similarity
            )
            if manual_review:
                total_risk_score = max(total_risk_score, 0.45)

            issues = distinctive.get("issues", [])
            generic_exact = any(
                i.get("check_key") == "distinctiveness_generic" and i.get("severity") == "high"
                for i in issues)
            whole_descriptive = distinctive.get("whole_descriptive", False)

            thresholds = (self.config.get("trademark_review", {})
                          .get("risk_threshold", {}))
            high_t = thresholds.get("high", 0.7)
            medium_t = thresholds.get("medium", 0.4)

            if generic_exact or whole_descriptive:
                verdict = "高风险（缺乏显著特征）"
                risk_level = "高风险"
                total_risk_score = max(total_risk_score, 0.85)
                recommendation = ("名称整体由通用名称或描述性词汇构成，原则上不得注册；"
                                  "如能证明经使用已取得显著特征并便于识别，可尝试申请并提供使用证据。")
            elif total_risk_score >= high_t:
                verdict = "高风险"
                risk_level = "高风险"
                recommendation = "存在较高驳回风险，建议修改名称或咨询代理机构。"
            elif total_risk_score >= medium_t:
                verdict = "中风险"
                risk_level = "中风险"
                recommendation = "存在需要处理的风险点，建议修改后申请或先做专业检索。"
            else:
                verdict = "低风险"
                risk_level = "低风险"
                recommendation = "规则层面未发现明显障碍；仍需专业检索确认在先商标。"

            if manual_review and not (generic_exact or whole_descriptive):
                verdict = "条件性风险（需人工确认）"
                recommendation = self._manual_review_advice(prohibited)
            success_rate = max(0, min(100, int((1 - total_risk_score) * 100)))
            if completeness != "complete":
                # 未做在先商标检索时，不给满分结论
                success_rate = min(success_rate, 80)
            if pending_national:
                success_rate = None

        caveats = []
        if sim_status == "not_configured":
            caveats.append("在先商标未检索：未配置数据源，本结论不含冲突判断。")
        elif sim_status == "error":
            caveats.append(f"在先商标检索失败：{similarity.get('error')}，本结论不含冲突判断。")
        elif sim_status == "skipped":
            caveats.append("在先商标检索被跳过，本结论不含冲突判断。")

        ai_alternatives = []
        all_issues = prohibited.get("violations", []) + distinctive.get("issues", [])
        if self.ai_analyzer and self.ai_analyzer.enabled and all_issues:
            print("🤖 AI正在生成修改建议...")
            ai_alternatives = self.ai_analyzer.generate_alternatives(
                trademark_name, all_issues, classes)

        versions = self.article_map["versions"]
        cur_v = self.law_version
        other_v = "2026" if cur_v == "2019" else "2019"

        result = {
            "trademark_name": trademark_name,
            "classes": classes,
            "review_date": self._today(),
            "data_provenance": self._data_provenance(),
            "coverage": self._coverage_report(prohibited, distinctive, similarity),
            "law": {
                "version": cur_v,
                "label": versions[cur_v]["label"],
                "effective_from": versions[cur_v]["effective_from"],
                "counterpart_version": other_v,
                "counterpart_label": versions[other_v]["label"],
                "counterpart_effective_from": versions[other_v]["effective_from"],
                "note": ("结论按现行有效版本作出；括号内并列标注 2026 年修订版条号。"
                         "2026 年修订版自 2027-01-01 起施行。"),
            },
            "prohibited_check": prohibited,
            "distinctiveness_check": distinctive,
            "similarity_check": similarity,
            "overall": {
                "verdict": verdict,
                "risk_level": risk_level,
                "risk_score": round(total_risk_score, 2),
                "success_rate": success_rate,
                "success_rate_basis": "启发式估算，非统计数据；命中禁用条款时不适用",
                "completeness": completeness,
                "caveats": caveats,
                "recommendation": recommendation,
                "ai_alternatives": ai_alternatives or None,
            },
        }

        self._print_summary(result)
        return result

    def _print_summary(self, result: Dict):
        overall = result["overall"]
        sim = result["similarity_check"]

        print("\n" + "=" * 60)
        print("📊 审查结果摘要")
        print("=" * 60)
        print(f"商标名称: {result['trademark_name']}")
        print(f"审查依据: {result['law']['label']}（{result['law']['effective_from']} 施行）")
        print(f"结论: {overall['verdict']}")
        if overall["success_rate"] is None:
            if result["overall"].get("verdict") == "不得注册":
                print("预估成功率: 不适用（命中禁用条款）")
            else:
                print("预估成功率: 不适用（结论未决，取决于能否落入法定例外）")
        else:
            print(f"预估成功率: {overall['success_rate']}%（启发式估算，非统计）")
        print(f"建议: {overall['recommendation']}")

        print("\n逐项结果:")

        violations = result["prohibited_check"]["violations"]
        if violations:
            high_like = [v for v in violations if v.get("severity") != "low"]
            if high_like:
                print(f"  ❌ 禁用标志: {len(high_like)} 项")
            else:
                print(f"  ℹ️  禁用标志: {len(violations)} 项低置信提示（不改变结论）")
            for v in violations[:5]:
                print(f"     - {v['description']}")
                print(f"       依据: {v['article']}")
        else:
            print("  ✅ 禁用标志: 未命中")

        issues = result["distinctiveness_check"]["issues"]
        if issues:
            print(f"  ⚠️  显著特征: {len(issues)} 项")
            for i in issues[:5]:
                print(f"     - {i['description']}")
                print(f"       依据: {i['article']}")
        else:
            print("  ✅ 显著特征: 未发现规则层问题")

        status = sim["status"]
        if status == "ok":
            marks = sim.get("similar_marks", [])
            if marks:
                print(f"  ⚠️  在先商标: 发现 {len(marks)} 条可能冲突")
                if sim.get("high_risk_count"):
                    print(f"     - 高度近似: {sim['high_risk_count']} 条")
                print(f"       依据: {sim.get('article','')}")
            else:
                print("  ✅ 在先商标: 检索完成，未发现冲突")
        elif status == "skipped":
            print("  ⏭️  在先商标: 已跳过（结论不含冲突判断）")
        elif status == "not_configured":
            print("  ⚠️  在先商标: 未检索（未配置数据源）")
            print("      → 本结论不含在先商标冲突判断")
        else:
            print(f"  ❌ 在先商标: 检索失败（{sim.get('error')}）")
            print("      → 本结论不含在先商标冲突判断")

        if overall.get("caveats"):
            print("\n⚠️  结论边界:")
            for c in overall["caveats"]:
                print(f"  - {c}")

        coverage = result.get("coverage")
        if coverage:
            print("\n📋 本次检查范围:")
            for item in coverage["checked"]:
                print(f"  ✅ {item}")
            for item in coverage["not_checked"]:
                print(f"  ⛔ {item}")

        prov = result.get("data_provenance")
        if prov:
            print(f"\n🗂  规则库: v{prov.get('rules_version')}（更新于 {prov.get('rules_updated')}）"
                  f"，条号映射截至 {prov.get('article_map_as_of')}")

        if overall.get("ai_alternatives"):
            print("\n🤖 AI修改建议:")
            for i, alt in enumerate(overall["ai_alternatives"][:5], 1):
                print(f"  {i}. {alt}")

        print("=" * 60)

    def _data_provenance(self) -> Dict:
        """
        数据新鲜度与来源。报告里必须写明规则库版本和生成日期，
        让读者能判断"这份结论是基于什么时候的规则算出来的"。
        """
        rules_path = self.skill_dir / "references" / "risk_rules.json"
        geo_path = self.skill_dir / "references" / "geographic_names.json"
        law_path = self.skill_dir / "references" / "laws" / f"trademark_law_{self.law_version}.md"

        def _stamp(p: Path) -> Dict:
            if not p.exists():
                return {"path": str(p.relative_to(self.skill_dir)), "status": "missing"}
            return {
                "path": str(p.relative_to(self.skill_dir)),
                "bytes": p.stat().st_size,
                # 用内容摘要而非文件 mtime：clone 后 mtime 不可信
                "sha256_8": __import__("hashlib").sha256(p.read_bytes()).hexdigest()[:8],
            }

        return {
            "rules_version": self.risk_rules.get("version"),
            "rules_updated": self.risk_rules.get("last_updated"),
            "article_map_as_of": self.article_map.get("as_of"),
            "risk_rules": _stamp(rules_path),
            "geographic_names": _stamp(geo_path),
            "law_text": _stamp(law_path),
        }

    @staticmethod
    def _coverage_report(prohibited: Dict, distinctive: Dict, similarity: Dict) -> Dict:
        """
        明写"查了什么、没查什么"。这是法律类工具最该暴露的一栏：
        读者据此知道结论的效力范围，而不是默认"没报错就是全查过了"。
        """
        sim_status = similarity.get("status")
        similarity_label = {
            "ok": "已检索",
            "skipped": "已跳过（用户指定）",
            "not_configured": "未执行（未配置数据源）",
            "error": "失败（结论不含冲突判断）",
        }.get(sim_status, "未执行")

        checked = [
            "禁用标志（国家名称/国家象征/欺骗性/政治敏感/民族宗教）",
            "显著性（描述性词汇、尼斯分类 1-45 类通用名称）",
            "县级以上行政区划地名（省级/地级/县级）",
        ]
        not_checked = [
            "在先商标近似检索：" + similarity_label,
            "图形、声音、三维、动态商标",
            "跨类别近似与类似商品/服务判定",
            "使用证据与在先使用抗辩",
        ]
        if not distinctive.get("ai_analysis") and not prohibited.get("ai_checked"):
            not_checked.append("语义歧义判断（AI 分析未启用）")

        return {"checked": checked, "not_checked": not_checked,
                "similarity_status": sim_status}

    @staticmethod
    def _manual_review_advice(prohibited: Dict) -> str:
        """按命中的检查项生成"需人工确认"的具体建议，不写死成地名。"""
        keys = {v.get("check_key") for v in prohibited.get("violations", [])
                if str(v.get("consequence", "")).startswith("需确认")}
        advice = []
        if "geographic_name" in keys:
            advice.append("含县级以上地名：须确认其是否具有其他含义；无其他含义则不得注册。")
        if "national_name" in keys:
            advice.append("含国家名称：须判断整体是否构成近似；"
                          "如属指南第三章列举的例外（客观事物、报刊名称、"
                          "经批准的企事业单位简称且长期使用形成唯一对应关系），可主张不适用禁用条款。")
        if "public_order" in keys:
            advice.append("含政治敏感词：须判断是否损害国家尊严或造成公众误认。")
        if "ethnic_discrimination" in keys:
            advice.append("含民族/宗教元素：须判断是否构成民族歧视或产生不良影响。")
        if not advice:
            advice.append("存在需人工判断的风险点，建议由专业人士复核。")
        return "".join(advice)

    @staticmethod
    def _today() -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")


def main():
    parser = argparse.ArgumentParser(
        description="商标合规审查工具（基于现行商标法，逐条给出依据）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/review.py "云图智能" --class 9,42
  python scripts/review.py "北京烤鸭" --class 30
  python scripts/review.py --batch trademarks.txt --class 9,35,42
  python scripts/review.py "云图智能" --report --format docx
        """)

    parser.add_argument("trademarks", nargs="*", help="商标名称（可多个）")
    parser.add_argument("--class", "--classes", dest="classes",
                        help="商标类别，逗号分隔，如 9,35,42")
    parser.add_argument("--batch", help="从文件批量读取（每行一个）")
    parser.add_argument("--report", action="store_true", help="生成报告")
    parser.add_argument("--format", choices=["docx", "pdf", "json"], default="docx")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--skip-similarity", action="store_true", help="跳过在先商标检索")
    parser.add_argument("--law-version", choices=["2019", "2026"],
                        help="审查依据版本（默认取 config.yaml，未配置则 2019）")

    args = parser.parse_args()

    trademarks = []
    if args.batch:
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                trademarks = [line.strip() for line in f if line.strip()]
        except OSError as e:
            parser.error(f"无法读取批量文件 {args.batch}: {e}")
    elif args.trademarks:
        trademarks = [t.strip() for t in args.trademarks]
    else:
        parser.print_help()
        return

    # 输入校验：空名/空白名不得给出任何结论（空名会穿透所有规则）
    empty = [i for i, t in enumerate(trademarks) if not t]
    if empty or not trademarks:
        parser.error("商标名称不能为空或仅含空白字符")

    classes = None
    if args.classes:
        try:
            classes = [int(c.strip()) for c in args.classes.split(",")]
        except ValueError:
            parser.error(f"类别必须是 1-45 的整数，收到: {args.classes}")
        bad = [c for c in classes if not 1 <= c <= 45]
        if bad:
            parser.error(f"尼斯类别范围为 1-45，越界: {bad}")

    reviewer = TrademarkReviewer(config_path=args.config)

    if args.law_version:
        reviewer.law_version = args.law_version
    if args.skip_similarity:
        reviewer.config.setdefault("trademark_review", {}) \
            .setdefault("review", {})["skip_similarity_check"] = True

    results = [reviewer.review(name, classes) for name in trademarks]

    if args.report:
        print("\n📄 正在生成报告...")
        from report_generator import generate_report
        output_path = args.output
        if not output_path:
            output_path = f"商标审查报告_{results[0]['review_date'].replace('-', '')}.{args.format}"
        generate_report(results, output_path, format=args.format)
        print(f"✅ 报告已生成: {output_path}")
    elif args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"✅ 结果已保存: {args.output}")


if __name__ == "__main__":
    main()
