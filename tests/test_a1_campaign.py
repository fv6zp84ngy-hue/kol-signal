from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

from kol_signal.cli import main
from kol_signal.core import (
    CAMPAIGN_PARSER_VERSION,
    CampaignParseResult,
    aggregate_group,
    load_records,
    parse_campaign_result,
    run_pipeline,
    score_creator,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
CAMPAIGN_FIXTURES = FIXTURES / "campaign"
GOLDEN = json.loads(
    (CAMPAIGN_FIXTURES / "golden_cases.json").read_text(encoding="utf-8")
)
CASES = {case["id"]: case for case in GOLDEN["cases"]}
REFERENCE_TIME = datetime(2026, 7, 29, tzinfo=timezone.utc)


def campaign_snapshot(result: CampaignParseResult) -> dict[str, object]:
    campaign = result.parsed_campaign
    return {
        "markets": list(campaign.markets),
        "languages": list(campaign.languages),
        "platforms": list(campaign.platforms),
        "follower_min": campaign.follower_min,
        "follower_max": campaign.follower_max,
        "latest_post_max_age_days": campaign.latest_post_max_age_days,
        "require_contact_path": campaign.require_contact_path,
    }


class CampaignParserGoldenTests(unittest.TestCase):
    def parse_case(self, case_id: str) -> CampaignParseResult:
        return parse_campaign_result(CAMPAIGN_FIXTURES / CASES[case_id]["brief"])

    def test_aliases_and_number_formats_normalize_identically(self) -> None:
        expected = CASES["zh_aliases"]["expected"]
        for case_id in ("zh_aliases", "en_aliases", "comma_numbers"):
            with self.subTest(case=case_id):
                result = self.parse_case(case_id)
                self.assertEqual(campaign_snapshot(result), expected)
                self.assertFalse(result.conflicting_conditions)
                self.assertFalse(result.blocking_unrecognized_conditions)

    def test_unrecognized_hard_conditions_are_visible_and_blocking(self) -> None:
        result = self.parse_case("unrecognized_hard_conditions")
        texts = [item["text"] for item in result.unrecognized_conditions]
        for expected in CASES["unrecognized_hard_conditions"]["expected_unrecognized"]:
            self.assertTrue(any(expected in text for text in texts))
        self.assertEqual(
            len(result.blocking_unrecognized_conditions),
            CASES["unrecognized_hard_conditions"]["expected_blocking_count"],
        )
        self.assertTrue(result.requires_confirmation)

        unsupported_market = self.parse_case("unsupported_market")
        self.assertTrue(
            any(
                CASES["unsupported_market"]["expected_blocking_text"] in item["text"]
                for item in unsupported_market.blocking_unrecognized_conditions
            )
        )

    def test_conflicting_follower_ranges_are_detected(self) -> None:
        result = self.parse_case("conflicting_ranges")
        self.assertTrue(result.conflicting_conditions)
        self.assertEqual(
            result.conflicting_conditions[0]["field"],
            CASES["conflicting_ranges"]["expected_conflict_field"],
        )
        self.assertTrue(result.requires_resolution)

    def test_blocklist_and_topics_are_structured_without_new_scoring_dimension(self) -> None:
        result = self.parse_case("blocklist_topics")
        expected = CASES["blocklist_topics"]["expected"]
        self.assertEqual(list(result.parsed_campaign.blocklist), expected["blocklist"])
        self.assertEqual(list(result.parsed_campaign.topics), expected["topics"])
        topic_condition = next(
            item for item in result.recognized_conditions if item["field"] == "topics"
        )
        self.assertFalse(topic_condition["applied"])
        self.assertTrue(any("topic" in warning.lower() for warning in result.warnings))
        self.assertEqual(self.parse_case("zh_aliases").parsed_campaign.topics, ())

    def test_parser_is_deterministic_for_same_brief_and_version(self) -> None:
        first = self.parse_case("blocklist_topics")
        second = self.parse_case("blocklist_topics")
        self.assertEqual(first.parser_version, CAMPAIGN_PARSER_VERSION)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_blocklisted_handle_is_hard_excluded(self) -> None:
        result = self.parse_case("blocklist_topics")
        records, _ = load_records([FIXTURES / "nox_creators.csv"])
        record = next(
            item for item in records if item.handle == "fixture_t001_pet"
        )
        creator = aggregate_group([record], REFERENCE_TIME)
        score_creator(creator, result.parsed_campaign, REFERENCE_TIME)
        self.assertEqual(creator.action_level, "Excluded")
        self.assertIn("EXCLUDED_BLOCKLIST", creator.exclusion_reasons)


class CampaignCliAndRunTests(unittest.TestCase):
    def test_campaign_preview_returns_structured_json(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "campaign-preview",
                    "--brief",
                    str(CAMPAIGN_FIXTURES / "supported_zh.txt"),
                    "--format",
                    "json",
                ]
            )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["parser_version"], CAMPAIGN_PARSER_VERSION)
        self.assertEqual(payload["parsed_campaign"]["markets"], ["US"])
        self.assertIn("recognized_conditions", payload)
        self.assertIn("unrecognized_conditions", payload)

    def test_non_interactive_run_stops_on_unrecognized_hard_condition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        "run",
                        "--input",
                        str(FIXTURES / "nox_creators.csv"),
                        "--brief",
                        str(
                            CAMPAIGN_FIXTURES
                            / "unrecognized_hard_conditions.txt"
                        ),
                        "--output",
                        str(Path(temporary_directory) / "runs"),
                        "--non-interactive",
                    ]
                )
            self.assertEqual(exit_code, 2)
            self.assertIn("unrecognized Campaign condition", stderr.getvalue())
            self.assertFalse((Path(temporary_directory) / "runs").exists())

    def test_confirmed_campaign_config_allows_explicit_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            config_path = base / "confirmed_campaign.json"
            preview_stdout = io.StringIO()
            with redirect_stdout(preview_stdout):
                preview_exit = main(
                    [
                        "campaign-preview",
                        "--brief",
                        str(
                            CAMPAIGN_FIXTURES
                            / "unrecognized_hard_conditions.txt"
                        ),
                        "--confirm",
                        "--output",
                        str(config_path),
                        "--format",
                        "json",
                    ]
                )
            self.assertEqual(preview_exit, 0)
            self.assertTrue(config_path.exists())

            run_stdout = io.StringIO()
            with redirect_stdout(run_stdout):
                run_exit = main(
                    [
                        "run",
                        "--input",
                        str(FIXTURES / "nox_creators.csv"),
                        "--brief",
                        str(
                            CAMPAIGN_FIXTURES
                            / "unrecognized_hard_conditions.txt"
                        ),
                        "--campaign-config",
                        str(config_path),
                        "--output",
                        str(base / "runs"),
                        "--non-interactive",
                        "--format",
                        "json",
                    ]
                )
            self.assertEqual(run_exit, 0)
            payload = json.loads(run_stdout.getvalue())
            self.assertTrue(Path(payload["run_dir"]).is_dir())

    def test_conflicting_config_cannot_be_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        "campaign-preview",
                        "--brief",
                        str(CAMPAIGN_FIXTURES / "conflicting_ranges.txt"),
                        "--confirm",
                        "--output",
                        str(Path(temporary_directory) / "campaign.json"),
                    ]
                )
        self.assertEqual(exit_code, 2)
        self.assertIn("conflicting Campaign conditions", stderr.getvalue())

    def test_run_persists_final_campaign_in_manifest_config_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run_pipeline(
                input_paths=[FIXTURES / "nox_creators.csv"],
                brief_path=CAMPAIGN_FIXTURES / "supported_zh.txt",
                output_base=Path(temporary_directory) / "runs",
            )
            manifest = json.loads(
                (result.run_dir / "manifest.json").read_text(encoding="utf-8")
            )
            campaign_config = json.loads(
                (result.run_dir / "campaign.json").read_text(encoding="utf-8")
            )
            report = (result.run_dir / "report.md").read_text(encoding="utf-8")

        self.assertEqual(
            manifest["campaign_parse"]["parser_version"],
            CAMPAIGN_PARSER_VERSION,
        )
        self.assertEqual(campaign_config["parsed_campaign"]["markets"], ["US"])
        self.assertIn("已识别条件", report)
        self.assertIn("未识别条件", report)


if __name__ == "__main__":
    unittest.main()
