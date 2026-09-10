from __future__ import annotations

"""Import public pages from the NUAA Information Office website into SQLite.

The importer stores page titles, categorized key excerpts, and original URLs. It
does not crawl authentication pages or copy downloadable attachments.
"""

import argparse
from collections import deque
from dataclasses import dataclass
from datetime import date
from hashlib import sha1
from html.parser import HTMLParser
import re
import sys
import time
from typing import Iterable
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from database import DEFAULT_DB_PATH, bootstrap_database, replace_imported_site_items
from info_service_assistant import KnowledgeItem


DEFAULT_BASE_URL = "https://xxhc.nuaa.edu.cn/"
USER_AGENT = "NUAA-Info-Service-KB-Importer/1.0 (local competition project)"
SKIPPED_SUFFIXES = {
    ".7z", ".avi", ".doc", ".docx", ".gif", ".gz", ".jpeg", ".jpg",
    ".mov", ".mp3", ".mp4", ".pdf", ".png", ".ppt", ".pptx", ".rar",
    ".tar", ".wav", ".xls", ".xlsx", ".zip",
}
SKIPPED_PATH_PARTS = {"_upload", "admin", "login", "manage", "search", "system"}


@dataclass(frozen=True)
class Page:
    url: str
    title: str
    text: str
    links: tuple[str, ...]
    article_text: str = ""
    description: str = ""


class PageParser(HTMLParser):
    """Extract visible page text and internal links without external packages."""

    BLOCK_TAGS = {"article", "br", "div", "h1", "h2", "h3", "h4", "li", "p", "section", "tr"}
    HIDDEN_TAGS = {"footer", "header", "iframe", "nav", "noscript", "script", "style", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._hidden_depth = 0
        self._in_title = False
        self._title_parts: list[str] = []
        self._text_parts: list[str] = []
        self._article_parts: list[str] = []
        self._article_tags: list[str] = []
        self.description = ""
        self.links: list[str] = []

    @property
    def title(self) -> str:
        return compact_text(" ".join(self._title_parts))

    @property
    def text(self) -> str:
        return unique_text_lines(self._text_parts)

    @property
    def article_text(self) -> str:
        return unique_text_lines(self._article_parts)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "meta" and attributes.get("name", "").lower() == "description":
            self.description = compact_text(attributes.get("content") or "")
        class_names = (attributes.get("class") or "").split()
        if "wp_articlecontent" in class_names:
            self._article_tags.append(tag)
        if tag in self.HIDDEN_TAGS:
            self._hidden_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "a":
            href = attributes.get("href")
            if href:
                self.links.append(href)
        if not self._hidden_depth and tag in self.BLOCK_TAGS:
            self._text_parts.append("\n")
            if self._article_tags:
                self._article_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag in self.HIDDEN_TAGS and self._hidden_depth:
            self._hidden_depth -= 1
        if self._article_tags and self._article_tags[-1] == tag:
            self._article_tags.pop()
        if not self._hidden_depth and tag in self.BLOCK_TAGS:
            self._text_parts.append("\n")
            if self._article_tags:
                self._article_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)
        if not self._hidden_depth:
            self._text_parts.append(data)
            if self._article_tags:
                self._article_parts.append(data)


def compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def unique_text_lines(parts: list[str]) -> str:
    lines = (compact_text(part) for part in "".join(parts).split("\n"))
    unique_lines: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if line and line not in seen:
            seen.add(line)
            unique_lines.append(line)
    return "\n".join(unique_lines)


def normalized_url(base_url: str, href: str) -> str | None:
    candidate = urlsplit(urljoin(base_url, href))
    base = urlsplit(base_url)
    if candidate.scheme not in {"http", "https"} or candidate.netloc != base.netloc:
        return None
    path = candidate.path or "/"
    # The campus CMS exposes the same article under template-prefixed aliases.
    path = re.sub(r"^/_(?:s|t)\d+", "", path)
    suffix = path.lower().rsplit(".", 1)
    if len(suffix) == 2 and f".{suffix[-1]}" in SKIPPED_SUFFIXES:
        return None
    if any(part.lower() in SKIPPED_PATH_PARTS for part in path.split("/") if part):
        return None
    return urlunsplit((candidate.scheme, candidate.netloc, path, "", ""))


