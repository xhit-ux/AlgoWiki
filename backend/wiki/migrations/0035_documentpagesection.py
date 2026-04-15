from django.db import migrations, models
import django.db.models.deletion


DEFAULT_DOCUMENT_PAGES = [
    {
        "key": "about",
        "slug": "about",
        "section_title": "关于AlgoWiki",
        "page_title": "关于 AlgoWiki",
        "description": "站点定位、内容范围与协作方式说明。",
        "content_md": "# 关于 AlgoWiki\n\nAlgoWiki 是一个面向程序设计竞赛学习者的结构化知识库与社区协作平台。",
        "display_order": 10,
    },
    {
        "key": "trick-guide",
        "slug": "trick-guide",
        "section_title": "trick 规范手册",
        "page_title": "trick 规范手册",
        "description": "用于说明 trick 技巧条目的提交要求。",
        "content_md": "## 标题\n\n标题应尽量简短，直接概括 trick 的核心用途、结论或适用场景。\n\n## 词条\n\n发布时必须选择对应词条，可多选，但应与内容实际相关。\n\n## 内容\n\n1. 说明 trick 的核心思路、适用范围与限制。\n2. 尽量附上 1 道或多道相关例题，并使用 Markdown 链接。\n3. 不接受代码模板、题解全文搬运、无实际内容的结论堆砌。\n4. 请遵守 Markdown 与 LaTeX 语法，保证排版清晰、表达准确。\n",
        "display_order": 20,
    },
    {
        "key": "announcement-guide",
        "slug": "announcement-guide",
        "section_title": "公告手册",
        "page_title": "赛事公告手册",
        "description": "用于说明赛事公告的编写范围与发布标准。",
        "content_md": "## 适用范围\n\n用于补充赛事时刻表中需要单独说明的内容，例如中文信息、邀请函、官网链接、报名方式、特殊提醒等。\n\n## 标题\n\n标题应直接对应赛事名称；如有必要，可补充年份、站次或阶段信息。\n\n## 内容\n\n1. 先写关键结论，再补充来源链接与细节说明。\n2. 时间、地点、语言、报名规则等信息应尽量可核实。\n3. 涉及时效性内容时，请写明更新时间。\n4. 不发布无法确认、容易误导或与赛事无关的内容。\n",
        "display_order": 30,
    },
    {
        "key": "admin-guide",
        "slug": "admin-guide",
        "section_title": "管理员手册",
        "page_title": "管理员手册",
        "description": "用于说明审核、管理与日常维护的基本原则。",
        "content_md": "## 审核原则\n\n以准确、可验证、可维护为原则，优先检查事实、链接、格式、分类与可读性。\n\n## 处理建议\n\n1. 内容完整、来源可靠、格式清晰的可通过。\n2. 信息不足、格式混乱或存在明显错误的应驳回，并补充批注。\n3. 对重复内容优先合并处理，避免页面信息分散。\n4. 涉及账号、权限、审核记录等操作时，请保留必要说明与日志。\n",
        "display_order": 40,
    },
]


def seed_document_sections(apps, schema_editor):
    ExtensionPage = apps.get_model("wiki", "ExtensionPage")
    DocumentPageSection = apps.get_model("wiki", "DocumentPageSection")

    for item in DEFAULT_DOCUMENT_PAGES:
        page, _ = ExtensionPage.objects.update_or_create(
            slug=item["slug"],
            defaults={
                "title": item["page_title"],
                "description": item["description"],
                "content_md": item["content_md"],
                "access_level": "public",
                "is_enabled": True,
            },
        )
        DocumentPageSection.objects.update_or_create(
            key=item["key"],
            defaults={
                "title": item["section_title"],
                "page": page,
                "display_order": item["display_order"],
                "is_visible": True,
            },
        )


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0034_fixed_trick_term_categories"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentPageSection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=120)),
                ("key", models.SlugField(max_length=120, unique=True)),
                ("display_order", models.PositiveIntegerField(db_index=True, default=0)),
                ("is_visible", models.BooleanField(db_index=True, default=True)),
                (
                    "page",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="document_page_sections",
                        to="wiki.extensionpage",
                    ),
                ),
            ],
            options={
                "ordering": ["display_order", "id"],
            },
        ),
        migrations.RunPython(seed_document_sections, noop_reverse),
    ]
