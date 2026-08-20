from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from kol_signal.adapters import NOX_ADAPTER, WAVEINFLU_ADAPTER, detect_native_adapter
from kol_signal.core import PipelineError, prepare_input_mappings, read_tabular
from kol_signal.mapping import (
    confirm_ambiguous_columns,
    create_mapping_plan,
    save_mapping_config,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


class NativeAdapterTests(unittest.TestCase):
    def test_waveinflu_and_nox_are_native_adapters(self) -> None:
        wave_headers, wave_rows = read_tabular(FIXTURES / "waveinflu_creators.xlsx")
        nox_headers, nox_rows = read_tabular(FIXTURES / "nox_creators.csv")

        self.assertEqual(detect_native_adapter(wave_headers), WAVEINFLU_ADAPTER)
        self.assertEqual(detect_native_adapter(nox_headers), NOX_ADAPTER)

        wave_plan = create_mapping_plan(
            FIXTURES / "waveinflu_creators.xlsx",
            wave_headers,
            wave_rows,
        )
        nox_plan = create_mapping_plan(
            FIXTURES / "nox_creators.csv",
            nox_headers,
            nox_rows,
        )
        self.assertEqual(wave_plan.origin, "native")
        self.assertEqual(nox_plan.origin, "native")
        self.assertFalse(wave_plan.ambiguous)
        self.assertFalse(nox_plan.ambiguous)
        self.assertEqual(wave_plan.mapping["Profile Link"], "profile_url")
        self.assertEqual(nox_plan.mapping["Channel ID"], "platform_creator_id")


class GenericMappingTests(unittest.TestCase):
    @staticmethod
    def write_generic_csv(path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "Network",
                    "Creator",
                    "Profile",
                    "Audience",
                    "Contact",
                    "Updated",
                    "Internal Note",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "Network": "TikTok",
                    "Creator": "@dogtech",
                    "Profile": "https://example.com/dogtech?utm_source=test",
                    "Audience": "128K",
                    "Contact": "hello@example.com",
                    "Updated": "2026-07-29",
                    "Internal Note": "synthetic",
                }
            )

    def test_preview_separates_auto_confirm_and_unmapped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "generic.csv"
            self.write_generic_csv(path)
            headers, rows = read_tabular(path)
            plan = create_mapping_plan(path, headers, rows)
            status_by_column = {
                item.source_column: (item.target_field, item.status)
                for item in plan.suggestions
            }

            self.assertEqual(status_by_column["Network"], ("platform", "Auto"))
            self.assertEqual(status_by_column["Profile"], ("profile_url", "Auto"))
            self.assertEqual(status_by_column["Audience"], ("followers", "Auto"))
            self.assertEqual(status_by_column["Creator"], ("display_name", "Confirm"))
            self.assertEqual(status_by_column["Contact"], ("email", "Confirm"))
            self.assertEqual(status_by_column["Updated"], ("observed_at", "Confirm"))
            self.assertEqual(status_by_column["Internal Note"], (None, "Unmapped"))

    def test_confirmed_mapping_is_saved_and_reused_by_header_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            path = base / "first_export.csv"
            second_path = base / "second_export.csv"
            mapping_dir = base / "mappings"
            self.write_generic_csv(path)
            self.write_generic_csv(second_path)
            headers, rows = read_tabular(path)
            plan = create_mapping_plan(path, headers, rows)

            answers = iter(["handle", "", "skip"])
            confirm_ambiguous_columns(
                plan,
                input_fn=lambda _: next(answers),
                output_fn=lambda _: None,
            )
            config_path = save_mapping_config(plan, mapping_dir)
            self.assertTrue(config_path.exists())
            self.assertEqual(plan.mapping["Creator"], "handle")
            self.assertEqual(plan.mapping["Contact"], "email")
            self.assertNotIn("Updated", plan.mapping)

            second_headers, second_rows = read_tabular(second_path)
            reused = create_mapping_plan(
                second_path,
                second_headers,
                second_rows,
                mapping_dir=mapping_dir,
            )
            self.assertEqual(reused.origin, "reused")
            self.assertEqual(reused.reused_config, config_path)
            self.assertFalse(reused.ambiguous)
            self.assertEqual(reused.mapping, plan.mapping)

    def test_non_interactive_run_refuses_ambiguous_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "generic.csv"
            self.write_generic_csv(path)
            with self.assertRaisesRegex(PipelineError, "ambiguous columns"):
                prepare_input_mappings([path], interactive=False)


if __name__ == "__main__":
    unittest.main()
