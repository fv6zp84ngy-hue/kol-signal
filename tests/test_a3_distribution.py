from __future__ import annotations

import io
import json
import tempfile
import tomllib
import unittest
from contextlib import redirect_stdout
from importlib import resources
from pathlib import Path

from kol_signal import __version__
from kol_signal.cli import main


ROOT = Path(__file__).resolve().parents[1]


class DemoDistributionGoldenTests(unittest.TestCase):
    def test_demo_package_data_is_self_contained_and_fully_synthetic(self) -> None:
        demo_root = resources.files("kol_signal.demo_data")
        names = {item.name for item in demo_root.iterdir()}
        self.assertTrue(
            {"waveinflu_demo.csv", "nox_demo.csv", "campaign.txt"}.issubset(names)
        )
        for name in ("waveinflu_demo.csv", "nox_demo.csv"):
            content = demo_root.joinpath(name).read_text(encoding="utf-8")
            self.assertIn("example.com", content)
            self.assertIn("Fully Synthetic Demo", content)

    def test_demo_outputs_complete_marked_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "demo",
                        "--output",
                        temporary_directory,
                        "--format",
                        "json",
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            run_dir = Path(payload["run_dir"])
            expected = {
                "data_audit.xlsx",
                "creator_shortlist.xlsx",
                "merge_review.xlsx",
                "feedback_template.xlsx",
                "report.md",
                "campaign.json",
                "manifest.json",
            }
            self.assertTrue(expected.issubset({path.name for path in run_dir.iterdir()}))
            report = (run_dir / "report.md").read_text(encoding="utf-8")
            self.assertTrue(report.startswith("# Fully Synthetic Demo"))
            manifest = json.loads(
                (run_dir / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["run_type"], "demo")
            self.assertEqual(manifest["data_classification"], "fully_synthetic")

    def test_demo_does_not_overwrite_an_existing_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            first = io.StringIO()
            second = io.StringIO()
            with redirect_stdout(first):
                self.assertEqual(
                    main(["demo", "--output", temporary_directory, "--format", "json"]),
                    0,
                )
            with redirect_stdout(second):
                self.assertEqual(
                    main(["demo", "--output", temporary_directory, "--format", "json"]),
                    0,
                )
            self.assertNotEqual(
                json.loads(first.getvalue())["run_dir"],
                json.loads(second.getvalue())["run_dir"],
            )


class VersionAndDoctorGoldenTests(unittest.TestCase):
    def test_package_and_project_versions_match(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(project["project"]["version"], __version__)
        self.assertEqual(__version__, "0.5.0a1")
        stdout = io.StringIO()
        with redirect_stdout(stdout), self.assertRaises(SystemExit) as raised:
            main(["--version"])
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(stdout.getvalue().strip(), "kol-signal 0.5.0a1")

    def test_doctor_is_privacy_safe_and_skill_is_optional(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["doctor", "--format", "json"])
        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        payload = json.loads(output)
        self.assertEqual(
            set(payload),
            {
                "status",
                "python",
                "package",
                "dependencies",
                "working_directory",
                "skill",
                "privacy",
            },
        )
        self.assertNotIn(str(Path.home()), output)
        self.assertNotIn("@", output)
        self.assertNotIn("creator_records", output)
        self.assertFalse(payload["skill"]["required"])
        self.assertEqual(payload["privacy"]["user_data_accessed"], False)


class SelfServiceDocumentationGoldenTests(unittest.TestCase):
    def test_readme_first_screen_contains_self_service_route(self) -> None:
        content = (ROOT / "README.md").read_text(encoding="utf-8")[:5000]
        for phrase in (
            "安装 CLI",
            "kol-signal demo",
            "分析自己的文件",
            "输出在哪里",
            "当前限制",
        ):
            self.assertIn(phrase, content)

    def test_install_and_skill_docs_cover_safe_uninstall_and_platforms(self) -> None:
        install = (ROOT / "docs" / "INSTALLATION.md").read_text(encoding="utf-8")
        skill = (ROOT / "docs" / "SKILL_INSTALLATION.md").read_text(encoding="utf-8")
        for platform in ("macOS", "Windows", "Linux"):
            self.assertIn(platform, install)
            self.assertIn(platform, skill)
        self.assertIn("不会删除", install)
        self.assertIn("历史 Run", install)
        self.assertIn("不覆盖", skill)
        self.assertIn("SKILL.md", skill)
        self.assertIn("重启 Codex", skill)
        self.assertIn("不会安装 Gmail", skill)
        self.assertIn("飞书", skill)


if __name__ == "__main__":
    unittest.main()
