from django.db import migrations


FIXED_TRICK_TERMS = (
    {"name": "数学", "slug": "math"},
    {"name": "动态规划", "slug": "dynamic-programming"},
    {"name": "字符串", "slug": "string"},
    {"name": "计算几何", "slug": "computational-geometry"},
    {"name": "数据结构", "slug": "data-structure"},
    {"name": "图论", "slug": "graph-theory"},
    {"name": "其他", "slug": "other"},
)

EXACT_TERM_CATEGORY_MAP = {
    "二分答案": ("其他",),
    "双指针": ("其他",),
    "滑动窗口": ("其他",),
    "前缀和": ("数据结构",),
    "差分": ("数据结构",),
    "离散化": ("数据结构",),
    "贪心": ("其他",),
    "排序技巧": ("其他",),
    "位运算": ("数学",),
    "lowbit": ("数据结构",),
    "快速幂": ("数学",),
    "矩阵快速幂": ("数学",),
    "欧拉函数": ("数学",),
    "扩展欧几里得": ("数学",),
    "中国剩余定理": ("数学",),
    "筛法": ("数学",),
    "质因数分解": ("数学",),
    "组合数学": ("数学",),
    "容斥原理": ("数学",),
    "博弈论": ("数学",),
    "DFS": ("图论",),
    "BFS": ("图论",),
    "最短路": ("图论",),
    "并查集": ("图论", "数据结构"),
    "最小生成树": ("图论",),
    "树形DP": ("动态规划", "图论"),
    "换根DP": ("动态规划", "图论"),
    "LCA": ("图论",),
    "树状数组": ("数据结构",),
    "线段树": ("数据结构",),
    "可持久化数据结构": ("数据结构",),
    "单调栈": ("数据结构",),
    "单调队列": ("数据结构",),
    "字符串哈希": ("字符串",),
    "KMP": ("字符串",),
    "AC自动机": ("字符串",),
    "后缀数组": ("字符串",),
    "网络流": ("图论",),
    "最小割": ("图论",),
    "费用流": ("图论",),
    "状态压缩DP": ("动态规划",),
    "区间DP": ("动态规划",),
    "数位DP": ("动态规划", "数学"),
    "概率DP": ("动态规划", "数学"),
    "构造": ("其他",),
    "交互题": ("其他",),
    "模拟": ("其他",),
    "高精度处理": ("数学",),
    "卡常": ("其他",),
    "代码模板": ("其他",),
    "数学": ("数学",),
    "动态规划": ("动态规划",),
    "字符串": ("字符串",),
    "计算几何": ("计算几何",),
    "数据结构": ("数据结构",),
    "图论": ("图论",),
    "其他": ("其他",),
}

KEYWORD_CATEGORY_MAP = {
    "数学": (
        "数学",
        "数论",
        "组合",
        "概率",
        "同余",
        "素数",
        "质数",
        "因数",
        "因子",
        "gcd",
        "lcm",
        "欧拉",
        "莫比乌斯",
        "逆元",
        "crt",
        "exgcd",
        "快速幂",
        "高精度",
    ),
    "动态规划": (
        "动态规划",
        "dp",
        "树形dp",
        "换根dp",
        "状压",
        "数位dp",
        "区间dp",
        "概率dp",
        "背包",
    ),
    "字符串": (
        "字符串",
        "string",
        "kmp",
        "ac自动机",
        "后缀",
        "hash",
        "trie",
        "字典树",
        "回文",
    ),
    "计算几何": (
        "计算几何",
        "几何",
        "geometry",
        "凸包",
        "叉积",
        "点积",
        "直线",
        "圆",
        "多边形",
        "扫描线",
    ),
    "数据结构": (
        "数据结构",
        "树状数组",
        "线段树",
        "主席树",
        "单调栈",
        "单调队列",
        "平衡树",
        "堆",
        "优先队列",
        "前缀和",
        "差分",
        "离散化",
        "rmq",
        "st表",
        "lowbit",
    ),
    "图论": (
        "图论",
        "dfs",
        "bfs",
        "最短路",
        "二分图",
        "拓扑",
        "强连通",
        "tarjan",
        "lca",
        "最小生成树",
        "网络流",
        "最小割",
        "费用流",
        "树上",
    ),
}


def normalize_text(value):
    return " ".join(str(value or "").strip().lower().split())


def categorize_trick_entry(term_names, title, content):
    assigned = []
    seen = set()

    def add_category(name):
        if not name or name in seen:
            return
        seen.add(name)
        assigned.append(name)

    for raw_name in term_names:
        display_name = " ".join(str(raw_name or "").strip().split())
        for category in EXACT_TERM_CATEGORY_MAP.get(display_name, ()):
            add_category(category)

    blob = "\n".join(
        [
            normalize_text(title),
            normalize_text(content),
            " ".join(normalize_text(name) for name in term_names if name),
        ]
    )
    for category_name in [item["name"] for item in FIXED_TRICK_TERMS]:
        for keyword in KEYWORD_CATEGORY_MAP.get(category_name, ()):
            if keyword in blob:
                add_category(category_name)
                break

    if not assigned:
        add_category("其他")

    return assigned


def migrate_trick_terms(apps, schema_editor):
    TrickEntry = apps.get_model("wiki", "TrickEntry")
    TrickTerm = apps.get_model("wiki", "TrickTerm")
    TrickTermSuggestion = apps.get_model("wiki", "TrickTermSuggestion")

    fixed_terms = {}
    for item in FIXED_TRICK_TERMS:
        term, _ = TrickTerm.objects.get_or_create(
            name=item["name"],
            defaults={
                "slug": item["slug"],
                "description": "",
                "is_active": True,
                "is_builtin": True,
            },
        )
        changed = False
        if term.slug != item["slug"]:
            term.slug = item["slug"]
            changed = True
        if not term.is_active:
            term.is_active = True
            changed = True
        if not term.is_builtin:
            term.is_builtin = True
            changed = True
        if changed:
            term.save(update_fields=["slug", "is_active", "is_builtin", "updated_at"])
        fixed_terms[item["name"]] = term

    fixed_term_ids = [term.id for term in fixed_terms.values()]

    for entry in TrickEntry.objects.all().iterator():
        existing_term_names = list(entry.terms.all().values_list("name", flat=True))
        next_category_names = categorize_trick_entry(
            existing_term_names,
            getattr(entry, "title", ""),
            getattr(entry, "content_md", ""),
        )
        entry.terms.set([fixed_terms[name] for name in next_category_names])
        if hasattr(entry, "pending_term_suggestions"):
            entry.pending_term_suggestions.clear()

    TrickTermSuggestion.objects.all().delete()
    TrickTerm.objects.exclude(id__in=fixed_term_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0033_answer_review_note_answer_reviewed_at_and_more"),
    ]

    operations = [
        migrations.RunPython(
            migrate_trick_terms,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
