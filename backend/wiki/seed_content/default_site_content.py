from __future__ import annotations

from django.utils import timezone


DEFAULT_TEAM_MEMBER = {
    "display_id": "Null_Resot",
    "avatar_url": "/wiki-assets/resot.png",
    "profile_url": "https://github.com/NullResot",
    "sort_order": 0,
}


FRIENDLY_LINK_DEFS = [
    {
        "name": "AlgoWiki 项目仓库",
        "description": "AlgoWiki 主仓库，包含后端、前端、部署脚本与默认内容包。",
        "url": "https://github.com/NullResot/AlgoWiki",
        "order": 10,
    },
    {
        "name": "【打破信息差】XCPC 入门仓库",
        "description": "AlgoWiki 中【打破信息差】专题的原始内容来源仓库。",
        "url": "https://github.com/NullResot/xcpc",
        "order": 20,
    },
    {
        "name": "Codeforces",
        "description": "国际主流算法竞赛平台，适合日常训练、打比赛和赛后补题。",
        "url": "https://codeforces.com/",
        "order": 30,
    },
    {
        "name": "AtCoder",
        "description": "日本算法竞赛平台，题面质量高，适合系统提升算法基本功。",
        "url": "https://atcoder.jp/",
        "order": 40,
    },
    {
        "name": "牛客竞赛",
        "description": "国内常用竞赛平台，多校赛、训练赛和校赛资源较多。",
        "url": "https://ac.nowcoder.com/",
        "order": 50,
    },
    {
        "name": "洛谷",
        "description": "题库、题单、专栏和社区资源较完整，适合作为基础训练入口。",
        "url": "https://www.luogu.com.cn/",
        "order": 60,
    },
    {
        "name": "QOJ",
        "description": "常见于训练营、区域赛或邀请赛相关题目与榜单承载。",
        "url": "https://qoj.ac/",
        "order": 70,
    },
    {
        "name": "VJudge",
        "description": "适合组队训练、虚拟参赛与跨平台组题。",
        "url": "https://vjudge.net/",
        "order": 80,
    },
]


DEFAULT_TRICK_DEFS = [
    {
        "title": "对拍脚本与最小反例",
        "content_md": (
            "# 对拍脚本与最小反例\n\n"
            "当你怀疑自己的程序在边界数据上会出错时，优先做对拍，而不是直接盲改。\n\n"
            "## 建议流程\n"
            "1. 先写一个朴素但可信的暴力程序。\n"
            "2. 再写一个随机数据生成器。\n"
            "3. 比较暴力程序和正式程序的输出。\n"
            "4. 一旦不一致，立刻缩小数据规模并记录最小反例。\n\n"
            "## 经验\n"
            "- 对拍最有价值的产出不是“发现 bug”，而是“得到一个可复现的最小数据”。\n"
            "- 赛后请把最小反例写进题解或复盘，方便以后复训。"
        ),
    },
    {
        "title": "补题记录不要只写 AC",
        "content_md": (
            "# 补题记录不要只写 AC\n\n"
            "只记录“这题我过了”没有长期价值。更有用的是记录：\n\n"
            "- 第一次失败卡在什么地方；\n"
            "- 正解的关键转化是什么；\n"
            "- 这道题和哪一类经典模型相似；\n"
            "- 下次再见到类似题目，应该先检查什么。\n\n"
            "把补题记录写成简短模板，长期收益会明显高于只刷题不复盘。"
        ),
    },
]


def build_default_competition_content() -> tuple[list[dict], list[dict]]:
    year = timezone.localdate().year

    notices = [
        {
            "title": f"{year} ICPC 赛季维护说明（默认内容）",
            "content_md": (
                f"# {year} ICPC 赛季维护说明（默认内容）\n\n"
                "这是一条默认初始化内容，用于避免赛事公告页为空。\n\n"
                "请管理员在部署后按当年真实赛历补充：\n"
                "- 官方赛站安排\n"
                "- 报名入口与截止时间\n"
                "- 校内选拔与组队流程\n"
                "- 赛后复盘与资料归档位置\n"
            ),
            "series": "icpc",
            "year": year,
            "stage": "regional",
        },
        {
            "title": f"{year} CCPC 赛季维护说明（默认内容）",
            "content_md": (
                f"# {year} CCPC 赛季维护说明（默认内容）\n\n"
                "这是一条默认初始化内容，用于避免赛事公告页为空。\n\n"
                "请管理员在部署后按当年真实赛历补充报名、赛站和校内选拔信息。"
            ),
            "series": "ccpc",
            "year": year,
            "stage": "regional",
        },
        {
            "title": "蓝桥杯参赛入口与维护说明（默认内容）",
            "content_md": (
                "# 蓝桥杯参赛入口与维护说明（默认内容）\n\n"
                "该条目为默认初始化内容。请管理员补充：\n\n"
                "- 当年报名入口\n"
                "- 省赛/国赛时间\n"
                "- 校内通知与组织方式\n"
            ),
            "series": "lanqiao",
            "year": None,
            "stage": "general",
        },
        {
            "title": "天梯赛参赛入口与维护说明（默认内容）",
            "content_md": (
                "# 天梯赛参赛入口与维护说明（默认内容）\n\n"
                "该条目为默认初始化内容。请管理员补充：\n\n"
                "- 报名链接\n"
                "- 比赛时间\n"
                "- 校内集训与参赛安排\n"
            ),
            "series": "tianti",
            "year": None,
            "stage": "general",
        },
    ]

    schedules = [
        {
            "event_date": f"{year}-03-01",
            "competition_time_range": "待更新",
            "competition_type": "蓝桥杯赛历待维护（默认内容）",
            "location": "请按本赛季官方公告更新",
            "qq_group": "",
            "notice_title": "蓝桥杯参赛入口与维护说明（默认内容）",
        },
        {
            "event_date": f"{year}-04-01",
            "competition_time_range": "待更新",
            "competition_type": "天梯赛赛历待维护（默认内容）",
            "location": "请按本赛季官方公告更新",
            "qq_group": "",
            "notice_title": "天梯赛参赛入口与维护说明（默认内容）",
        },
        {
            "event_date": f"{year}-09-01",
            "competition_time_range": "待更新",
            "competition_type": f"{year} ICPC 赛历待维护（默认内容）",
            "location": "请按本赛季官方公告更新",
            "qq_group": "",
            "notice_title": f"{year} ICPC 赛季维护说明（默认内容）",
        },
        {
            "event_date": f"{year}-10-01",
            "competition_time_range": "待更新",
            "competition_type": f"{year} CCPC 赛历待维护（默认内容）",
            "location": "请按本赛季官方公告更新",
            "qq_group": "",
            "notice_title": f"{year} CCPC 赛季维护说明（默认内容）",
        },
    ]

    return notices, schedules
