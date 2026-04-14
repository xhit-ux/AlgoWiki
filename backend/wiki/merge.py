from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from django.utils import timezone
from django.utils.dateparse import parse_datetime


@dataclass(frozen=True)
class ArticleSnapshot:
    title: str
    summary: str
    content_md: str
    updated_at: object = None


@dataclass(frozen=True)
class TextChange:
    start: int
    end: int
    replacement: tuple[str, ...]


def _normalize_text(value) -> str:
    return "" if value is None else str(value)


def _normalize_updated_at(value):
    if isinstance(value, str):
        parsed = parse_datetime(value)
        if parsed is not None:
            value = parsed
    if value is not None and timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    return value


def build_snapshot(*, title="", summary="", content_md="", updated_at=None) -> ArticleSnapshot:
    return ArticleSnapshot(
        title=_normalize_text(title),
        summary=_normalize_text(summary),
        content_md=_normalize_text(content_md),
        updated_at=_normalize_updated_at(updated_at),
    )


def snapshot_article(article) -> ArticleSnapshot:
    return build_snapshot(
        title=getattr(article, "title", ""),
        summary=getattr(article, "summary", ""),
        content_md=getattr(article, "content_md", ""),
        updated_at=getattr(article, "updated_at", None),
    )


def _split_lines(value: str) -> list[str]:
    return _normalize_text(value).splitlines(keepends=True)


def _collect_changes(base_lines: list[str], other_lines: list[str]) -> list[TextChange]:
    matcher = SequenceMatcher(a=base_lines, b=other_lines)
    changes: list[TextChange] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        changes.append(
            TextChange(
                start=i1,
                end=i2,
                replacement=tuple(other_lines[j1:j2]),
            )
        )
    return changes


def _same_change(left: TextChange, right: TextChange) -> bool:
    return (
        left.start == right.start
        and left.end == right.end
        and left.replacement == right.replacement
    )


def _changes_overlap(left: TextChange, right: TextChange) -> bool:
    left_insert = left.start == left.end
    right_insert = right.start == right.end
    if left_insert and right_insert:
        return left.start == right.start
    if left_insert:
        return right.start < left.start < right.end
    if right_insert:
        return left.start < right.start < left.end
    return max(left.start, right.start) < min(left.end, right.end)


def _build_conflict_block(*, current_text: str, proposed_text: str) -> str:
    current_body = _normalize_text(current_text)
    proposed_body = _normalize_text(proposed_text)
    return (
        "<<<<<<< Current Article\n"
        f"{current_body}"
        "=======\n"
        f"{proposed_body}"
        ">>>>>>> Your Revision\n"
    )


def _merge_scalar_field(*, field: str, base: str, current: str, proposed: str):
    base = _normalize_text(base)
    current = _normalize_text(current)
    proposed = _normalize_text(proposed)

    if proposed == current:
        return current, None, False
    if current == base:
        return proposed, None, False
    if proposed == base:
        return current, None, current != proposed

    return (
        _build_conflict_block(current_text=current, proposed_text=proposed),
        {
            "field": field,
            "base": base,
            "current": current,
            "proposed": proposed,
        },
        False,
    )


