from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .adapters import detect_native_adapter


CANONICAL_FIELDS = (
    "source_record_id",
    "platform",
    "platform_creator_id",
    "handle",
    "profile_url",
    "display_name",
    "followers",
    "average_views",
    "engagement_rate",
    "country",
    "language",
    "email",
    "email_role",
    "latest_post_at",
    "latest_sponsored_post_at",
    "observed_at",
    "email_observed_at",
    "is_estimated",
)

IDENTITY_FIELDS = {"platform_creator_id", "profile_url", "handle"}

HEADER_ALIASES = {
    "source_record_id": {
        "record id",
        "source id",
        "creator record id",
        "row id",
    },
    "platform": {"channel", "social platform", "network"},
    "platform_creator_id": {
        "channel id",
        "platform id",
        "creator id",
        "user id",
        "uid",
    },
    "handle": {"username", "user name", "screen name", "account", "creator handle"},
    "profile_url": {"url", "profile", "profile link", "channel url", "creator url"},
    "display_name": {"name", "creator name", "display name", "creator"},
    "followers": {
        "total followers",
        "follower count",
        "fans",
        "subscribers",
        "audience",
        "audience size",
    },
    "average_views": {"avg views", "average views", "mean views", "views average"},
    "engagement_rate": {"engagement", "engagement rate", "er", "eng rate"},
    "country": {"location", "market", "region", "creator country"},
    "language": {"content language", "primary language", "lang"},
    "email": {"business email", "contact email", "email address"},
    "email_role": {"email type", "contact type", "email role"},
    "latest_post_at": {"last post", "latest upload", "last upload", "latest post"},
    "latest_sponsored_post_at": {
        "latest brand post",
        "last sponsored post",
        "latest sponsored post",
        "last ad post",
    },
    "observed_at": {
        "observed at",
        "metrics updated at",
        "updated at",
        "retrieved at",
        "exported at",
    },
    "email_observed_at": {
        "email observed at",
        "email checked at",
        "email verified at",
    },
    "is_estimated": {"estimated", "estimated metrics", "data estimated", "is estimate"},
}


@dataclass(slots=True)
class MappingSuggestion:
    source_column: str
    target_field: str | None
    confidence: float
    status: str
    example_values: list[str]
    alternatives: list[tuple[str, float]] = field(default_factory=list)


@dataclass(slots=True)
class InputMappingPlan:
    input_path: Path
    fingerprint: str
    source: str
    origin: str
    mapping: dict[str, str]
    suggestions: list[MappingSuggestion]
    sheet_name: str | None = None
    adapter_version: str | None = None
    adapter_validation_level: str | None = None
    reused_config: Path | None = None
    input_columns: list[str] = field(default_factory=list)

    @property
    def ambiguous(self) -> list[MappingSuggestion]:
        return [item for item in self.suggestions if item.status == "Confirm"]

    @property
    def unmapped_columns(self) -> list[str]:
        return [item.source_column for item in self.suggestions if not item.target_field]


def normalized_header(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def header_fingerprint(headers: list[str]) -> str:
    normalized = "\n".join(normalized_header(header) for header in headers)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def compact_examples(rows: list[dict[str, Any]], column: str, limit: int = 3) -> list[str]:
    examples: list[str] = []
    for row in rows:
        value = row.get(column)
        if value in (None, ""):
            continue
        text = str(value).strip().replace("\n", " ")
        if text and text not in examples:
            examples.append(text[:80])
        if len(examples) >= limit:
            break
    return examples


def _header_similarity(header: str, target: str) -> float:
    normalized = normalized_header(header)
    canonical = normalized_header(target)
    if normalized == canonical:
        return 0.99
    spaced = normalized.replace("_", " ")
    aliases = HEADER_ALIASES.get(target, set())
    if spaced in aliases:
        return 0.92
    header_tokens = set(spaced.split())
    candidate_tokens = [
        set(alias.split()) for alias in aliases | {canonical.replace("_", " ")}
    ]
    token_scores = [
        len(header_tokens & candidate) / len(header_tokens | candidate)
        for candidate in candidate_tokens
        if header_tokens and candidate
    ]
    best = max(token_scores, default=0.0)
    return 0.45 + 0.35 * best if best >= 0.5 else 0.0


def _value_evidence(examples: list[str], target: str) -> float:
    if not examples:
        return 0.0
    lowered = [value.lower() for value in examples]
    ratio = lambda predicate: sum(predicate(value) for value in lowered) / len(lowered)
    if target == "email":
        return 0.25 * ratio(lambda value: bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value)))
    if target == "profile_url":
        return 0.25 * ratio(lambda value: value.startswith(("http://", "https://")))
    if target == "handle":
        return 0.22 * ratio(
            lambda value: value.startswith("@")
            or bool(re.fullmatch(r"[a-z0-9_.-]{2,40}", value))
        )
    if target == "platform":
        return 0.25 * ratio(lambda value: value in {"tiktok", "instagram", "youtube", "ig", "yt"})
    if target == "engagement_rate":
        return 0.18 * ratio(lambda value: value.endswith("%"))
    if target == "is_estimated":
        return 0.18 * ratio(lambda value: value in {"true", "false", "yes", "no", "0", "1"})
    if target in {"latest_post_at", "latest_sponsored_post_at", "observed_at", "email_observed_at"}:
        return 0.10 * ratio(
            lambda value: bool(re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}", value))
        )
    if target in {"followers", "average_views"}:
        return 0.08 * ratio(
            lambda value: bool(re.fullmatch(r"[\d,.]+\s*[km]?", value.replace(" ", "")))
        )
    return 0.0


