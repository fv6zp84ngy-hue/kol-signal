from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import PipelineError, file_hash, load_run_manifest, read_tabular
from .reporting import write_feedback_report


BOOLEAN_FIELDS = (
    "merge_correct",
    "shortlist_accepted",
    "contact_correct",
    "actually_contacted",
    "delivered",
    "bounced",
    "replied",
    "positive_reply",
)

REQUIRED_FIELDS = {"creator_id", *BOOLEAN_FIELDS, "feedback_note"}


@dataclass(slots=True)
class FeedbackResult:
    run_id: str
    run_dir: Path
    metrics: list[dict[str, Any]]
    feedback_count: int
    note_count: int
    warning_count: int
    output_files: tuple[Path, ...]


def parse_optional_bool(value: Any, *, row_number: int, field_name: str) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in {0, 1}:
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"true", "yes", "y", "1"}:
        return True
    if normalized in {"false", "no", "n", "0"}:
        return False
    raise PipelineError(
        f"Invalid boolean at row {row_number}, column {field_name}: {value}"
    )


def _rate_metric(
    key: str,
    label: str,
    numerator: int,
    denominator: int,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "kind": "rate",
        "value": numerator / denominator if denominator else None,
        "numerator": numerator,
        "denominator": denominator,
    }


def calculate_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merge_reviewed = [row for row in rows if row["merge_correct"] is not None]
    shortlist_reviewed = [row for row in rows if row["shortlist_accepted"] is not None]
    contacts_reviewed = [row for row in rows if row["contact_correct"] is not None]
    actually_contacted = sum(row["actually_contacted"] is True for row in rows)
    delivered = sum(row["delivered"] is True for row in rows)
    replied = sum(row["replied"] is True for row in rows)
    positive = sum(row["positive_reply"] is True for row in rows)
    return [
        _rate_metric(
            "merge_accuracy",
            "合并准确率",
            sum(row["merge_correct"] is True for row in merge_reviewed),
            len(merge_reviewed),
        ),
        _rate_metric(
            "shortlist_acceptance_rate",
            "推荐接受率",
            sum(row["shortlist_accepted"] is True for row in shortlist_reviewed),
            len(shortlist_reviewed),
        ),
        _rate_metric(
            "contact_accuracy",
            "联系方式准确率",
            sum(row["contact_correct"] is True for row in contacts_reviewed),
            len(contacts_reviewed),
        ),
        {
            "key": "actually_contacted",
            "label": "实际联系人数",
            "kind": "count",
            "value": actually_contacted,
            "numerator": actually_contacted,
            "denominator": None,
        },
        _rate_metric(
            "delivery_rate",
            "送达率",
            delivered,
            actually_contacted,
        ),
        _rate_metric(
            "reply_rate",
            "回复率",
            replied,
            delivered,
        ),
        _rate_metric(
            "positive_reply_rate",
            "正向回复率",
            positive,
            delivered,
        ),
    ]


def feedback_warnings(rows: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for row in rows:
        creator_id = row["creator_id"]
        if row["delivered"] is True and row["actually_contacted"] is not True:
            warnings.append(f"{creator_id}: delivered=TRUE but actually_contacted is not TRUE.")
        if row["bounced"] is True and row["delivered"] is True:
            warnings.append(f"{creator_id}: delivered and bounced are both TRUE.")
        if row["replied"] is True and row["delivered"] is not True:
            warnings.append(f"{creator_id}: replied=TRUE but delivered is not TRUE.")
        if row["positive_reply"] is True and row["replied"] is not True:
            warnings.append(f"{creator_id}: positive_reply=TRUE but replied is not TRUE.")
    return warnings


def summarize_notes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    creators_by_note: dict[str, list[str]] = defaultdict(list)
    original_text: dict[str, str] = {}
    for row in rows:
        note = re.sub(r"\s+", " ", str(row.get("feedback_note") or "")).strip()
        if not note:
            continue
        normalized = note.casefold()
        original_text.setdefault(normalized, note)
        creators_by_note[normalized].append(row["creator_id"])
    counts = Counter(
        {normalized: len(creator_ids) for normalized, creator_ids in creators_by_note.items()}
    )
    return [
        {
            "feedback_note": original_text[normalized],
            "occurrences": count,
            "creator_ids": sorted(creators_by_note[normalized]),
        }
        for normalized, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], original_text[item[0]]),
        )
    ]


def format_metric_value(metric: dict[str, Any]) -> str:
    if metric["value"] is None:
        return "null（暂无有效分母）"
    if metric["kind"] == "rate":
        return f"{metric['value']:.1%}（{metric['numerator']}/{metric['denominator']}）"
    return str(metric["value"])


