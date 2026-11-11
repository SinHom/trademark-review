"""
商标查询接口适配器

提供标准化的商标查询接口规范，由使用方根据实际可用的API实现具体逻辑。
"""

from typing import List, Dict, Optional
from abc import ABC, abstractmethod


class TrademarkAPIAdapter(ABC):
    """商标查询接口适配器基类"""

    @abstractmethod
    def search_similar(self, trademark_name: str, classes: List[int]) -> List[Dict]:
        """
        查询近似商标

        Args:
            trademark_name: 商标名称
            classes: 商标类别列表（1-45）

        Returns:
            商标列表，每个商标包含以下字段：
            [
                {
                    "name": str,                    # 商标名称
                    "registration_number": str,      # 注册号
                    "status": str,                   # 注册状态：已注册/申请中/已驳回/已撤销等
                    "classes": List[int],            # 商标类别
                    "applicant": str,                # 申请人
                    "application_date": str,         # 申请日期 YYYY-MM-DD
                    "registration_date": str,        # 注册日期（可选）
                    "similarity_score": float,       # 相似度 0-1（可选）
                },
                ...
            ]
        """
        raise NotImplementedError("需要实现具体的商标查询接口")

    def get_trademark_detail(self, registration_number: str) -> Optional[Dict]:
        """
        获取商标详细信息（可选实现）

        Args:
            registration_number: 商标注册号

        Returns:
            商标详细信息字典，包含：
            {
                "name": str,
                "registration_number": str,
                "status": str,
                "classes": List[int],
                "applicant": str,
                "application_date": str,
                "registration_date": str,
                "exclusive_period": str,         # 专用权期限
                "goods_services": List[str],     # 具体商品/服务项目
                "agent": str,                    # 代理机构（可选）
                "announcement_issue": str,       # 公告期号（可选）
                "image_url": str,                # 商标图样URL（可选）
            }
        """
        raise NotImplementedError("可选实现")

    def check_exact_match(self, trademark_name: str, classes: List[int]) -> List[Dict]:
        """
        检查完全相同的商标（可选实现，默认调用search_similar）

        Args:
            trademark_name: 商标名称
            classes: 商标类别列表

        Returns:
            完全相同的商标列表
        """
        results = self.search_similar(trademark_name, classes)
        return [r for r in results if r.get("name") == trademark_name]


class MockTrademarkAPI(TrademarkAPIAdapter):
    """
    Mock实现，用于演示和测试
    当没有配置真实API时，返回模拟数据
    """

    def search_similar(self, trademark_name: str, classes: List[int]) -> List[Dict]:
        """返回模拟的近似商标数据"""
        return [
            {
                "name": f"{trademark_name}（示例）",
                "registration_number": "12345678",
                "status": "已注册",
                "classes": classes,
                "applicant": "某公司",
                "application_date": "2023-01-01",
                "registration_date": "2024-01-01",
                "similarity_score": 0.85,
            }
        ]

    def get_trademark_detail(self, registration_number: str) -> Optional[Dict]:
        """返回模拟的商标详情"""
        return {
            "name": "示例商标",
            "registration_number": registration_number,
            "status": "已注册",
            "classes": [9, 42],
            "applicant": "某公司",
            "application_date": "2023-01-01",
            "registration_date": "2024-01-01",
            "exclusive_period": "2024-01-01 至 2034-01-01",
            "goods_services": ["计算机软件", "云计算服务"],
        }


# 示例：实现一个具体的适配器
class ExampleCustomAPI(TrademarkAPIAdapter):
    """
    示例适配器实现
    展示如何对接第三方商标查询API
    """

    def __init__(self, api_key: str, base_url: str = "https://api.example.com"):
        """
        初始化适配器

        Args:
            api_key: API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = None  # 可以在这里初始化requests.Session

    def search_similar(self, trademark_name: str, classes: List[int]) -> List[Dict]:
        """
        示例实现：调用第三方API

        实际使用时需要根据API文档调整请求参数和响应解析
        """
        # import requests
        #
        # response = requests.post(
        #     f"{self.base_url}/trademark/search",
        #     json={
        #         "name": trademark_name,
        #         "classes": classes,
        #         "similarity_threshold": 0.6
        #     },
        #     headers={"Authorization": f"Bearer {self.api_key}"},
        #     timeout=30
        # )
        #
        # if response.status_code != 200:
        #     raise Exception(f"API请求失败: {response.status_code}")
        #
        # data = response.json()
        #
        # # 将API响应转换为标准格式
        # return [
        #     {
        #         "name": item["trademark_name"],
        #         "registration_number": item["reg_no"],
        #         "status": item["status"],
        #         "classes": item["nice_classes"],
        #         "applicant": item["applicant_name"],
        #         "application_date": item["apply_date"],
        #         "similarity_score": item.get("score", 0),
        #     }
        #     for item in data["results"]
        # ]

        # 暂时返回空列表
        return []


def load_adapter(config: Dict):
    """
    根据配置加载适配器。

    重要约定：
      - 未配置数据源时返回 None，由调用方标注"未检索"。
      - 绝不自动回退到 Mock 数据（虚构的近似商标会直接污染审查结论）。
      - 如需演示数据，必须显式配置
        adapter_class: "references.trademark_api_adapter.MockTrademarkAPI"

    Returns:
        TrademarkAPIAdapter 实例，或 None
    """
    adapter_class = config.get("api", {}).get("adapter_class")

    if not adapter_class:
        return None

    module_name, class_name = adapter_class.rsplit(".", 1)
    module = __import__(module_name, fromlist=[class_name])
    adapter_cls = getattr(module, class_name)

    import os
    api_key = os.getenv("TRADEMARK_API_KEY")
    return adapter_cls(api_key=api_key)