def suggest_columns(
    headers: list[str], rows: list[dict[str, Any]]
) -> list[MappingSuggestion]:
    suggestions: list[MappingSuggestion] = []
    claimed_targets: set[str] = set()
    ranked_by_column: list[tuple[str, list[str], list[tuple[str, float]]]] = []
    for header in headers:
        examples = compact_examples(rows, header)
        ranked = []
        for target in CANONICAL_FIELDS:
            score = min(0.99, _header_similarity(header, target) + _value_evidence(examples, target))
            if score >= 0.45:
                ranked.append((target, round(score, 2)))
        ranked.sort(key=lambda item: (-item[1], item[0]))
        ranked_by_column.append((header, examples, ranked))

    ranked_by_column.sort(
        key=lambda item: item[2][0][1] if item[2] else 0.0,
        reverse=True,
    )
    provisional: dict[str, MappingSuggestion] = {}
    for header, examples, ranked in ranked_by_column:
        available = [item for item in ranked if item[0] not in claimed_targets]
        if not available or available[0][1] < 0.60:
            provisional[header] = MappingSuggestion(
                source_column=header,
                target_field=None,
                confidence=available[0][1] if available else 0.0,
                status="Unmapped",
                example_values=examples,
                alternatives=available[:3],
            )
            continue
        target, confidence = available[0]
        runner_up = available[1][1] if len(available) > 1 else 0.0
        status = "Auto" if confidence >= 0.90 and confidence - runner_up >= 0.10 else "Confirm"
        provisional[header] = MappingSuggestion(
            source_column=header,
            target_field=target,
            confidence=confidence,
            status=status,
            example_values=examples,
            alternatives=available[:3],
        )
        if status == "Auto":
            claimed_targets.add(target)

    return [provisional[header] for header in headers]


def _suggestions_from_mapping(
    headers: list[str],
    rows: list[dict[str, Any]],
    mapping: dict[str, str],
    status: str,
    confidence: float,
) -> list[MappingSuggestion]:
    return [
        MappingSuggestion(
            source_column=header,
            target_field=mapping.get(header),
            confidence=confidence if header in mapping else 0.0,
            status=status if header in mapping else "Unmapped",
            example_values=compact_examples(rows, header),
        )
        for header in headers
    ]


def read_mapping_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("mapping"), dict):
        raise ValueError(f"Unsupported mapping config: {path}")
    invalid_targets = set(payload["mapping"].values()) - set(CANONICAL_FIELDS)
    if invalid_targets:
        raise ValueError(
            f"Mapping config {path} contains unknown fields: {', '.join(sorted(invalid_targets))}"
        )
    return payload


def find_reusable_config(
    fingerprint: str,
    mapping_dir: Path | None,
    explicit_configs: list[Path],
) -> tuple[Path, dict[str, Any]] | None:
    candidates = list(explicit_configs)
    if mapping_dir:
        candidates.append(mapping_dir / f"{fingerprint}.json")
    for path in candidates:
        if not path.exists():
            continue
        payload = read_mapping_config(path)
        if payload.get("fingerprint") == fingerprint:
            return path, payload
    return None


