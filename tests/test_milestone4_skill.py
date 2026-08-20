from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "creator-signal-intelligence"


class SkillPackageTests(unittest.TestCase):
    def test_skill_package_has_required_files(self) -> None:
        self.assertTrue((SKILL_ROOT / "SKILL.md").is_file())
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").is_file())
        self.assertTrue((SKILL_ROOT / "references" / "cli-workflow.md").is_file())

    def test_skill_is_a_thin_cli_wrapper(self) -> None:
        content = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: creator-signal-intelligence", content)
        self.assertIn("Use the existing `kol-signal` CLI as the source of truth.", content)
        self.assertIn("references/cli-workflow.md", content)
        self.assertIn("Do not reproduce or override", content)
        self.assertNotIn("0.35 × Brand Fit", content)
        self.assertNotIn("followers = 30", content)

    def test_ui_metadata_mentions_explicit_skill_invocation(self) -> None:
        content = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "Creator Signal Intelligence"', content)
        self.assertIn("$creator-signal-intelligence", content)

    def test_cli_reference_covers_frozen_p0_commands(self) -> None:
        content = (SKILL_ROOT / "references" / "cli-workflow.md").read_text(
            encoding="utf-8"
        )
        for command in (
            "kol-signal campaign-preview",
            "kol-signal mapping-preview",
            "kol-signal run",
            "kol-signal review",
            "kol-signal feedback",
        ):
            self.assertIn(command, content)
        for backlog_item in ("Gmail", "competitor analysis", "automatic weight"):
            self.assertNotIn(backlog_item, content)


if __name__ == "__main__":
    unittest.main()
