from __future__ import annotations

import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from kol_signal.cli import main


ROOT = Path(__file__).resolve().parents[1]


class DiagnosticsGoldenTests(unittest.TestCase):
    def _create_demo_run(self, root: Path) -> tuple[Path, str]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                ["demo", "--output", str(root), "--format", "json"]
            )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        return Path(payload["run_dir"]), payload["run_id"]

    def test_diagnostics_zip_is_allowlisted_and_removes_pii(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run_dir, run_id = self._create_demo_run(root / "runs")
            manifest_path = run_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["secret_probe"] = "api_token=super-secret-value"
            manifest["campaign_parse"]["private_note"] = (
                "Contact alice@example.com and @private_handle "
                "at https://social.example/private."
            )
            manifest["mapping_plans"][0]["input_path"] = (
                "/Users/private-team/creator-list.xlsx"
            )
            manifest["mapping_plans"][0]["sheet_name"] = "alice@example.com"
            manifest["mapping_plans"][0]["mapping"][
                "@private_handle"
            ] = "display_name"
            manifest["mapping_plans"][0]["input_columns"].extend(
                ["@private_handle", "alice@example.com"]
            )
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            output = root / "diagnostics.zip"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "diagnostics",
                        "--run",
                        run_id,
                        "--runs-dir",
                        str(root / "runs"),
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.is_file())
            cli_output = stdout.getvalue()
            self.assertLess(
                cli_output.index("environment.json"),
                cli_output.index("Diagnostics created"),
            )
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {
                        "environment.json",
                        "input_schemas.json",
                        "redacted_manifest.json",
                        "failure_context.json",
                    },
                )
                combined = "\n".join(
                    archive.read(name).decode("utf-8")
                    for name in archive.namelist()
                )
                input_schemas = json.loads(
                    archive.read("input_schemas.json").decode("utf-8")
                )

            self.assertIn("Notes", input_schemas[0]["columns"])
            for forbidden in (
                "alice@example.com",
                "@private_handle",
                "https://social.example/private",
                "super-secret-value",
                "/Users/private-team",
                str(root),
                "alpha@creators.example.com",
                "demo_pet_alpha",
            ):
                self.assertNotIn(forbidden, combined)
            self.assertNotIn("campaign_parse", combined)
            self.assertNotIn("input_files", combined)

    def test_diagnostics_missing_run_has_stable_code_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        "diagnostics",
                        "--run",
                        "run_missing",
                        "--runs-dir",
                        temporary_directory,
                        "--output",
                        str(Path(temporary_directory) / "diagnostics.zip"),
                    ]
                )
        self.assertEqual(exit_code, 2)
        self.assertIn("KS_DIAGNOSTICS_001", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_diagnostics_never_overwrites_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _, run_id = self._create_demo_run(root / "runs")
            output = root / "diagnostics.zip"
            output.write_bytes(b"keep-original")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        "diagnostics",
                        "--run",
                        run_id,
                        "--runs-dir",
                        str(root / "runs"),
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(exit_code, 5)
            self.assertEqual(output.read_bytes(), b"keep-original")
            self.assertIn("KS_OUTPUT_001", stderr.getvalue())


class OpenSourceOperationsContractTests(unittest.TestCase):
    def test_ci_has_frozen_minimum_matrix_and_release_smoke_steps(self) -> None:
        test_workflow = (
            ROOT / ".github" / "workflows" / "test.yml"
        ).read_text(encoding="utf-8")
        build_workflow = (
            ROOT / ".github" / "workflows" / "build.yml"
        ).read_text(encoding="utf-8")
        for token in ("ubuntu-latest", "windows-latest", "3.11", "3.12"):
            self.assertIn(token, test_workflow)
        for command in (
            "pip check",
            "unittest",
            "kol-signal --help",
            "pip wheel",
            "kol-signal demo",
        ):
            self.assertIn(command, test_workflow)
        self.assertIn("tools.build_release", build_workflow)
        combined = test_workflow + build_workflow
        self.assertNotIn("secrets.", combined)
        self.assertNotIn("GMAIL", combined.upper())
        self.assertNotIn("FEISHU", combined.upper())

    def test_issue_templates_cover_public_feedback_and_private_security(self) -> None:
        template_root = ROOT / ".github" / "ISSUE_TEMPLATE"
        expected = {
            "bug_report.yml",
            "adapter_format_request.yml",
            "feature_request.yml",
            "documentation_problem.yml",
            "security_issue.md",
            "config.yml",
        }
        self.assertTrue(expected.issubset({path.name for path in template_root.iterdir()}))
        adapter = (template_root / "adapter_format_request.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("column", adapter.lower())
        self.assertIn("diagnostics", adapter.lower())
        self.assertIn("Do not", adapter)
        security = (template_root / "security_issue.md").read_text(encoding="utf-8")
        self.assertIn("Security tab", security)
        self.assertIn("Do not", security)
        self.assertIn("public", security.lower())

    def test_error_catalog_documents_actual_diagnostic_command(self) -> None:
        error_root = ROOT / "docs" / "errors"
        index = (error_root / "README.md").read_text(encoding="utf-8")
        for code in (
            "KS_PIPELINE_001",
            "KS_OUTPUT_001",
            "KS_DIAGNOSTICS_001",
        ):
            self.assertIn(code, index)
            page = (error_root / f"{code}.md").read_text(encoding="utf-8")
            for heading in ("错误原因", "数据风险", "下一步", "脱敏信息"):
                self.assertIn(heading, page)
        diagnostic_page = (
            error_root / "KS_DIAGNOSTICS_001.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "kol-signal diagnostics --run RUN_ID --output diagnostics.zip",
            diagnostic_page,
        )

    def test_readme_exposes_ci_and_private_security_routes(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(".github/workflows/test.yml", readme)
        self.assertIn("SECURITY.md", readme)


if __name__ == "__main__":
    unittest.main()