def decode_html(content: bytes, charset: str | None) -> str:
    encodings = [charset, "utf-8", "gb18030"]
    for encoding in encodings:
        if not encoding:
            continue
        try:
            return content.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return content.decode("utf-8", errors="replace")


def fetch_page(url: str) -> Page:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=20) as response:
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError(f"not HTML ({content_type})")
        html = decode_html(response.read(), response.headers.get_content_charset())
    parser = PageParser()
    parser.feed(html)
    parser.close()
    return Page(
        url=url,
        title=parser.title,
        text=parser.text,
        links=tuple(parser.links),
        article_text=parser.article_text,
        description=parser.description,
    )


def classify_page(title: str, url: str, text: str) -> str:
    title_haystack = f"{title} {url}".lower()
    title_rules = (
        ("部门信息", ("部门概况", "部门职责", "内设机构", "联络员", "部门文化", "职权")),
        ("党建工作", ("党支部", "党建", "党员", "党日", "廉洁教育")),
        ("制度规范", ("法律", "法规", "条例", "管理办法", "制度", "规范", "标准")),
        ("公告公示", ("公告", "公示")),
        ("工作通知", ("通知", "招聘", "申报", "竞赛")),
        ("新闻动态", ("我校", "召开", "调研", "入选", "举办", "来校", "活动")),
        ("网络服务", ("校园网", "vpn", "webvpn", "eduroam", "5g", "ip地址", "域名", "云桌面")),
        ("账号与安全", ("统一身份认证", "密码", "保密", "安全教育", "安全防护")),
        ("软件服务", ("软件", "wps", "mathtype", "正版")),
        ("协同办公", ("电子邮件", "邮箱", "云盘", "统一消息")),
        ("数据与平台", ("数据治理", "高性能计算", "云服务器", "网站群", "流程制作", "数据接口")),
        ("服务指南", ("校园卡", "故障报修", "视频会议", "高清录播", "智慧教室", "标准化考场")),
        ("常见问题", ("常见问题", "如何")),
    )
    for category, keywords in title_rules:
        if any(keyword in title_haystack for keyword in keywords):
            return category

    haystack = f"{title_haystack} {text[:1000].lower()}"
    content_rules = (
        ("网络服务", ("校园网", "vpn", "webvpn", "eduroam", "ip地址", "网络服务", "云桌面")),
        ("账号与安全", ("网络安全", "安全", "保密", "漏洞", "身份认证", "密码")),
        ("软件服务", ("软件", "wps", "mathtype", "正版")),
        ("协同办公", ("电子邮件", "邮箱", "云盘", "统一消息")),
        ("数据与平台", ("数据治理", "数据质量", "高性能计算", "云服务器", "网站群", "域名")),
        ("服务指南", ("服务指南", "办事流程", "校园卡", "电子邮件", "报修", "视频会议", "智慧教室")),
        ("制度规范", ("制度", "规范", "办法", "条例", "标准")),
        ("工作通知", ("通知", "招聘", "申报", "竞赛")),
        ("公告公示", ("公告", "公示")),
        ("新闻动态", ("新闻", "动态", "召开", "入选", "调研", "活动")),
        ("部门信息", ("部门概况", "部门职责", "机构", "联络员", "文化", "职权")),
        ("常见问题", ("常见问题", "faq", "如何")),
    )
    for category, keywords in content_rules:
        if any(keyword in haystack for keyword in keywords):
            return category
    return "官网信息"


def useful_lines(text: str) -> list[str]:
    ignored = {"首页", "部门概况", "新闻动态", "工作通知", "公告公示", "服务指南", "常见问题"}
    lines: list[str] = []
    for line in text.splitlines():
        value = compact_text(line)
        if len(value) < 10 or value in ignored:
            continue
        lines.append(value)
    return lines


