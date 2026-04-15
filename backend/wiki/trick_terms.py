FIXED_TRICK_TERM_DEFINITIONS = (
    {"name": "数学", "slug": "math"},
    {"name": "动态规划", "slug": "dynamic-programming"},
    {"name": "字符串", "slug": "string"},
    {"name": "计算几何", "slug": "computational-geometry"},
    {"name": "数据结构", "slug": "data-structure"},
    {"name": "图论", "slug": "graph-theory"},
    {"name": "其他", "slug": "other"},
)

FIXED_TRICK_TERM_NAMES = tuple(item["name"] for item in FIXED_TRICK_TERM_DEFINITIONS)
FIXED_TRICK_TERM_SLUGS = tuple(item["slug"] for item in FIXED_TRICK_TERM_DEFINITIONS)
FIXED_TRICK_TERM_NAME_TO_ORDER = {
    item["name"]: index for index, item in enumerate(FIXED_TRICK_TERM_DEFINITIONS)
}
FIXED_TRICK_TERM_SLUG_TO_ORDER = {
    item["slug"]: index for index, item in enumerate(FIXED_TRICK_TERM_DEFINITIONS)
}
