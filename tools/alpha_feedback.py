from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
DEFAULT_LOG = Path(".kol-signal/alpha_feedback_log.json")

TOP_LEVEL_FIELDS = {
    "feedback_id",
    "version",
    "user_type",
    "environment",
    "input_source",
    "record_count",
    "issue_stage",
    "severity",
    "reproducible",
    "workaround",
    "resolution",
    "triage",
}
REQUIRED_FIELDS = TOP_LEVEL_FIELDS
USER_TYPES = {
    "brand_operator",
    "agency_operator",
    "marketing_intern",
    "independent_operator",
    "unknown",
}
ISSUE_STAGES = {
    "install",
    "input",
    "mapping",
    "campaign",
    "merge",
    "audit",
    "scoring",
    "export",
    "review",
    "feedback",
    "diagnostics",
    "documentation",
}
SEVERITIES = {"Blocker", "Major", "Minor"}
RESOLUTION_STATUSES = {
    "new",
    "triaged",
    "in_progress",
    "resolved",
    "wont_fix",
    "duplicate",
}

EMAIL_PATTERN = re.compile(
    r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
)
HANDLE_PATTERN = re.compile(r"(?<![A-Za-z0-9_])@[A-Za-z0-9_.-]{2,}")
URL_PATTERN = re.compile(r"(?i)(?:https?://|www\.)")
TOKEN_PATTERN = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|token|secret|password|authorization)\s*[:=]"
)
ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?:^|\s)(?:/(?:Users|home|private|var|tmp)/|~/|[A-Za-z]:[\\/])"
)


class FeedbackValidationError(ValueError):
    """A feedback record violates the private redacted-log contract."""


def priority_score(
    user_value: int,
    frequency: int,
    blocking: bool,
    implementation_cost: int,
) -> float:
    if not all(
        isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 5
        for value in (user_value, frequency, implementation_cost)
    ):
        raise FeedbackValidationError(
            "user_value, frequency, and implementation_cost must be integers 1–5."
        )
    if not isinstance(blocking, bool):
        raise FeedbackValidationError("blocking must be true or false.")
    blocking_factor = 2 if blocking else 1
    return round(
        user_value * frequency * blocking_factor / implementation_cost,
        2,
    )


def _validate_private_text(value: Any, field_name: str, maximum: int = 500) -> str:
    if not isinstance(value, str):
        raise FeedbackValidationError(f"{field_name} must be text.")
    cleaned = " ".join(value.split())
    if len(cleaned) > maximum:
        raise FeedbackValidationError(f"{field_name} is longer than {maximum} characters.")
    forbidden = (
        (EMAIL_PATTERN, "Email"),
        (HANDLE_PATTERN, "Handle"),
        (URL_PATTERN, "URL"),
        (TOKEN_PATTERN, "Token or secret"),
        (ABSOLUTE_PATH_PATTERN, "absolute path"),
    )
    for pattern, label in forbidden:
        if pattern.search(cleaned):
            raise FeedbackValidationError(
                f"{field_name} contains forbidden {label} data. Redact it first."
            )
    return cleaned


