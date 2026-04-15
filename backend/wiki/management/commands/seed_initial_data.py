import os
import secrets
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from wiki.models import (
    Announcement,
    Article,
    Category,
    CompetitionNotice,
    CompetitionScheduleEntry,
    DocumentPageSection,
    ExtensionPage,
    FriendlyLink,
    TeamMember,
    TrickEntry,
    User,
)
from wiki.security import record_password_history
from wiki.seed_content.default_site_content import (
    DEFAULT_TEAM_MEMBER,
    DEFAULT_TRICK_DEFS,
    FRIENDLY_LINK_DEFS,
    build_default_competition_content,
)

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

DEFAULT_DOCUMENT_PAGE_DEFS = [
    {
        "key": "about",
        "slug": "about",
        "section_title": "关于AlgoWiki",
        "page_title": "关于 AlgoWiki",
        "description": "站点定位、内容范围与协作方式说明。",
        "content_md": "# 关于 AlgoWiki\n\nAlgoWiki 是一个公益性质的算法竞赛 Wiki 信息平台，围绕开源协作、信息共享、互助交流与友善社区建设展开，目标是帮助算法竞赛学习者更低成本地获取可靠资料、赛事信息与备赛经验。\n\n## 主要内容\n\n### 竞赛 Wiki\n\n竞赛 Wiki 以 [【打破信息差】萌新认识与入门算法竞赛](https://github.com/NullResot/xcpc) 为初始数据源，面向刚入门的竞赛选手，系统整理大学生算法竞赛相关信息。\n\n主要包含：\n\n1. 常见赛制与主要竞赛介绍。\n2. 入门训练建议、学习路线与资源汇总。\n3. 竞赛相关网站、项目与工具的整理。\n\n### 赛事专区\n\n赛事专区用于集中维护竞赛相关的时效信息与经验资料，主要包含：\n\n1. 比赛日历表：整理 Codeforces、AtCoder、牛客、洛谷等线上训练比赛日程。\n2. trick 技巧汇总：收集算法竞赛中的技巧、结论与经验，便于检索和复习。\n3. 赛事时刻表：整理年度线下竞赛安排，帮助选手了解比赛时间与阶段。\n4. 赛事公告：补充赛事时刻表中的详细说明，例如语言支持、邀请函、报名链接与特殊规则。\n5. 补题链接：以 [hh2048 / 历年 XCPC 赛事补题链接整理](https://github.com/hh2048/XCPC/tree/main/04%20-%20%E5%8E%86%E5%B9%B4XCPC%E8%B5%9B%E4%BA%8B%E8%A1%A5%E9%A2%98%E9%93%BE%E6%8E%A5%E6%95%B4%E7%90%86) 为初始数据源，帮助选手快速找到对应比赛的补题入口。\n\n## 其他页面\n\n1. 问答：用于提交网站建议、讨论竞赛问题与进行社区互助。\n2. 文档：用于记录站点说明、提交规范与管理员维护说明。\n3. 友链：用于收录和展示竞赛相关的优质网站。\n\n## 参与方式\n\n欢迎通过页面提交、问答反馈、GitHub 贡献等方式参与内容维护。官方交流群：1094808529。\n\n## 项目信息\n\n本项目起始于 2025 年 12 月 26 日 20:01:21。\n\n本项目正式上线于 2026 年 4 月 11 日。\n",
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

INSECURE_PLACEHOLDER_PASSWORDS = {
    "",
    "changeme123!",
    "replace-me",
    "replace-with-a-random-password",
    "<set-a-strong-superadmin-password>",
}


def resolve_seed_password(candidate: str, *, prefix: str) -> str:
    value = (candidate or "").strip()
    if value.lower() in INSECURE_PLACEHOLDER_PASSWORDS:
        return f"{prefix}{secrets.token_urlsafe(12)}!"
    return value


class Command(BaseCommand):
    help = "Seed initial categories, extension pages, super admin account, and starter content."

    def add_arguments(self, parser):
        parser.add_argument("--content-file", type=str, default="")
        parser.add_argument(
            "--skip-markdown-section-import",
            action="store_true",
            help="Only use content file for welcome article, skip sectionized markdown import.",
        )
        parser.add_argument(
            "--section-levels",
            type=str,
            default="3,2",
            help="Heading levels used by import_markdown_sections, comma-separated (default: 3,2).",
        )
        parser.add_argument(
            "--section-default-category",
            type=str,
            default="xcpc-preface",
            help="Fallback category slug for markdown section import.",
        )
        parser.add_argument(
            "--superadmin-username",
            type=str,
            default=os.getenv("SUPERADMIN_USERNAME", "superadmin"),
        )
        parser.add_argument(
            "--superadmin-password",
            type=str,
            default=os.getenv("SUPERADMIN_PASSWORD", ""),
        )
        parser.add_argument(
            "--superadmin-email",
            type=str,
            default=os.getenv("SUPERADMIN_EMAIL", "admin@example.com"),
        )
        parser.add_argument(
            "--reset-superadmin-password",
            action="store_true",
            help="Reset super admin password even when the account already exists.",
        )
        parser.add_argument(
            "--skip-demo-users",
            action="store_true",
            help="Skip creating demo role accounts (normal/school/admin).",
        )
        parser.add_argument(
            "--demo-password",
            type=str,
            default=os.getenv("DEMO_PASSWORD", ""),
            help="Password used by demo role accounts.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        superadmin_username = options["superadmin_username"]
        superadmin_password = resolve_seed_password(
            options["superadmin_password"],
            prefix="AlgoWiki-SuperAdmin-",
        )
        superadmin_email = options["superadmin_email"]
        reset_password = options["reset_superadmin_password"]

        superadmin, created = User.objects.get_or_create(
            username=superadmin_username,
            defaults={
                "email": superadmin_email,
                "role": User.Role.SUPERADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created or reset_password:
            superadmin.set_password(superadmin_password)
            if created:
                superadmin.save()
                self.stdout.write(self.style.SUCCESS(f"Created super admin: {superadmin_username}"))
            else:
                superadmin.save(update_fields=["password"])
                self.stdout.write(self.style.SUCCESS(f"Reset super admin password: {superadmin_username}"))
            record_password_history(superadmin)
        else:
            updated_fields = []
            if superadmin.role != User.Role.SUPERADMIN:
                superadmin.role = User.Role.SUPERADMIN
                updated_fields.append("role")
            if not superadmin.is_staff:
                superadmin.is_staff = True
                updated_fields.append("is_staff")
            if not superadmin.is_superuser:
                superadmin.is_superuser = True
                updated_fields.append("is_superuser")
            if superadmin.email != superadmin_email:
                superadmin.email = superadmin_email
                updated_fields.append("email")
            if updated_fields:
                superadmin.save(update_fields=updated_fields)

        category_defs = [
            ("0. 阅前须知", "xcpc-preface", None, Category.ModerationScope.PUBLIC, 10, True),
            ("1. 学术诚信", "xcpc-academic-integrity", None, Category.ModerationScope.PUBLIC, 20, True),
            ("2. 常见术语", "xcpc-common-terms", None, Category.ModerationScope.PUBLIC, 30, True),
            ("3. 竞赛概念", "xcpc-concepts", None, Category.ModerationScope.PUBLIC, 40, True),
            ("4. 比赛介绍", "xcpc-contests", None, Category.ModerationScope.SCHOOL, 50, True),
            ("5. 关键网站", "xcpc-sites", None, Category.ModerationScope.PUBLIC, 60, True),
            ("6. 代码工具", "xcpc-tools", None, Category.ModerationScope.PUBLIC, 70, True),
            ("7. 阶段任务", "xcpc-stages", None, Category.ModerationScope.PUBLIC, 80, True),
            ("8. 关于训练", "xcpc-training", None, Category.ModerationScope.PUBLIC, 90, True),
            ("9. 结语与致谢", "xcpc-closing", None, Category.ModerationScope.PUBLIC, 100, True),
            ("Getting Started", "getting-started", None, Category.ModerationScope.PUBLIC, 1000, False),
        ]

        categories = {}
        for name, slug, parent_slug, scope, order, is_visible in category_defs:
            parent = categories.get(parent_slug) if parent_slug else None
            category, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "parent": parent,
                    "moderation_scope": scope,
                    "order": order,
                    "is_visible": is_visible,
                },
            )
            categories[slug] = category

        Category.objects.filter(slug__in=LEGACY_CATEGORY_SLUGS).update(is_visible=False)

        for item in DEFAULT_DOCUMENT_PAGE_DEFS:
            page, _ = ExtensionPage.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "title": item["page_title"],
                    "description": item["description"],
                    "content_md": item["content_md"],
                    "access_level": ExtensionPage.AccessLevel.PUBLIC,
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
        ExtensionPage.objects.update_or_create(
            slug="labs",
            defaults={
                "title": "实验室",
                "description": "预留给后续交互工具与训练辅助功能。",
                "content_md": "# 实验室\n\n该页面保留用于后续功能扩展。",
                "access_level": ExtensionPage.AccessLevel.PUBLIC,
                "is_enabled": True,
            },
        )
        ExtensionPage.objects.update_or_create(
            slug="operations",
            defaults={
                "title": "运维面板",
                "description": "仅管理员可访问的扩展页。",
                "content_md": "# 运维面板\n\n该页面保留用于后续内部运维工具。",
                "access_level": ExtensionPage.AccessLevel.ADMIN,
                "is_enabled": True,
            },
        )

        Announcement.objects.update_or_create(
            title="欢迎来到 AlgoWiki",
            defaults={
                "content_md": "站点已上线，可浏览知识条目、提交修订、发起问答与工单协作。",
                "created_by": superadmin,
                "priority": 100,
                "is_published": True,
            },
        )

        content = self._load_content(options["content_file"])
        Article.objects.update_or_create(
            slug="welcome",
            defaults={
                "title": "欢迎来到 AlgoWiki",
                "summary": "项目概览与使用说明。",
                "content_md": content,
                "category": categories["xcpc-preface"],
                "author": superadmin,
                "last_editor": superadmin,
                "status": Article.Status.PUBLISHED,
                "is_featured": True,
            },
        )

        self._seed_default_team_member()
        self._seed_friendly_links(superadmin)
        self._seed_competition_content(superadmin)
        self._seed_default_tricks(superadmin)

        if options["content_file"] and not options["skip_markdown_section_import"]:
            self._import_markdown_sections(
                content_file=options["content_file"],
                author=superadmin_username,
                default_category=options["section_default_category"],
                section_levels=options["section_levels"],
            )

        demo_accounts = []
        if not options["skip_demo_users"]:
            demo_accounts = self._ensure_demo_users(
                resolve_seed_password(options["demo_password"], prefix="AlgoWiki-Demo-")
            )

        self.stdout.write(self.style.SUCCESS("Initial data has been seeded."))
        self.stdout.write(
            self.style.WARNING(
                f"Super admin credential -> username: {superadmin_username}, password: {superadmin_password}"
            )
        )
        if demo_accounts:
            self.stdout.write(self.style.WARNING("Demo credentials (for role testing):"))
            for account in demo_accounts:
                self.stdout.write(
                    self.style.WARNING(
                        f"- {account['username']} ({account['role']}): {account['password']}"
                    )
                )

    def _seed_default_team_member(self) -> None:
        TeamMember.objects.update_or_create(
            display_id=DEFAULT_TEAM_MEMBER["display_id"],
            defaults={
                "avatar_url": DEFAULT_TEAM_MEMBER["avatar_url"],
                "profile_url": DEFAULT_TEAM_MEMBER["profile_url"],
                "is_active": True,
                "sort_order": DEFAULT_TEAM_MEMBER["sort_order"],
            },
        )

    def _seed_friendly_links(self, operator: User) -> None:
        for item in FRIENDLY_LINK_DEFS:
            FriendlyLink.objects.update_or_create(
                name=item["name"],
                defaults={
                    "description": item["description"],
                    "url": item["url"],
                    "created_by": operator,
                    "is_enabled": True,
                    "order": item["order"],
                },
            )

    def _seed_competition_content(self, operator: User) -> None:
        notice_defs, schedule_defs = build_default_competition_content()
        notices = {}

        for item in notice_defs:
            notice, _ = CompetitionNotice.objects.update_or_create(
                title=item["title"],
                defaults={
                    "content_md": item["content_md"],
                    "series": item["series"],
                    "year": item["year"],
                    "stage": item["stage"],
                    "created_by": operator,
                    "updated_by": operator,
                    "is_visible": True,
                    "published_at": timezone.now(),
                },
            )
            notices[item["title"]] = notice

        for item in schedule_defs:
            CompetitionScheduleEntry.objects.update_or_create(
                event_date=item["event_date"],
                competition_type=item["competition_type"],
                defaults={
                    "competition_time_range": item["competition_time_range"],
                    "location": item["location"],
                    "qq_group": item["qq_group"],
                    "announcement": notices.get(item["notice_title"]),
                    "created_by": operator,
                    "updated_by": operator,
                },
            )

    def _seed_default_tricks(self, operator: User) -> None:
        for item in DEFAULT_TRICK_DEFS:
            TrickEntry.objects.update_or_create(
                title=item["title"],
                defaults={
                    "content_md": item["content_md"],
                    "author": operator,
                    "status": TrickEntry.Status.APPROVED,
                },
            )

    def _load_content(self, content_file: str) -> str:
        default_content = (
            "# AlgoWiki\n\n"
            "AlgoWiki 是一个面向算法竞赛学习者的结构化知识库与社区协作平台。\n\n"
            "- 浏览分类条目并系统学习\n"
            "- 提交 issue/request 与修订提议\n"
            "- 在问答区讨论训练问题\n"
            "- 在个人中心追踪贡献历史\n"
        )

        if not content_file:
            return default_content

        source_path = Path(content_file)
        if not source_path.exists():
            self.stdout.write(self.style.WARNING(f"Content file not found: {source_path}"))
            return default_content

        for encoding in ("utf-8", "utf-8-sig", "gb18030"):
            try:
                return source_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue

        self.stdout.write(self.style.WARNING("Could not decode content file, using fallback content."))
        return default_content

    def _import_markdown_sections(
        self,
        *,
        content_file: str,
        author: str,
        default_category: str,
        section_levels: str,
    ) -> None:
        source_path = Path(content_file)
        if not source_path.exists():
            self.stdout.write(self.style.WARNING(f"Section import skipped, content file not found: {source_path}"))
            return

        levels = []
        for item in str(section_levels).split(","):
            token = item.strip()
            if not token:
                continue
            try:
                level = int(token)
            except ValueError:
                self.stdout.write(self.style.WARNING(f"Ignore invalid section level: {token}"))
                continue
            if 1 <= level <= 6 and level not in levels:
                levels.append(level)
            else:
                self.stdout.write(self.style.WARNING(f"Ignore unsupported section level: {token}"))

        if not levels:
            self.stdout.write(self.style.WARNING("Section import skipped, no valid heading levels configured."))
            return

        for level in levels:
            self.stdout.write(
                f"Import markdown sections: level={level}, default_category={default_category}, author={author}"
            )
            call_command(
                "import_markdown_sections",
                file=str(source_path),
                author=author,
                default_category=default_category,
                split_level=level,
            )

    def _ensure_demo_users(self, default_password: str):
        demo_specs = [
            {
                "username": os.getenv("DEMO_NORMAL_USERNAME", "demo_normal"),
                "email": os.getenv("DEMO_NORMAL_EMAIL", "demo_normal@example.com"),
                "role": User.Role.NORMAL,
                "school_name": "Demo University",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "username": os.getenv("DEMO_SCHOOL_USERNAME", "demo_school"),
                "email": os.getenv("DEMO_SCHOOL_EMAIL", "demo_school@example.com"),
                "role": User.Role.SCHOOL,
                "school_name": "Demo University",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "username": os.getenv("DEMO_ADMIN_USERNAME", "demo_admin"),
                "email": os.getenv("DEMO_ADMIN_EMAIL", "demo_admin@example.com"),
                "role": User.Role.ADMIN,
                "school_name": "Demo University",
                "is_staff": True,
                "is_superuser": False,
            },
        ]

        created_accounts = []
        for spec in demo_specs:
            user, created = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "email": spec["email"],
                    "role": spec["role"],
                    "school_name": spec["school_name"],
                    "is_staff": spec["is_staff"],
                    "is_superuser": spec["is_superuser"],
                },
            )

            update_fields = []
            if user.email != spec["email"]:
                user.email = spec["email"]
                update_fields.append("email")
            if user.role != spec["role"]:
                user.role = spec["role"]
                update_fields.append("role")
            if user.school_name != spec["school_name"]:
                user.school_name = spec["school_name"]
                update_fields.append("school_name")
            if user.is_staff != spec["is_staff"]:
                user.is_staff = spec["is_staff"]
                update_fields.append("is_staff")
            if user.is_superuser != spec["is_superuser"]:
                user.is_superuser = spec["is_superuser"]
                update_fields.append("is_superuser")
            if user.is_banned:
                user.is_banned = False
                user.banned_reason = ""
                user.banned_at = None
                update_fields.append("is_banned")
                update_fields.append("banned_reason")
                update_fields.append("banned_at")
            if not user.is_active:
                user.is_active = True
                update_fields.append("is_active")

            user.set_password(default_password)
            update_fields.append("password")

            if created:
                user.save()
            else:
                user.save(update_fields=sorted(set(update_fields)))
            record_password_history(user)

            created_accounts.append(
                {
                    "username": spec["username"],
                    "role": spec["role"],
                    "password": default_password,
                }
            )

        return created_accounts
