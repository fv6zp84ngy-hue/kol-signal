from __future__ import annotations

import json
import platform
import re
import tempfile
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from . import __version__
from .core import OutputError, PipelineError


DIAGNOSTIC_FILES = (
    "environment.json",
    "input_schemas.json",
    "redacted_manifest.json",
    "failure_context.json",
)

EMAIL_PATTERN = re.compile(
    r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
)
URL_PATTERN = re.compile(r"(?i)(?:https?://|www\.)")
SECRET_PATTERN = re.compile(
    r"(?i)(?:api[_-]?key|secret|token|authorization|bearer|password)"
)
WINDOWS_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")
ERROR_CODE_PATTERN = re.compile(r"^KS_[A-Z]+_[0-9]{3}$")

SAFE_ADAPTERS = {"waveinflu", "nox", "manual", "generic"}
SAFE_VALIDATION_LEVELS = {
    "Verified",
    "Experimental",
    "Generic Import",
    "Not Tested",
}
SAFE_MAPPING_ORIGINS = {
    "native",
    "generic",
    "suggested",
    "confirmed",
    "reused",
    "manifest",
}
SAFE_RUN_TYPES = {"standard", "demo"}
SAFE_DATA_CLASSIFICATIONS = {"user_provided", "fully_synthetic"}
SAFE_FAILURE_STAGES = {
    "input",
    "mapping",
    "normalization",
    "identity_resolution",
    "data_audit",
    "campaign",
    "scoring",
    "export",
    "review",
    "feedback",
}


class DiagnosticsError(PipelineError):
    """A diagnostics request that cannot be completed safely."""

    default_code = "KS_DIAGNOSTICS_001"


def diagnostic_file_list() -> tuple[str, ...]:
    return DIAGNOSTIC_FILES