def _validate_resolution(value: Any, severity: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise FeedbackValidationError("resolution must be an object.")
    allowed = {"status", "owner", "summary"}
    unexpected = set(value) - allowed
    if unexpected:
        raise FeedbackValidationError(
            "resolution has unexpected fields: " + ", ".join(sorted(unexpected))
        )
    status = value.get("status")
    if status not in RESOLUTION_STATUSES:
        raise FeedbackValidationError("resolution.status is not supported.")
    owner = _validate_private_text(value.get("owner", ""), "resolution.owner", 80)
    summary = _validate_private_text(
        value.get("summary", ""),
        "resolution.summary",
        500,
    )
    if severity == "Blocker" and not owner:
        raise FeedbackValidationError("Blocker feedback requires an explicit owner.")
    return {"status": status, "owner": owner, "summary": summary}


def _validate_triage(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FeedbackValidationError("triage must be an object.")
    allowed = {
        "user_value",
        "frequency",
        "blocking",
        "implementation_cost",
        "priority_score",
    }
    unexpected = set(value) - allowed
    if unexpected:
        raise FeedbackValidationError(
            "triage has unexpected fields: " + ", ".join(sorted(unexpected))
        )
    required = allowed - {"priority_score"}
    missing = required - set(value)
    if missing:
        raise FeedbackValidationError(
            "triage is missing fields: " + ", ".join(sorted(missing))
        )
    score = priority_score(
        value["user_value"],
        value["frequency"],
        value["blocking"],
        value["implementation_cost"],
    )
    return {
        "user_value": value["user_value"],
        "frequency": value["frequency"],
        "blocking": value["blocking"],
        "implementation_cost": value["implementation_cost"],
        "priority_score": score,
    }


def validate_feedback_record(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise FeedbackValidationError("Feedback record must be an object.")
    unexpected = set(record) - TOP_LEVEL_FIELDS
    if unexpected:
        raise FeedbackValidationError(
            "Feedback record has unexpected fields: "
            + ", ".join(sorted(unexpected))
        )
    missing = REQUIRED_FIELDS - set(record)
    if missing:
        raise FeedbackValidationError(
            "Feedback record is missing fields: " + ", ".join(sorted(missing))
        )

    feedback_id = record["feedback_id"]
    if not isinstance(feedback_id, str) or not re.fullmatch(
        r"AF-[0-9]{8}-[0-9]{3,}", feedback_id
    ):
        raise FeedbackValidationError("feedback_id must match AF-YYYYMMDD-NNN.")
    version = record["version"]
    if not isinstance(version, str) or not re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+a[0-9]+", version
    ):
        raise FeedbackValidationError("version must use the Alpha package format.")
    if record["user_type"] not in USER_TYPES:
        raise FeedbackValidationError("user_type is not supported.")
    if record["issue_stage"] not in ISSUE_STAGES:
        raise FeedbackValidationError("issue_stage is not supported.")
    if record["severity"] not in SEVERITIES:
        raise FeedbackValidationError("severity must be Blocker, Major, or Minor.")
    if not isinstance(record["record_count"], int) or isinstance(
        record["record_count"], bool
    ) or record["record_count"] < 0:
        raise FeedbackValidationError("record_count must be a non-negative integer.")
    if not isinstance(record["reproducible"], bool):
        raise FeedbackValidationError("reproducible must be true or false.")

    normalized = copy.deepcopy(record)
    normalized["environment"] = _validate_private_text(
        record["environment"], "environment", 200
    )
    normalized["input_source"] = _validate_private_text(
        record["input_source"], "input_source", 160
    )
    normalized["workaround"] = _validate_private_text(
        record["workaround"], "workaround", 500
    )
    normalized["resolution"] = _validate_resolution(
        record["resolution"], record["severity"]
    )
    normalized["triage"] = _validate_triage(record["triage"])
    return normalized


def _empty_log() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "records": []}


def load_log(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _empty_log()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FeedbackValidationError("Feedback log is not valid UTF-8 JSON.") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise FeedbackValidationError("Feedback log schema is not supported.")
    records = payload.get("records")
    if not isinstance(records, list):
        raise FeedbackValidationError("Feedback log records must be a list.")
    return {
        "schema_version": SCHEMA_VERSION,
        "records": [validate_feedback_record(record) for record in records],
    }


def append_feedback(path: Path, record: Any) -> dict[str, Any]:
    normalized = validate_feedback_record(record)
    payload = load_log(path)
    if any(
        existing["feedback_id"] == normalized["feedback_id"]
        for existing in payload["records"]
    ):
        raise FeedbackValidationError(
            f"Duplicate feedback_id: {normalized['feedback_id']}"
        )
    payload["records"].append(normalized)
    payload["records"].sort(key=lambda item: item["feedback_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=".alpha-feedback-",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(payload, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
        temporary_path.replace(path)
    except OSError as exc:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise FeedbackValidationError("Could not write feedback log safely.") from exc
    return {
        "feedback_id": normalized["feedback_id"],
        "record_count": len(payload["records"]),
        "path_disclosed": False,
    }


def evaluate_adapter_gate(requests: Any) -> dict[str, Any]:
    if isinstance(requests, dict):
        if requests.get("schema_version") != SCHEMA_VERSION:
            raise FeedbackValidationError("Adapter request register schema is not supported.")
        requests = requests.get("requests")
    if not isinstance(requests, list) or not requests:
        return {
            "eligible": False,
            "missing": [
                "two_legal_redacted_schemas",
                "generic_mapping_inadequate",
                "demand_threshold",
                "maintenance_cost_acceptable",
            ],
            "unique_user_count": 0,
            "legal_schema_count": 0,
        }
    sources = {
        request.get("source_name")
        for request in requests
        if isinstance(request, dict)
    }
    legal_hashes: set[str] = set()
    user_keys: set[str] = set()
    generic_results: list[str] = []
    request_shares: list[float] = []
    maintenance_flags: list[bool] = []
    for request in requests:
        if not isinstance(request, dict):
            continue
        requester = request.get("requester_key")
        if isinstance(requester, str) and requester:
            user_keys.add(requester)
        generic_results.append(str(request.get("generic_mapping_result", "")))
        share = request.get("source_request_share", 0)
        request_shares.append(float(share) if isinstance(share, (int, float)) else 0.0)
        maintenance_flags.append(request.get("maintenance_cost_acceptable") is True)
        evidence = request.get("evidence", [])
        if isinstance(evidence, list):
            for item in evidence:
                if not isinstance(item, dict) or item.get("legal_and_redacted") is not True:
                    continue
                schema_hash = item.get("schema_hash")
                if isinstance(schema_hash, str) and schema_hash:
                    legal_hashes.add(schema_hash)

    conditions = {
        "single_source_scope": len(sources) == 1 and None not in sources,
        "two_legal_redacted_schemas": len(legal_hashes) >= 2,
        "generic_mapping_inadequate": bool(generic_results)
        and all(result in {"poor", "blocked"} for result in generic_results),
        "demand_threshold": len(user_keys) >= 2
        or max(request_shares, default=0.0) >= 0.5,
        "maintenance_cost_acceptable": bool(maintenance_flags)
        and all(maintenance_flags),
    }
    missing = [name for name, passed in conditions.items() if not passed]
    return {
        "eligible": not missing,
        "missing": missing,
        "unique_user_count": len(user_keys),
        "legal_schema_count": len(legal_hashes),
        "conditions": conditions,
    }


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FeedbackValidationError("Input is not valid UTF-8 JSON.") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Maintain a private, redacted Open Alpha feedback log."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--input", type=Path, required=True)
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("--input", type=Path, required=True)
    add_parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    gate_parser = subparsers.add_parser("adapter-gate")
    gate_parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            record = validate_feedback_record(_read_json(args.input))
            print(
                json.dumps(
                    {
                        "valid": True,
                        "feedback_id": record["feedback_id"],
                        "priority_score": record["triage"]["priority_score"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        elif args.command == "add":
            print(
                json.dumps(
                    append_feedback(args.log, _read_json(args.input)),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(
                json.dumps(
                    evaluate_adapter_gate(_read_json(args.input)),
                    ensure_ascii=False,
                    indent=2,
                )
            )
    except FeedbackValidationError as exc:
        print(f"alpha feedback error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
