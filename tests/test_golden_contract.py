from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kol_signal.core import (
    Campaign,
    aggregate_group,
    identity_resolution,
    load_records,
    mark_review_creators,
    parse_campaign,
    run_pipeline,
    score_creator,
    serialize_debug_summary,
    sort_creators,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
GOLDEN_PATH = FIXTURES / "golden_tests.json"
REFERENCE_TIME = datetime(2026, 7, 29, tzinfo=timezone.utc)
ALL_INPUTS = [
    FIXTURES / "waveinflu_creators.xlsx",
    FIXTURES / "nox_creators.csv",
    FIXTURES / "manual_creators.xlsx",
]


class PublicBetaGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        payload = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
        cls.cases = {case["id"]: case for case in payload["cases"]}
        cls.records, _ = load_records(ALL_INPUTS)
        cls.records_by_id = {
            record.source_record_id: record for record in cls.records
        }

    def case(self, case_id: str) -> dict[str, Any]:
        return self.cases[case_id]

    def records_for(self, case_id: str):
        ids = self.case(case_id)["input"]["source_record_ids"]
        return [self.records_by_id[record_id] for record_id in ids]

    def aggregate_case(self, case_id: str):
        groups, review_items = identity_resolution(self.records_for(case_id))
        creators = [
            aggregate_group(group, REFERENCE_TIME)
            for group in groups
        ]
        return creators, review_items

    @staticmethod
    def campaign_from_case(case: dict[str, Any]) -> Campaign:
        values = case["input"]["campaign"]
        return Campaign(
            brand="Golden Test Brand",
            markets=tuple(values["markets"]),
            languages=tuple(values["languages"]),
            platforms=(),
            follower_min=values["follower_min"],
            follower_max=values["follower_max"],
            latest_post_max_age_days=values["latest_post_max_age_days"],
            require_contact_path=values["require_contact_path"],
            raw_text="Golden Test campaign; no inferred criteria.",
        )

    def decision_snapshot(self) -> str:
        groups, review_items = identity_resolution(self.records)
        creators = [
            aggregate_group(group, REFERENCE_TIME)
            for group in groups
        ]
        mark_review_creators(creators, review_items)
        campaign = parse_campaign(FIXTURES / "campaign.txt")
        for creator in creators:
            score_creator(creator, campaign, REFERENCE_TIME)
        sort_creators(creators)
        return serialize_debug_summary(creators)

    def test_golden_contract_contains_the_ten_frozen_cases(self) -> None:
        self.assertEqual(
            set(self.cases),
            {
                "three_sources_same_creator",
                "shared_agency_email",
                "same_handle_conflicting_platform_ids",
                "followers_spread_above_twenty_percent",
                "observed_time_missing",
                "invalid_followers",
                "missing_email_otherwise_good",
                "market_mismatch",
                "same_input_is_deterministic",
                "model_disabled_core_outputs",
            },
        )

    def test_three_sources_same_creator_merge_into_one(self) -> None:
        case = self.case("three_sources_same_creator")
        creators, _ = self.aggregate_case(case["id"])
        self.assertEqual(
            len(creators),
            case["expected"]["canonical_creator_count"],
        )
        self.assertEqual(
            creators[0].source_record_ids,
            case["expected"]["merged_source_record_ids"],
        )

    def test_shared_agency_email_does_not_merge_creators(self) -> None:
        case = self.case("shared_agency_email")
        creators, _ = self.aggregate_case(case["id"])
        self.assertEqual(
            len(creators),
            case["expected"]["canonical_creator_count"],
        )
        self.assertTrue(case["expected"]["must_not_auto_merge"])
        self.assertTrue(all(len(creator.records) == 1 for creator in creators))

    def test_same_handle_with_conflicting_platform_ids_enters_review(self) -> None:
        case = self.case("same_handle_conflicting_platform_ids")
        creators, review_items = self.aggregate_case(case["id"])
        self.assertEqual(
            len(creators),
            case["expected"]["canonical_creator_count"],
        )
        self.assertTrue(case["expected"]["review_required"])
        review_ids = {
            value
            for item in review_items
            for value in (item["candidate_a"], item["candidate_b"])
        }
        self.assertEqual(
            review_ids,
            set(case["input"]["source_record_ids"]),
        )

    def test_followers_spread_above_twenty_percent_is_high_conflict(self) -> None:
        case = self.case("followers_spread_above_twenty_percent")
        creators, _ = self.aggregate_case(case["id"])
        followers_conflict = next(
            conflict
            for conflict in creators[0].conflicts
            if conflict.field == case["input"]["field"]
        )
        self.assertEqual(
            followers_conflict.level,
            case["expected"]["conflict_level"],
        )

    def test_missing_observed_time_is_never_fresh(self) -> None:
        case = self.case("observed_time_missing")
        creators, _ = self.aggregate_case(case["id"])
        statuses = {
            item.status
            for item in creators[0].stale_items
            if item.field == case["input"]["field"]
        }
        self.assertIn(case["expected"]["status"], statuses)
        self.assertNotIn(case["expected"]["must_not_have_status"], statuses)

    def test_invalid_followers_remains_invalid_and_never_becomes_zero(self) -> None:
        case = self.case("invalid_followers")
        record = self.records_for(case["id"])[0]
        field = case["input"]["field"]
        self.assertIsNone(getattr(record, field))
        self.assertEqual(
            record.invalid_fields[field],
            case["input"]["raw_value"],
        )
        self.assertNotEqual(
            getattr(record, field),
            case["expected"]["must_not_equal"],
        )

    def test_missing_email_stays_empty_and_is_not_promoted_to_priority(self) -> None:
        case = self.case("missing_email_otherwise_good")
        creators, _ = self.aggregate_case(case["id"])
        creator = creators[0]
        score_creator(
            creator,
            self.campaign_from_case(case),
            REFERENCE_TIME,
        )
        self.assertIn(
            creator.action_level,
            case["expected"]["action_level_one_of"],
        )
        self.assertIsNone(creator.selected.get("email"))

    def test_market_mismatch_is_excluded(self) -> None:
        case = self.case("market_mismatch")
        creators, _ = self.aggregate_case(case["id"])
        creator = creators[0]
        score_creator(
            creator,
            self.campaign_from_case(case),
            REFERENCE_TIME,
        )
        self.assertEqual(
            creator.action_level,
            case["expected"]["action_level"],
        )
        self.assertIn(
            case["expected"]["exclusion_reason"],
            creator.exclusion_reasons,
        )

    def test_same_input_produces_identical_ranking_and_results(self) -> None:
        first = self.decision_snapshot()
        second = self.decision_snapshot()
        self.assertEqual(first, second)
        self.assertGreater(len(json.loads(first)), 0)

    def test_model_disabled_core_still_outputs_audit_and_shortlist(self) -> None:
        case = self.case("model_disabled_core_outputs")
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run_pipeline(
                input_paths=[
                    FIXTURES / name
                    for name in case["input"]["files"]
                ],
                brief_path=FIXTURES / case["input"]["campaign"],
                output_base=Path(temporary_directory) / "runs",
            )
            produced = {path.name for path in result.output_files}
            self.assertTrue(
                set(case["expected"]["required_outputs"]).issubset(produced)
            )


if __name__ == "__main__":
    unittest.main()
