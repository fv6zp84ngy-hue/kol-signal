from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.alpha_feedback import (
    FeedbackValidationError,
    append_feedback,
    evaluate_adapter_gate,
    priority_score,
    validate_feedback_record,
)


ROOT = Path(__file__).resolve().parents[1]


def safe_feedback() -> dict[str, object]:
    return {
        "feedback_id": "AF-20260801-001",
        "version": "0.5.0a1",
        "user_type": "brand_operator",
        "environment": "Windows 11; Python 3.12; pipx",
        "input_source": "Generic creator database CSV export",
        "record_count": 240,
        "issue_stage": "mapping",
        "severity": "Major",
        "reproducible": True,
        "workaround": "Confirmed ambiguous columns manually.",
        "resolution": {
            "status": "triaged",
            "owner": "maintainer",
            "summary": "Create a structure-faithful synthetic reproduction first.",
        },
        "triage": {
            "user_value": 5,
            "frequency": 2,
            "blocking": False,
            "implementation_cost": 2,
        },
    }


class AlphaFeedbackLogGoldenTests(unittest.TestCase):
    def test_safe_record_is_normalized_and_priority_is_computed(self) -> None:
        record = validate_feedback_record(safe_feedback())
        self.assertEqual(record["feedback_id"], "AF-20260801-001")
        self.assertEqual(record["triage"]["priority_score"], 5.0)
        self.assertEqual(priority_score(5, 2, False, 2), 5.0)
        self.assertEqual(priority_score(5, 2, True, 2), 10.0)

    def test_blocker_requires_explicit_owner_and_status(self) -> None:
        record = safe_feedback()
        record["severity"] = "Blocker"
        record["resolution"] = {
            "status": "new",
            "owner": "",
            "summary": "",
        }
        with self.assertRaisesRegex(FeedbackValidationError, "Blocker.*owner"):
            validate_feedback_record(record)

    def test_pii_and_unapproved_fields_are_rejected(self) -> None:
        probes = (
            "Contact person@example.net",
            "Creator @private_handle",
            "Profile https://social.invalid/creator",
            "token=super-secret-value",
            "/Users/private-team/source.xlsx",
        )
        for probe in probes:
            record = safe_feedback()
            record["workaround"] = probe
            with self.subTest(probe=probe), self.assertRaises(
                FeedbackValidationError
            ):
                validate_feedback_record(record)

        record = safe_feedback()
        record["raw_rows"] = ["must never be accepted"]
        with self.assertRaisesRegex(FeedbackValidationError, "unexpected fields"):
            validate_feedback_record(record)

    def test_append_is_atomic_and_duplicate_ids_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "feedback.json"
            appended = append_feedback(path, safe_feedback())
            self.assertEqual(appended["record_count"], 1)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(len(payload["records"]), 1)
            with self.assertRaisesRegex(FeedbackValidationError, "Duplicate"):
                append_feedback(path, safe_feedback())


class AdapterUpgradeGateGoldenTests(unittest.TestCase):
    def test_adapter_gate_requires_evidence_generic_failure_demand_and_cost(self) -> None:
        first = {
            "request_id": "AR-001",
            "requester_key": "alpha-user-001",
            "source_name": "Synthetic Source A",
            "generic_mapping_result": "blocked",
            "source_request_share": 0.2,
            "maintenance_cost_acceptable": True,
            "evidence": [
                {
                    "schema_hash": "schema-a",
                    "legal_and_redacted": True,
                },
                {
                    "schema_hash": "schema-b",
                    "legal_and_redacted": True,
                },
            ],
        }
        blocked = evaluate_adapter_gate([first])
        self.assertFalse(blocked["eligible"])
        self.assertIn("demand_threshold", blocked["missing"])

        second = {
            **first,
            "request_id": "AR-002",
            "requester_key": "alpha-user-002",
            "evidence": [],
        }
        eligible = evaluate_adapter_gate([first, second])
        self.assertTrue(eligible["eligible"])
        self.assertEqual(eligible["unique_user_count"], 2)
        self.assertEqual(eligible["legal_schema_count"], 2)

        registered = evaluate_adapter_gate(
            {"schema_version": 1, "requests": [first, second]}
        )
        self.assertTrue(registered["eligible"])


class AlphaOperationsDocumentationTests(unittest.TestCase):
    def test_public_log_and_queues_are_empty_not_fabricated(self) -> None:
        log = json.loads(
            (ROOT / "docs" / "alpha" / "alpha_feedback_log.json").read_text(
                encoding="utf-8"
            )
        )
        requests = json.loads(
            (ROOT / "docs" / "alpha" / "adapter_requests.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(log["records"], [])
        self.assertEqual(requests["requests"], [])
        self.assertIn(
            "尚未收到真实 Open Alpha 反馈",
            (ROOT / "docs" / "alpha" / "ALPHA_FEEDBACK_LOG.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_triage_docs_freeze_priority_and_scope_boundaries(self) -> None:
        triage = (ROOT / "docs" / "alpha" / "TRIAGE_POLICY.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "用户价值 × 出现频率 × 阻塞系数 ÷ 实现与维护成本",
            "先增加复现 Fixture 和测试",
            "不根据单个用户反馈修改全局评分权重",
            "Blocker",
            "Major",
            "Minor",
        ):
            self.assertIn(phrase, triage)

        intake = (ROOT / "docs" / "alpha" / "PRIVATE_FORMAT_INTAKE.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("真实格式不会直接进入公开仓库", intake)
        self.assertIn("结构保真的合成 Fixture", intake)

    def test_issue_templates_capture_a6_classification_fields(self) -> None:
        bug = (
            ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml"
        ).read_text(encoding="utf-8")
        adapter = (
            ROOT / ".github" / "ISSUE_TEMPLATE" / "adapter_format_request.yml"
        ).read_text(encoding="utf-8")
        for field_id in (
            "user_type",
            "input_source",
            "record_count",
            "issue_stage",
            "severity",
            "reproducible",
            "workaround",
        ):
            self.assertIn(f"id: {field_id}", bug)
        for field_id in (
            "requester_key",
            "evidence_count",
            "generic_result",
            "maintenance",
        ):
            self.assertIn(f"id: {field_id}", adapter)

    def test_changelog_and_blocker_board_do_not_invent_patch_releases(self) -> None:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        blockers = (
            ROOT / "docs" / "alpha" / "RELEASE_BLOCKERS.md"
        ).read_text(encoding="utf-8")
        board = (ROOT / "docs" / "alpha" / "ISSUE_BOARD.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("[Unreleased]", changelog)
        self.assertIn("No Alpha Patch has been published", changelog)
        self.assertNotIn("## [0.5.1-alpha.1]", changelog)
        self.assertIn("Owner", blockers)
        self.assertIn("Status", blockers)
        self.assertIn("真实用户 Blocker：0", blockers)
        self.assertIn("尚无真实反馈 Issue", board)


if __name__ == "__main__":
    unittest.main()
