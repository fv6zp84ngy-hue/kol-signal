from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class FormatVariant:
    """A deterministic tabular variation used by A2 compatibility tests."""

    name: str
    headers: list[str]
    rows: list[dict[str, Any]]
    encoding: str = "utf-8"
    expected_path: str = "native"


def _clone_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def _variant(
    name: str,
    headers: list[str],
    rows: list[dict[str, Any]],
    *,
    encoding: str = "utf-8",
    expected_path: str = "native",
) -> FormatVariant:
    return FormatVariant(
        name=name,
        headers=list(headers),
        rows=_clone_rows(rows),
        encoding=encoding,
        expected_path=expected_path,
    )


def build_nox_format_variants(
    headers: list[str],
    rows: list[dict[str, Any]],
) -> list[FormatVariant]:
    """Return stable variations without treating them as third-party evidence."""

    if not rows:
        raise ValueError("At least one source row is required.")

    variants: list[FormatVariant] = []

    variants.append(_variant("column_order_changed", list(reversed(headers)), rows))

    extra_headers = [*headers, "Internal Review Note"]
    extra_rows = _clone_rows(rows)
    for row in extra_rows:
        row["Internal Review Note"] = "synthetic-only"
    variants.append(_variant("unrelated_column_added", extra_headers, extra_rows))

    optional_headers = [header for header in headers if header != "Latest Brand Post"]
    optional_rows = [
        {header: row.get(header) for header in optional_headers}
        for row in rows
    ]
    variants.append(_variant("optional_column_removed", optional_headers, optional_rows))

    changed_headers = [
        f"  {header.lower()}  " if header in {"Nox ID", "Channel ID", "URL"} else header
        for header in headers
    ]
    header_lookup = dict(zip(headers, changed_headers, strict=True))
    changed_rows = [
        {header_lookup[header]: row.get(header) for header in headers}
        for row in rows
    ]
    variants.append(
        _variant(
            "header_case_and_space_changed",
            changed_headers,
            changed_rows,
            expected_path="generic",
        )
    )

    for name, value in (
        ("followers_plain", "128000"),
        ("followers_k", "128K"),
        ("followers_m", "1.2M"),
        ("missing_na", "N/A"),
        ("missing_dash", "-"),
        ("missing_empty", ""),
    ):
        changed = _clone_rows(rows)
        changed[0]["Total Followers"] = value
        variants.append(_variant(name, headers, changed))

    variants.append(_variant("utf8_sig", headers, rows, encoding="utf-8-sig"))

    variants.append(
        _variant(
            "worksheet_name_changed",
            headers,
            rows,
            expected_path="explicit_sheet",
        )
    )

    invalid_rows = _clone_rows(rows)
    invalid_rows[0]["Total Followers"] = "not-a-number"
    variants.append(_variant("single_row_invalid", headers, invalid_rows))

    drift_headers = [
        "Creator Record" if header == "Nox ID" else header
        for header in headers
    ]
    drift_lookup = dict(zip(headers, drift_headers, strict=True))
    drift_rows = [
        {drift_lookup[header]: row.get(header) for header in headers}
        for row in rows
    ]
    variants.append(
        _variant(
            "schema_drift",
            drift_headers,
            drift_rows,
            expected_path="generic",
        )
    )
    return variants


def write_csv_variant(variant: FormatVariant, output_path: Path) -> Path:
    """Write one variation as CSV for repeatable parser tests."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding=variant.encoding, newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=variant.headers,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(variant.rows)
    return output_path


def read_csv_source(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        return list(reader.fieldnames), [dict(row) for row in reader]


def generate_nox_variant_files(input_path: Path, output_dir: Path) -> Path:
    """Materialize CSV variations and a manifest for local compatibility checks."""

    headers, rows = read_csv_source(input_path)
    variants = build_nox_format_variants(headers, rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_variants: list[dict[str, Any]] = []
    for variant in variants:
        if variant.expected_path == "explicit_sheet":
            manifest_variants.append(
                {
                    "name": variant.name,
                    "materialized": False,
                    "fixture": "fixtures/waveinflu_creators.xlsx",
                    "worksheet": "Creators",
                    "expected_path": variant.expected_path,
                }
            )
            continue
        output_path = output_dir / f"{variant.name}.csv"
        write_csv_variant(variant, output_path)
        manifest_variants.append(
            {
                "name": variant.name,
                "materialized": True,
                "path": output_path.name,
                "encoding": variant.encoding,
                "expected_path": variant.expected_path,
            }
        )
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source": str(input_path),
                "data_classification": "fully_synthetic",
                "variants": manifest_variants,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate deterministic A2 Nox-like CSV format variations."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = generate_nox_variant_files(args.input, args.output)
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