def _merge_content_field(*, base: str, current: str, proposed: str):
    base = _normalize_text(base)
    current = _normalize_text(current)
    proposed = _normalize_text(proposed)

    if proposed == current:
        return current, [], False
    if current == base:
        return proposed, [], False
    if proposed == base:
        return current, [], current != proposed

    base_lines = _split_lines(base)
    current_changes = _collect_changes(base_lines, _split_lines(current))
    proposed_changes = _collect_changes(base_lines, _split_lines(proposed))

    if not current_changes:
        return proposed, [], False
    if not proposed_changes:
        return current, [], current != proposed

    merged: list[str] = []
    conflicts = []
    current_index = 0
    proposed_index = 0
    position = 0
    rebased = False

    while True:
        next_current = (
            current_changes[current_index] if current_index < len(current_changes) else None
        )
        next_proposed = (
            proposed_changes[proposed_index] if proposed_index < len(proposed_changes) else None
        )
        if next_current is None and next_proposed is None:
            break

        next_start = min(
            next_current.start if next_current is not None else len(base_lines),
            next_proposed.start if next_proposed is not None else len(base_lines),
        )

        if position < next_start:
            merged.extend(base_lines[position:next_start])
            position = next_start
            continue

        current_change = (
            next_current if next_current is not None and next_current.start == position else None
        )
        proposed_change = (
            next_proposed
            if next_proposed is not None and next_proposed.start == position
            else None
        )

        if current_change is not None:
            overlapping_proposed = (
                next_proposed
                if next_proposed is not None and _changes_overlap(current_change, next_proposed)
                else None
            )
            if overlapping_proposed is not None:
                if _same_change(current_change, overlapping_proposed):
                    merged.extend(current_change.replacement)
                else:
                    current_text = "".join(current_change.replacement)
                    proposed_text = "".join(overlapping_proposed.replacement)
                    merged.append(
                        _build_conflict_block(
                            current_text=current_text,
                            proposed_text=proposed_text,
                        )
                    )
                    conflicts.append(
                        {
                            "field": "content_md",
                            "base": "".join(
                                base_lines[
                                    min(current_change.start, overlapping_proposed.start) : max(
                                        current_change.end, overlapping_proposed.end
                                    )
                                ]
                            ),
                            "current": current_text,
                            "proposed": proposed_text,
                        }
                    )
                position = max(current_change.end, overlapping_proposed.end)
                current_index += 1
                proposed_index += 1
                continue

            merged.extend(current_change.replacement)
            position = current_change.end
            current_index += 1
            rebased = True
            continue

        if proposed_change is not None:
            overlapping_current = (
                next_current
                if next_current is not None and _changes_overlap(proposed_change, next_current)
                else None
            )
            if overlapping_current is not None:
                if _same_change(overlapping_current, proposed_change):
                    merged.extend(proposed_change.replacement)
                else:
                    current_text = "".join(overlapping_current.replacement)
                    proposed_text = "".join(proposed_change.replacement)
                    merged.append(
                        _build_conflict_block(
                            current_text=current_text,
                            proposed_text=proposed_text,
                        )
                    )
                    conflicts.append(
                        {
                            "field": "content_md",
                            "base": "".join(
                                base_lines[
                                    min(overlapping_current.start, proposed_change.start) : max(
                                        overlapping_current.end, proposed_change.end
                                    )
                                ]
                            ),
                            "current": current_text,
                            "proposed": proposed_text,
                        }
                    )
                position = max(overlapping_current.end, proposed_change.end)
                current_index += 1
                proposed_index += 1
                continue

            merged.extend(proposed_change.replacement)
            position = proposed_change.end
            proposed_index += 1
            continue

        if position < len(base_lines):
            merged.append(base_lines[position])
            position += 1
        else:
            break

    if position < len(base_lines):
        merged.extend(base_lines[position:])

    return "".join(merged), conflicts, rebased


def merge_article_revision(*, base: ArticleSnapshot, current: ArticleSnapshot, proposed: ArticleSnapshot):
    merged_title, title_conflict, title_rebased = _merge_scalar_field(
        field="title",
        base=base.title,
        current=current.title,
        proposed=proposed.title,
    )
    merged_summary, summary_conflict, summary_rebased = _merge_scalar_field(
        field="summary",
        base=base.summary,
        current=current.summary,
        proposed=proposed.summary,
    )
    merged_content, content_conflicts, content_rebased = _merge_content_field(
        base=base.content_md,
        current=current.content_md,
        proposed=proposed.content_md,
    )

    conflicts = [
        conflict
        for conflict in [title_conflict, summary_conflict, *content_conflicts]
        if conflict is not None
    ]
    merged_snapshot = build_snapshot(
        title=merged_title,
        summary=merged_summary,
        content_md=merged_content,
        updated_at=current.updated_at,
    )
    return {
        "has_conflicts": bool(conflicts),
        "conflicts": conflicts,
        "merged": merged_snapshot,
        "rebased": any([title_rebased, summary_rebased, content_rebased]),
    }