def page_to_knowledge_item(page: Page) -> KnowledgeItem | None:
    title = page.title.replace("_", " ").strip()
    title = re.sub(r"\s*[-|_]\s*信息化处.*$", "", title).strip()
    content = page.article_text or page.description
    if not content:
        return None
    lines = useful_lines(content)
    if not title or len(lines) < 2:
        return None
    excerpt = compact_text(" ".join(lines))[:700]
    if len(excerpt) < 30:
        return None
    category = classify_page(title, page.url, excerpt)
    return KnowledgeItem(
        id=f"xxhc-{sha1(page.url.encode('utf-8')).hexdigest()[:16]}",
        title=title[:120],
        category=category,
        audience="全校师生",
        summary=excerpt[:150],
        answer=f"{excerpt}\n\n完整内容请查看信息化处官网原文：{page.url}",
        steps=("打开官网原文查看完整说明、办理条件和最新通知。",),
        source="南京航空航天大学信息化处官网公开页面",
        owner="信息化处",
        updated=date.today().isoformat(),
        tags=(category, title[:40], "信息化处官网"),
        link=page.url,
    )


def deduplicate_items(items: Iterable[KnowledgeItem]) -> list[KnowledgeItem]:
    """Prefer the most complete page when the crawler finds a repeated title."""
    grouped: dict[tuple[str, str], list[KnowledgeItem]] = {}
    for item in items:
        key = (item.source, compact_text(item.title).lower())
        grouped.setdefault(key, []).append(item)

    unique_items: list[KnowledgeItem] = []
    for candidates in grouped.values():
        unique_items.append(
            max(
                candidates,
                key=lambda item: (len(item.answer), item.link),
            )
        )
    return unique_items


def crawl_public_pages(base_url: str, max_pages: int, delay: float) -> Iterable[Page]:
    start = normalized_url(base_url, base_url)
    if start is None:
        raise ValueError("base URL must be a public http(s) URL")
    frontier: deque[str] = deque([start])
    visited: set[str] = set()
    while frontier and len(visited) < max_pages:
        url = frontier.popleft()
        if url in visited:
            continue
        visited.add(url)
        try:
            page = fetch_page(url)
        except Exception as error:  # Network failures should not stop the whole import.
            print(f"skip {url}: {error}", file=sys.stderr)
            continue
        yield page
        for href in page.links:
            child = normalized_url(base_url, href)
            if child and child not in visited:
                frontier.append(child)
        if delay:
            time.sleep(delay)


def import_site(
    base_url: str,
    db_path: str,
    max_pages: int,
    delay: float,
    dry_run: bool,
    minimum_items: int,
) -> tuple[int, int]:
    connection = bootstrap_database(db_path)
    visited_count = 0
    items: list[KnowledgeItem] = []
    try:
        for page in crawl_public_pages(base_url, max_pages, delay):
            visited_count += 1
            item = page_to_knowledge_item(page)
            if item is None:
                continue
            items.append(item)
        items = deduplicate_items(items)
        if not dry_run and len(items) < minimum_items:
            raise RuntimeError(
                f"only {len(items)} valid content pages were found; "
                f"refusing to replace the existing import (minimum: {minimum_items})"
            )
        if not dry_run:
            replace_imported_site_items(connection, items)
        for index, item in enumerate(items, start=1):
            print(f"[{index}] {item.category} | {item.title}")
    finally:
        connection.close()
    return visited_count, len(items)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import public NUAA Information Office pages into SQLite.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--max-pages", type=int, default=300)
    parser.add_argument("--delay", type=float, default=0.25, help="seconds between requests")
    parser.add_argument(
        "--minimum-items",
        type=int,
        default=50,
        help="minimum valid pages required before replacing an earlier import",
    )
    parser.add_argument("--dry-run", action="store_true", help="crawl and print without changing SQLite")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    visited, imported = import_site(
        args.base_url,
        args.db,
        max(args.max_pages, 1),
        max(args.delay, 0),
        args.dry_run,
        max(args.minimum_items, 1),
    )
    action = "would import" if args.dry_run else "imported"
    print(f"Finished: fetched {visited} HTML pages and {action} {imported} knowledge items.")


if __name__ == "__main__":
    main()
