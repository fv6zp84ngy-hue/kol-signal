from __future__ import annotations

import json
import tempfile
import tomllib
import unittest
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from kol_signal import __version__
from kol_signal.core import (
    aggregate_group,
    identity_resolution,
    load_records,
    parse_campaign_result,
    prepare_input_mappings,
    score_creator,
)
from tools.build_release import expected_tag_for_version


ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = ROOT / "examples" / "open_alpha_case"


class OpenAlphaVersionContractTests(unittest.TestCase):
    def test_package_release_and_tag_versions_are_aligned(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(__version__, "0.5.0a1")
        self.assertEqual(project["project"]["version"], __version__)
        self.assertEqual(expected_tag_for_version(__version__), "v0.5.0-alpha.1")
        self.assertIn("Open Alpha", project["project"]["description"])

    def test_readme_first_screen_is_open_alpha_without_mature_claims(self) -> None:
        first_screen = (ROOT / "README.md").read_text(encoding="utf-8")[:5000]
        self.assertIn("Open Alpha", first_screen)
        self.assertNotIn("Open Alpha Candidate", first_screen)
        for forbidden in (
            "Production Ready",
            "Public Beta",
            "已提高回复率",
            "已验证所有平台",
            "AI 自动找到最佳达人",
        ):
            self.assertNotIn(forbidden, first_screen)


class OpenAlphaSyntheticCaseGoldenTests(unittest.TestCase):
    def test_case_is_fully_synthetic_and_has_frozen_metrics(self) -> None:
        expected = json.loads(
            (CASE_ROOT / "expected_metrics.json").read_text(encoding="utf-8")
        )
        self.assertEqual(expected["data_classification"], "fully_synthetic")
        self.assertFalse(expected["business_effect_inference_allowed"])

        input_paths = [
            CASE_ROOT / "waveinflu_case.csv",
            CASE_ROOT / "nox_case.csv",
        ]
        plans = prepare_input_mappings(input_paths)
        records, _ = load_records(input_paths, mapping_plans=plans)
        groups, review_items = identity_resolution(records)
        reference_time = datetime(2026, 7, 31, tzinfo=timezone.utc)
        creators = [aggregate_group(group, reference_time) for group in groups]
        campaign = parse_campaign_result(
            CASE_ROOT / "campaign.txt"
        ).parsed_campaign
        for creator in creators:
            score_creator(creator, campaign, reference_time)

        actual = {
            "raw_records": len(records),
            "canonical_creators": len(creators),
            "duplicate_groups": sum(
                len(creator.records) > 1 for creator in creators
            ),
            "review_candidates": len(review_items),
            "high_conflict_fields": sum(
                conflict.level == "High"
                for creator in creators
                for conflict in creator.conflicts
            ),
            "stale_critical_fields": sum(
                len(creator.stale_items) for creator in creators
            ),
            "action_levels": dict(
                sorted(Counter(creator.action_level for creator in creators).items())
            ),
        }
        self.assertEqual(actual, expected["metrics"])

    def test_case_copy_discloses_limits_and_workflow_only_purpose(self) -> None:
        case_study = (CASE_ROOT / "CASE_STUDY.md").read_text(encoding="utf-8")
        for phrase in (
            "完全合成",
            "不能推断实际业务收益",
            "只展示工作流和输出",
            "原始记录：280",
            "规范化记录：214",
            "重复候选：46",
            "高冲突字段：18",
            "过期关键字段：35",
            "Priority：20",
            "Verify：27",
        ):
            self.assertIn(phrase, case_study)


class OpenAlphaReleaseAssetContractTests(unittest.TestCase):
    def test_release_notes_cover_required_open_alpha_sections(self) -> None:
        notes = (
            ROOT / "docs" / "releases" / "v0.5.0-alpha.1.md"
        ).read_text(encoding="utf-8")
        for heading in (
            "本版能做什么",
            "明确不能做什么",
            "Adapter 验证等级",
            "已知限制",
            "数据隐私",
            "安装",
            "Demo",
            "提交反馈",
        ):
            self.assertIn(heading, notes)
        self.assertIn("Open Alpha", notes)
        self.assertIn("Not Tested", notes)
        self.assertIn("完全合成", notes)

    def test_known_limitations_and_feedback_assets_exist(self) -> None:
        limitations = (ROOT / "docs" / "KNOWN_LIMITATIONS.md").read_text(
            encoding="utf-8"
        )
        feedback = (ROOT / "docs" / "OPEN_ALPHA_FEEDBACK.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "不承诺提高回复率",
            "Not Tested",
            "不自动发送邮件",
            "不调用 Live API",
        ):
            self.assertIn(phrase, limitations)
        for route in (
            "bug_report.yml",
            "adapter_format_request.yml",
            "feature_request.yml",
            "SECURITY.md",
        ):
            self.assertIn(route, feedback)

    def test_launch_copy_contains_primary_secondary_cta_and_no_effect_claim(self) -> None:
        launch = (ROOT / "docs" / "OPEN_ALPHA_LAUNCH_COPY.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "上传两份你从不同找人工具导出的名单",
            launch,
        )
        self.assertIn(
            "只提交表头和三行脱敏示例",
            launch,
        )
        self.assertIn("不能推断实际业务收益", launch)
        self.assertIn("完全合成", launch)

    def test_release_checklist_does_not_overclaim_external_validation(self) -> None:
        checklist = (ROOT / "docs" / "OPEN_ALPHA_RELEASE_CHECKLIST.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("external_install_smoke_test: pending", checklist)
        self.assertIn("github_remote: missing", checklist)
        self.assertIn("release_status: blocked", checklist)


if __name__ == "__main__":
    unittest.main()