def write_feedback_markdown(
    path: Path,
    *,
    run_id: str,
    metrics: list[dict[str, Any]],
    notes: list[dict[str, Any]],
    warnings: list[str],
) -> None:
    lines = [
        "# Creator Signal Intelligence — Feedback Report",
        "",
        f"> Run ID: `{run_id}`  ",
        "> 仅展示描述统计；不会基于本轮样本自动修改评分权重。",
        "",
        "## 核心指标",
        "",
    ]
    for metric in metrics:
        lines.append(f"- {metric['label']}：{format_metric_value(metric)}")
    lines.extend(["", "## 用户文字反馈摘要", ""])
    if notes:
        for item in notes[:20]:
            creator_ids = ", ".join(item["creator_ids"])
            lines.append(
                f"- {item['feedback_note']}（{item['occurrences']} 次；{creator_ids}）"
            )
    else:
        lines.append("- 暂无文字反馈。")
    lines.extend(["", "## 数据校验提醒", ""])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- 未发现明显的状态逻辑冲突。")
    lines.extend(
        [
            "",
            "## 解释限制",
            "",
            "- 分母为 0 的比率输出 `null`，不显示为 0%。",
            "- 文字摘要仅合并完全相同的反馈，不进行模型推断或情绪归因。",
            "- 当前结果不能证明某个评分规则或数据源具有因果优势。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def import_feedback(
    *,
    run_id: str,
    feedback_input: Path,
    runs_dir: Path = Path("runs"),
    feedback_sheet_name: str | None = None,
) -> FeedbackResult:
    run_dir = runs_dir / run_id
    if not run_dir.is_dir():
        raise PipelineError(f"Run does not exist: {run_id}")
    manifest = load_run_manifest(run_dir)
    shortlist_path = run_dir / "creator_shortlist.xlsx"
    if not shortlist_path.exists():
        raise PipelineError(f"Shortlist is missing for Run {run_id}.")

    shortlist_headers, shortlist_rows = read_tabular(shortlist_path)
    required_context = {
        "creator_id",
        "action_level",
        "reference_score",
        "platform",
        "handle",
    }
    if not required_context.issubset(shortlist_headers):
        raise PipelineError("creator_shortlist.xlsx is missing required context columns.")
    context_by_creator = {
        str(row["creator_id"]).strip(): row for row in shortlist_rows
    }

    headers, raw_rows = read_tabular(
        feedback_input,
        sheet_name=feedback_sheet_name,
    )
    missing = REQUIRED_FIELDS - set(headers)
    if missing:
        raise PipelineError(
            "Feedback workbook is missing columns: " + ", ".join(sorted(missing))
        )

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row_number, raw in enumerate(raw_rows, start=2):
        creator_id = str(raw.get("creator_id") or "").strip()
        if not creator_id:
            raise PipelineError(f"Feedback row {row_number} has no creator_id.")
        if creator_id in seen:
            raise PipelineError(f"Duplicate creator_id in feedback: {creator_id}")
        if creator_id not in context_by_creator:
            raise PipelineError(
                f"Feedback row {row_number} references an unknown creator_id: {creator_id}"
            )
        seen.add(creator_id)
        context = context_by_creator[creator_id]
        parsed = {
            "creator_id": creator_id,
            "action_level": context.get("action_level"),
            "reference_score": context.get("reference_score"),
            "platform": context.get("platform"),
            "handle": context.get("handle"),
            "feedback_note": str(raw.get("feedback_note") or "").strip(),
        }
        for field_name in BOOLEAN_FIELDS:
            parsed[field_name] = parse_optional_bool(
                raw.get(field_name),
                row_number=row_number,
                field_name=field_name,
            )
        rows.append(parsed)

    metrics = calculate_metrics(rows)
    notes = summarize_notes(rows)
    warnings = feedback_warnings(rows)
    report_xlsx = run_dir / "feedback_report.xlsx"
    report_md = run_dir / "feedback_report.md"
    write_feedback_report(
        report_xlsx,
        run_id=run_id,
        metrics=metrics,
        feedback_rows=rows,
        notes=notes,
        warnings=warnings,
    )
    write_feedback_markdown(
        report_md,
        run_id=run_id,
        metrics=metrics,
        notes=notes,
        warnings=warnings,
    )

    manifest["feedback"] = {
        "input_path": str(feedback_input.resolve()),
        "sha256": file_hash(feedback_input),
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "feedback_rows": len(rows),
        "metrics": {metric["key"]: metric["value"] for metric in metrics},
        "warning_count": len(warnings),
    }
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return FeedbackResult(
        run_id=run_id,
        run_dir=run_dir,
        metrics=metrics,
        feedback_count=len(rows),
        note_count=sum(bool(row["feedback_note"]) for row in rows),
        warning_count=len(warnings),
        output_files=(report_xlsx, report_md),
    )