def create_mapping_plan(
    input_path: Path,
    headers: list[str],
    rows: list[dict[str, Any]],
    *,
    sheet_name: str | None = None,
    mapping_dir: Path | None = None,
    explicit_configs: list[Path] | None = None,
) -> InputMappingPlan:
    fingerprint = header_fingerprint(headers)
    adapter = detect_native_adapter(headers)
    if adapter:
        mapping = {
            column: target for column, target in adapter.mapping.items() if column in headers
        }
        return InputMappingPlan(
            input_path=input_path,
            fingerprint=fingerprint,
            source=adapter.name,
            origin="native",
            mapping=mapping,
            sheet_name=sheet_name,
            adapter_version=adapter.version,
            adapter_validation_level=adapter.validation_level.value,
            suggestions=_suggestions_from_mapping(headers, rows, mapping, "Native", 1.0),
            input_columns=list(headers),
        )

    reusable = find_reusable_config(
        fingerprint,
        mapping_dir,
        explicit_configs or [],
    )
    if reusable:
        config_path, payload = reusable
        mapping = {
            column: target
            for column, target in payload["mapping"].items()
            if column in headers
        }
        return InputMappingPlan(
            input_path=input_path,
            fingerprint=fingerprint,
            source=payload.get("source", "generic"),
            origin="reused",
            mapping=mapping,
            sheet_name=sheet_name,
            reused_config=config_path,
            suggestions=_suggestions_from_mapping(headers, rows, mapping, "Reused", 1.0),
            input_columns=list(headers),
        )

    suggestions = suggest_columns(headers, rows)
    mapping = {
        item.source_column: item.target_field
        for item in suggestions
        if item.target_field and item.status == "Auto"
    }
    return InputMappingPlan(
        input_path=input_path,
        fingerprint=fingerprint,
        source="generic",
        origin="suggested",
        mapping=mapping,
        sheet_name=sheet_name,
        suggestions=suggestions,
        input_columns=list(headers),
    )


def validate_mapping(plan: InputMappingPlan) -> None:
    mapped_targets = set(plan.mapping.values())
    if "platform" not in mapped_targets:
        raise ValueError(f"{plan.input_path.name}: field 'platform' is not mapped.")
    if not (IDENTITY_FIELDS & mapped_targets):
        raise ValueError(
            f"{plan.input_path.name}: map at least one identity field: "
            "platform_creator_id, profile_url, or handle."
        )
    duplicate_targets = {
        target for target in mapped_targets if list(plan.mapping.values()).count(target) > 1
    }
    if duplicate_targets:
        raise ValueError(
            f"{plan.input_path.name}: multiple columns map to "
            f"{', '.join(sorted(duplicate_targets))}."
        )


def confirm_ambiguous_columns(
    plan: InputMappingPlan,
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> None:
    claimed_targets = set(plan.mapping.values())
    for item in plan.ambiguous:
        alternatives = [
            field_name
            for field_name, _ in item.alternatives
            if field_name not in claimed_targets
        ]
        if not alternatives:
            item.target_field = None
            item.status = "Unmapped"
            continue
        suggested = alternatives[0]
        examples = " | ".join(item.example_values) or "(no non-empty samples)"
        output_fn(
            f"\nAmbiguous column: {item.source_column}\n"
            f"Examples: {examples}\n"
            f"Suggested: {suggested} ({item.confidence:.2f})\n"
            f"Choices: {', '.join(alternatives)}, skip"
        )
        while True:
            answer = input_fn(f"Map '{item.source_column}' [{suggested}]: ").strip()
            selected = suggested if not answer else answer
            if selected == "skip":
                item.target_field = None
                item.status = "Unmapped"
                break
            if selected not in CANONICAL_FIELDS:
                output_fn(f"Unknown field '{selected}'. Enter a listed field or skip.")
                continue
            if selected in claimed_targets:
                output_fn(f"Field '{selected}' is already mapped. Choose another field.")
                continue
            item.target_field = selected
            item.status = "Confirmed"
            plan.mapping[item.source_column] = selected
            claimed_targets.add(selected)
            break
    validate_mapping(plan)


def save_mapping_config(plan: InputMappingPlan, mapping_dir: Path) -> Path:
    mapping_dir.mkdir(parents=True, exist_ok=True)
    path = mapping_dir / f"{plan.fingerprint}.json"
    payload = {
        "schema_version": 1,
        "fingerprint": plan.fingerprint,
        "source": plan.source,
        "mapping": dict(sorted(plan.mapping.items())),
        "confirmed_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def mapping_preview_rows(plan: InputMappingPlan) -> list[dict[str, Any]]:
    return [
        {
            "source_column": item.source_column,
            "target_field": item.target_field or "",
            "confidence": item.confidence,
            "status": item.status,
            "example_values": item.example_values,
            "alternatives": [field_name for field_name, _ in item.alternatives],
        }
        for item in plan.suggestions
    ]
