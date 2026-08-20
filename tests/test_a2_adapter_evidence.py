from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from kol_signal.adapters import (
    NOX_ADAPTER,
    WAVEINFLU_ADAPTER,
    AdapterValidationLevel,
    detect_native_adapter,
)
from kol_signal.core import build_normalized_record, load_records, read_tabular
from kol_signal.mapping import create_mapping_plan
from tools.format_variants import (
    build_nox_format_variants,
    generate_nox_variant_files,
    write_csv_variant,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


class AdapterEvidenceContractTests(unittest.TestCase):
    def test_native_adapters_disclose_synthetic_only_evidence_level(self) -> None:
        self.assertEqual(
            WAVEINFLU_ADAPTER.validation_level,
            AdapterValidationLevel.NOT_TESTED,
        )
        self.assertEqual(
            NOX_ADAPTER.validation_level,
            AdapterValidationLevel.NOT_TESTED,
        )
        self.assertTrue(WAVEINFLU_ADAPTER.evidence_ids)
        self.assertTrue(NOX_ADAPTER.evidence_ids)
        headers, rows = read_tabular(FIXTURES / "nox_creators.csv")
        plan = create_mapping_plan(FIXTURES / "nox_creators.csv", headers, rows)
        self.assertEqual(plan.adapter_validation_level, "Not Tested")

    def test_machine_readable_source_register_has_required_fields(self) -> None:
        register = json.loads(
            (FIXTURES / "data_source_register.json").read_text(encoding="utf-8")
        )
        required = {
            "source_name",
            "source_type",
            "acquisition_method",
            "license",
            "contains_pii",
            "redistributable",
            "verified_at",
            "adapter_status",
            "intended_use",
        }
        self.assertGreaterEqual(len(register["sources"]), 3)
        for source in register["sources"]:
            self.assertTrue(required.issubset(source))
            self.assertIn(
                source["adapter_status"],
                {item.value for item in AdapterValidationLevel},
            )

    def test_ground_truth_manifest_covers_key_anomalies(self) -> None:
        manifest = json.loads(
            (FIXTURES / "ground_truth_manifest.json").read_text(encoding="utf-8")
        )
        covered = {item["id"] for item in manifest["cases"]}
        self.assertTrue(
            {
                "three_sources_same_creator",
                "shared_agency_email",
                "same_handle_conflicting_platform_ids",
                "followers_spread_above_twenty_percent",
                "observed_time_missing",
                "invalid_followers",
                "market_mismatch",
            }.issubset(covered)
        )

    def test_structure_faithful_suite_is_100_to_300_records_and_has_no_pii(self) -> None:
        paths = [
            FIXTURES / "waveinflu_creators.xlsx",
            FIXTURES / "nox_creators.csv",
            FIXTURES / "manual_creators.xlsx",
        ]
        records, _ = load_records(paths)
        self.assertGreaterEqual(len(records), 100)
        self.assertLessEqual(len(records), 300)
        for record in records:
            if record.email:
                self.assertTrue(record.email.endswith("example.com"))
            if record.profile_url:
                self.assertIn(".example.com", record.profile_url)
            if record.display_name:
                self.assertTrue(record.display_name.startswith("Fixture "))
            for value in record.raw_payload.values():
                text = str(value or "")
                for email in re.findall(
                    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                    text,
                ):
                    self.assertTrue(email.lower().endswith("example.com"))
                for url in re.findall(r"https?://[^\s,;]+", text):
                    host = url.split("/", 3)[2].split(":", 1)[0].lower()
                    self.assertTrue(host.endswith("example.com"))


class FormatVariationGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.headers, cls.rows = read_tabular(FIXTURES / "nox_creators.csv")
        cls.variants = {
            variant.name: variant
            for variant in build_nox_format_variants(cls.headers, cls.rows[:3])
        }

    def test_generator_covers_at_least_ten_declared_variations(self) -> None:
        required = {
            "column_order_changed",
            "unrelated_column_added",
            "optional_column_removed",
            "header_case_and_space_changed",
            "followers_plain",
            "followers_k",
            "followers_m",
            "missing_na",
            "missing_dash",
            "missing_empty",
            "utf8_sig",
            "worksheet_name_changed",
            "single_row_invalid",
            "schema_drift",
        }
        self.assertTrue(required.issubset(self.variants))
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest_path = generate_nox_variant_files(
                FIXTURES / "nox_creators.csv",
                Path(temporary_directory),
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(
                {item["name"] for item in manifest["variants"]},
                set(self.variants),
            )

    def test_non_breaking_native_variations_remain_native(self) -> None:
        for name in (
            "column_order_changed",
            "unrelated_column_added",
            "optional_column_removed",
        ):
            variant = self.variants[name]
            self.assertEqual(detect_native_adapter(variant.headers), NOX_ADAPTER)

    def test_native_signature_drift_safely_falls_back_to_generic(self) -> None:
        for name in ("header_case_and_space_changed", "schema_drift"):
            variant = self.variants[name]
            self.assertIsNone(detect_native_adapter(variant.headers))
            plan = create_mapping_plan(
                Path(f"{name}.csv"),
                variant.headers,
                variant.rows,
            )
            self.assertEqual(plan.source, "generic")
            self.assertEqual(plan.origin, "suggested")

    def test_numeric_and_missing_variations_normalize_without_fabricating_zero(self) -> None:
        expected = {
            "followers_plain": 128000,
            "followers_k": 128000,
            "followers_m": 1200000,
            "missing_na": None,
            "missing_dash": None,
            "missing_empty": None,
        }
        for name, expected_followers in expected.items():
            variant = self.variants[name]
            record = build_normalized_record(
                variant.rows[0],
                NOX_ADAPTER.mapping,
                "nox",
                Path(f"{name}.csv"),
                2,
            )
            self.assertEqual(record.followers, expected_followers)
            if expected_followers is None and name != "missing_empty":
                self.assertIn("followers", record.invalid_fields)

    def test_utf8_sig_and_single_invalid_row_do_not_block_valid_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            utf8_path = base / "utf8_sig.csv"
            invalid_path = base / "single_row_invalid.csv"
            write_csv_variant(self.variants["utf8_sig"], utf8_path)
            write_csv_variant(self.variants["single_row_invalid"], invalid_path)

            utf8_headers, utf8_rows = read_tabular(utf8_path)
            self.assertEqual(utf8_headers[0], self.variants["utf8_sig"].headers[0])
            self.assertEqual(len(utf8_rows), 3)

            invalid_headers, invalid_rows = read_tabular(invalid_path)
            records = [
                build_normalized_record(
                    row,
                    NOX_ADAPTER.mapping,
                    "nox",
                    invalid_path,
                    index,
                )
                for index, row in enumerate(invalid_rows, start=2)
            ]
            self.assertEqual(len(records), 3)
            self.assertIn("followers", records[0].invalid_fields)
            self.assertIsNotNone(records[1].followers)
            self.assertEqual(invalid_headers, self.variants["single_row_invalid"].headers)

    def test_changed_worksheet_name_is_selected_explicitly(self) -> None:
        headers, rows = read_tabular(
            FIXTURES / "waveinflu_creators.xlsx",
            sheet_name="Creators",
        )
        self.assertEqual(headers[0], "Wave Creator ID")
        self.assertEqual(len(rows), 40)

    def test_unmapped_columns_are_preserved_in_raw_payload(self) -> None:
        variant = self.variants["unrelated_column_added"]
        record = build_normalized_record(
            variant.rows[0],
            NOX_ADAPTER.mapping,
            "nox",
            Path("extra.csv"),
            2,
        )
        self.assertEqual(record.raw_payload["Internal Review Note"], "synthetic-only")


if __name__ == "__main__":
    unittest.main()
