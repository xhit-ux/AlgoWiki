from __future__ import annotations

import hashlib
import re
from pathlib import Path


LEGACY_CATEGORY_SLUGS = [
    "language-basics",
    "data-structures",
    "graph",
    "dynamic-programming",
    "math",
    "string",
    "contest-zone",
    "icpc",
    "ccpc",
    "experience",
]


CATEGORY_DEFS = [
    ("0. 阅前须知", "xcpc-preface", None, 10, "public"),
    ("1. 学术诚信", "xcpc-academic-integrity", None, 20, "public"),
    ("2. 常见术语", "xcpc-common-terms", None, 30, "public"),
    ("3. 竞赛概念", "xcpc-concepts", None, 40, "public"),
    ("4. 比赛介绍", "xcpc-contests", None, 50, "school"),
    ("5. 关键网站", "xcpc-sites", None, 60, "public"),
    ("6. 代码工具", "xcpc-tools", None, 70, "public"),
    ("7. 阶段任务", "xcpc-stages", None, 80, "public"),
    ("8. 关于训练", "xcpc-training", None, 90, "public"),
    ("9. 结语与致谢", "xcpc-closing", None, 100, "public"),
]


SNAPSHOT_PATH = Path(__file__).resolve().parents[2] / "data" / "xcpc_readme_snapshot.md"

SECTION_CATEGORY_MAP = {
    "阅前须知": "xcpc-preface",
    "文章大纲": "xcpc-preface",
    "阅读索引": "xcpc-preface",
    "学术诚信": "xcpc-academic-integrity",
    "常见术语": "xcpc-common-terms",
    "竞赛概念": "xcpc-concepts",
    "比赛介绍": "xcpc-contests",
    "关键网站": "xcpc-sites",
    "代码工具": "xcpc-tools",
    "阶段任务": "xcpc-stages",
    "关于训练": "xcpc-training",
    "结语与致谢": "xcpc-closing",
}

HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$", re.MULTILINE)
TOC_RE = re.compile(r"^\[TOC\]\s*$", re.MULTILINE)


def _read_snapshot() -> str:
    if not SNAPSHOT_PATH.exists():
        raise RuntimeError(f"XCPC snapshot file not found: {SNAPSHOT_PATH}")
    return SNAPSHOT_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")


def _normalize_markdown(text: str) -> str:
    normalized = TOC_RE.sub("", text)
    normalized = re.sub(r"\((?:\./)?assets/", "(/wiki-assets/", normalized)
    normalized = re.sub(r'(?<=src=["\'])(?:\./)?assets/', "/wiki-assets/", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _body_lines(markdown: str) -> list[str]:
    lines = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "[TOC]":
            continue
        lines.append(stripped)
    return lines


def _has_meaningful_body(markdown: str) -> bool:
    return bool(_body_lines(markdown))


def _extract_summary(markdown: str) -> str:
    for line in _body_lines(markdown):
        if line.startswith("![") or line.startswith("|") or line.startswith("- ") or line.startswith("* "):
            continue
        return line[:110]
    return ""


def _slug_for(category_slug: str, title: str) -> str:
    digest = hashlib.sha1(f"{category_slug}\n{title}".encode("utf-8")).hexdigest()[:12]
    return f"{category_slug}-{digest}"


def _parse_articles() -> list[dict]:
    text = _read_snapshot()
    headings = [
        {
            "level": len(match.group(1)),
            "title": match.group(2).strip(),
            "start": match.start(),
        }
        for match in HEADING_RE.finditer(text)
    ]

    h2_sections = [
        item for item in headings if item["level"] == 2 and item["title"] in SECTION_CATEGORY_MAP
    ]

    articles: list[dict] = []
    for index, h2 in enumerate(h2_sections):
        block_end = h2_sections[index + 1]["start"] if index + 1 < len(h2_sections) else len(text)
        h3_sections = [
            item
            for item in headings
            if item["level"] == 3 and h2["start"] < item["start"] < block_end
        ]

        overview_end = h3_sections[0]["start"] if h3_sections else block_end
        overview_markdown = _normalize_markdown(text[h2["start"] : overview_end])
        category_slug = SECTION_CATEGORY_MAP[h2["title"]]
        if _has_meaningful_body(overview_markdown):
            articles.append(
                {
                    "slug": _slug_for(category_slug, h2["title"]),
                    "title": h2["title"],
                    "category": category_slug,
                    "summary": _extract_summary(overview_markdown),
                    "featured": category_slug == "xcpc-preface",
                    "content_md": overview_markdown,
                }
            )

        for child_index, h3 in enumerate(h3_sections):
            section_end = h3_sections[child_index + 1]["start"] if child_index + 1 < len(h3_sections) else block_end
            section_markdown = _normalize_markdown(text[h3["start"] : section_end])
            article_title = f"{h2['title']}｜{h3['title']}"
            articles.append(
                {
                    "slug": _slug_for(category_slug, article_title),
                    "title": article_title,
                    "category": category_slug,
                    "summary": _extract_summary(section_markdown),
                    "featured": False,
                    "content_md": section_markdown,
                }
            )

    return articles


ARTICLE_DEFS = _parse_articles()
