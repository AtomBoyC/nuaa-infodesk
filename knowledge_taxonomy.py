from __future__ import annotations

from collections.abc import Iterable


CATEGORY_ALIASES = {
    "办事大厅": "服务大厅",
    "服务大厅": "服务大厅",
    "服务指南": "服务大厅",
    "校园服务": "服务大厅",
    "教学支持": "服务大厅",
    "常见问题": "服务大厅",
    "业务系统": "信息系统",
    "信息系统": "信息系统",
    "信息系统服务": "信息系统",
    "数据与平台": "信息系统",
    "网站与数据": "信息系统",
    "工作通知": "通知与制度",
    "公告公示": "通知与制度",
    "制度规范": "通知与制度",
    "新闻动态": "新闻与党建",
    "党建工作": "新闻与党建",
    "官网信息": "部门信息",
}

CATEGORY_ORDER = (
    "网络服务",
    "账号与安全",
    "服务大厅",
    "信息系统",
    "协同办公",
    "软件服务",
    "通知与制度",
    "新闻与党建",
    "部门信息",
)


def canonical_category(category: str) -> str:
    return CATEGORY_ALIASES.get(category.strip(), category.strip() or "其他服务")


def ordered_categories(categories: Iterable[str]) -> list[str]:
    available = {canonical_category(category) for category in categories}
    standard = [category for category in CATEGORY_ORDER if category in available]
    custom = sorted(available.difference(CATEGORY_ORDER))
    return ["全部", *standard, *custom]