def _safe_label(value: Any, *, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    cleaned = "".join(
        character if character.isprintable() else " "
        for character in value.strip()
    )
    if not cleaned or len(cleaned) > 120:
        return fallback
    if (
        EMAIL_PATTERN.search(cleaned)
        or URL_PATTERN.search(cleaned)
        or SECRET_PATTERN.search(cleaned)
        or cleaned.startswith(("/", "~/", "\\\\"))
        or WINDOWS_ABSOLUTE_PATTERN.search(cleaned)
        or cleaned.startswith("@")
    ):
        return fallback
    return cleaned


def _safe_enum(value: Any, allowed: set[str], fallback: str) -> str:
    return value if isinstance(value, str) and value in allowed else fallback


def _load_manifest(run_id: str, runs_dir: Path) -> tuple[Path, dict[str, Any]]:
    if not re.fullmatch(r"run_[A-Za-z0-9][A-Za-z0-9._-]{0,127}", run_id):
        raise DiagnosticsError("Run ID is not valid.")
    root = runs_dir.resolve()
    run_dir = (root / run_id).resolve()
    if run_dir.parent != root or not run_dir.is_dir():
        raise DiagnosticsError(f"Run does not exist: {run_id}")
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        raise DiagnosticsError(f"Run {run_id} has no manifest.json.")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DiagnosticsError("Run manifest cannot be read as valid UTF-8 JSON.") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise DiagnosticsError("Run manifest schema is not supported.")
    return run_dir, manifest


def _input_schemas(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    schemas: list[dict[str, Any]] = []
    plans = manifest.get("mapping_plans", [])
    if not isinstance(plans, list):
        return schemas
    for index, plan in enumerate(plans, start=1):
        if not isinstance(plan, dict):
            continue
        input_columns = plan.get("input_columns")
        mapping = plan.get("mapping")
        raw_columns = (
            list(input_columns)
            if isinstance(input_columns, list)
            else list(mapping)
            if isinstance(mapping, dict)
            else []
        )
        columns = [
            _safe_label(column, fallback=f"[redacted_column_{column_index}]")
            for column_index, column in enumerate(raw_columns, start=1)
        ]
        schemas.append(
            {
                "input_index": index,
                "adapter": _safe_enum(
                    plan.get("source"),
                    SAFE_ADAPTERS,
                    "generic",
                ),
                "adapter_version": _safe_label(
                    plan.get("adapter_version"),
                    fallback="unavailable",
                ),
                "adapter_validation_level": _safe_enum(
                    plan.get("adapter_validation_level"),
                    SAFE_VALIDATION_LEVELS,
                    "Generic Import",
                ),
                "mapping_origin": _safe_enum(
                    plan.get("origin"),
                    SAFE_MAPPING_ORIGINS,
                    "manifest",
                ),
                "worksheet": _safe_label(
                    plan.get("sheet_name"),
                    fallback="unavailable_or_redacted",
                ),
                "columns": columns,
            }
        )
    return schemas


def _redacted_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    plans = manifest.get("mapping_plans")
    reviews = manifest.get("review_decisions")
    return {
        "schema_version": 1,
        "run_type": _safe_enum(
            manifest.get("run_type"),
            SAFE_RUN_TYPES,
            "standard",
        ),
        "data_classification": _safe_enum(
            manifest.get("data_classification"),
            SAFE_DATA_CLASSIFICATIONS,
            "user_provided",
        ),
        "input_count": len(manifest.get("input_files", []))
        if isinstance(manifest.get("input_files"), list)
        else 0,
        "mapping_plan_count": len(plans) if isinstance(plans, list) else 0,
        "review_revision": (
            manifest.get("review_revision")
            if isinstance(manifest.get("review_revision"), int)
            else 0
        ),
        "review_decision_count": len(reviews) if isinstance(reviews, list) else 0,
        "top": manifest.get("top") if isinstance(manifest.get("top"), int) else None,
    }


def _failure_context(manifest: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    raw_error_code = manifest.get("error_code")
    error_code = (
        raw_error_code
        if isinstance(raw_error_code, str)
        and ERROR_CODE_PATTERN.fullmatch(raw_error_code)
        else None
    )
    failed_stage = _safe_enum(
        manifest.get("failed_stage"),
        SAFE_FAILURE_STAGES,
        "none_recorded",
    )
    expected_outputs = {
        "data_audit.xlsx",
        "creator_shortlist.xlsx",
        "merge_review.xlsx",
        "feedback_template.xlsx",
        "report.md",
        "campaign.json",
        "manifest.json",
    }
    present_outputs = {
        path.name for path in run_dir.iterdir() if path.is_file()
    }
    return {
        "error_code": error_code,
        "failed_stage": failed_stage,
        "run_artifact_stage": (
            "complete"
            if expected_outputs.issubset(present_outputs)
            else "partial"
        ),
    }


def _json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def create_diagnostics(
    *,
    run_id: str,
    runs_dir: Path,
    output: Path,
) -> dict[str, Any]:
    """Create a fixed-schema diagnostics ZIP without reading original inputs."""

    run_dir, manifest = _load_manifest(run_id, runs_dir)
    if output.suffix.lower() != ".zip":
        raise OutputError("Diagnostics output must use a .zip extension.")
    if output.exists():
        raise OutputError(f"Diagnostics output already exists: {output.name}")
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OutputError("Cannot create the diagnostics output directory.") from exc

    payloads = {
        "environment.json": {
            "product": "kol-signal",
            "product_version": __version__,
            "python_version": platform.python_version(),
            "operating_system": {
                "name": platform.system(),
                "release": platform.release(),
            },
        },
        "input_schemas.json": _input_schemas(manifest),
        "redacted_manifest.json": _redacted_manifest(manifest),
        "failure_context.json": _failure_context(manifest, run_dir),
    }

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".kol-signal-diagnostics-",
            suffix=".tmp",
            dir=output.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
        with ZipFile(temporary_path, "w", compression=ZIP_DEFLATED) as archive:
            for name in DIAGNOSTIC_FILES:
                archive.writestr(name, _json_bytes(payloads[name]))
        temporary_path.replace(output)
    except OSError as exc:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise OutputError("Cannot write the diagnostics ZIP.") from exc

    return {
        "output": output.name,
        "files": list(DIAGNOSTIC_FILES),
        "privacy": {
            "original_values_included": False,
            "campaign_text_included": False,
            "absolute_paths_included": False,
            "network_accessed": False,
        },
    }
