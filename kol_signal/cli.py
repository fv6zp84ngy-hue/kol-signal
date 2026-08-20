from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import (
    CampaignParseResult,
    OutputError,
    PipelineError,
    load_campaign_config,
    parse_campaign_result,
    prepare_input_mappings,
    read_tabular,
    review_run,
    run_pipeline,
    validate_campaign_for_run,
    write_campaign_config,
)
from .feedback import format_metric_value, import_feedback
from .mapping import create_mapping_plan, mapping_preview_rows
from .demo import run_demo
from .diagnostics import (
    DiagnosticsError,
    create_diagnostics,
    diagnostic_file_list,
)
from .doctor import doctor_report


def add_mapping_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--mapping",
        action="append",
        default=[],
        type=Path,
        help="Confirmed mapping JSON. Repeat for multiple input schemas.",
    )
    parser.add_argument(
        "--mapping-dir",
        type=Path,
        default=Path(".kol-signal/mappings"),
        help="Directory for reusable mappings. Default: .kol-signal/mappings",
    )
    parser.add_argument(
        "--sheet",
        action="append",
        default=[],
        metavar="INPUT=WORKSHEET",
        help=(
            "Select one worksheet for an XLSX input. "
            "Repeat as --sheet 'file.xlsx=Creators'."
        ),
    )


def parse_sheet_selections(
    values: list[str],
    input_paths: list[Path],
) -> dict[Path, str]:
    inputs_by_resolved = {path.resolve(): path for path in input_paths}
    selections: dict[Path, str] = {}
    for value in values:
        input_value, separator, worksheet = value.partition("=")
        if not separator or not input_value.strip() or not worksheet.strip():
            raise PipelineError(
                f"Invalid --sheet value '{value}'. "
                "Use --sheet 'file.xlsx=Worksheet Name'."
            )
        resolved = Path(input_value.strip()).resolve()
        input_path = inputs_by_resolved.get(resolved)
        if input_path is None:
            raise PipelineError(
                f"--sheet references a file that is not listed with --input: "
                f"{input_value.strip()}"
            )
        if input_path.suffix.lower() != ".xlsx":
            raise PipelineError(f"--sheet can only select XLSX input: {input_path}")
        if input_path in selections:
            raise PipelineError(f"Duplicate --sheet selection for {input_path}")
        selections[input_path] = worksheet.strip()
    return selections


def print_mapping_preview(plan) -> None:
    print(
        f"\nMapping Preview: {plan.input_path}\n"
        f"Source: {plan.source} | Origin: {plan.origin} | "
        f"Validation: {plan.adapter_validation_level or 'Generic Import'} | "
        f"Worksheet: {plan.sheet_name or 'only non-empty worksheet'} | "
        f"Fingerprint: {plan.fingerprint}"
    )
    print(f"{'Source column':<30} {'Target field':<28} {'Conf.':>6}  Status")
    print("-" * 78)
    for item in plan.suggestions:
        print(
            f"{item.source_column[:30]:<30} "
            f"{(item.target_field or '—')[:28]:<28} "
            f"{item.confidence:>6.2f}  {item.status}"
        )


def print_campaign_preview(result: CampaignParseResult) -> None:
    campaign = result.parsed_campaign
    print(f"\nCampaign Preview | Parser: {result.parser_version}")
    print("Recognized:")
    if result.recognized_conditions:
        for item in result.recognized_conditions:
            applied = "applied" if item.get("applied") else "not applied"
            print(f"  - {item['field']}: {item['value']} ({applied})")
    else:
        print("  - None")
    print("Unrecognized:")
    if result.unrecognized_conditions:
        for item in result.unrecognized_conditions:
            print(f"  - [{item['severity']}] {item['text']}")
    else:
        print("  - None")
    print("Conflicts:")
    if result.conflicting_conditions:
        for item in result.conflicting_conditions:
            print(f"  - {item['field']}: {item['reason']}")
    else:
        print("  - None")
    print("Warnings:")
    if result.warnings:
        for warning in result.warnings:
            print(f"  - {warning}")
    else:
        print("  - None")
    print(
        "Final config: "
        f"markets={list(campaign.markets)}, "
        f"languages={list(campaign.languages)}, "
        f"platforms={list(campaign.platforms)}, "
        f"followers={campaign.follower_min}-{campaign.follower_max}, "
        f"latest_post_days={campaign.latest_post_max_age_days}, "
        f"require_contact={campaign.require_contact_path}, "
        f"blocklist={list(campaign.blocklist)}, "
        f"topics={list(campaign.topics)}"
    )


def print_cli_error(label: str, exc: BaseException, fallback_code: str) -> None:
    code = getattr(exc, "code", fallback_code)
    print(f"{label} [{code}]: {exc}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kol-signal",
        description="Audit multiple creator lists and produce an explainable outreach shortlist.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_parser = subparsers.add_parser(
        "demo",
        help="Run the complete pipeline with package-contained fully synthetic data.",
    )
    demo_parser.add_argument(
        "--output",
        type=Path,
        default=Path("kol-signal-demo"),
        help="Base output directory. Default: ./kol-signal-demo",
    )
    demo_parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Top candidates shown in the synthetic report.",
    )
    demo_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="CLI result format.",
    )

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check the local CLI environment without reading creator data.",
    )
    doctor_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Doctor output format.",
    )

    diagnostics_parser = subparsers.add_parser(
        "diagnostics",
        help="Create an allowlisted, redacted diagnostics ZIP for an existing Run.",
    )
    diagnostics_parser.add_argument("--run", required=True, help="Existing Run ID.")
    diagnostics_parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("runs"),
        help="Run directory root. Default: ./runs",
    )
    diagnostics_parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="New diagnostics ZIP path. Existing files are never overwritten.",
    )

    run_parser = subparsers.add_parser("run", help="Run the local audit and shortlist pipeline.")
    run_parser.add_argument(
        "--input",
        action="append",
        required=True,
        type=Path,
        help="CSV or XLSX creator list. Repeat for multiple sources.",
    )
    run_parser.add_argument("--brief", required=True, type=Path, help="Campaign brief text file.")
    run_parser.add_argument(
        "--campaign-config",
        type=Path,
        help="Confirmed Campaign JSON generated by campaign-preview.",
    )
    run_parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs"),
        help="Base output directory. Default: ./runs",
    )
    run_parser.add_argument("--top", type=int, default=20, help="Top candidates shown in report.md.")
    run_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="CLI result format.",
    )
    run_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Fail instead of prompting when a mapping is ambiguous.",
    )
    add_mapping_arguments(run_parser)

    campaign_parser = subparsers.add_parser(
        "campaign-preview",
        help="Preview recognized, unrecognized, and conflicting Campaign conditions.",
    )
    campaign_parser.add_argument(
        "--brief",
        required=True,
        type=Path,
        help="Campaign brief text file.",
    )
    campaign_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Preview output format.",
    )
    campaign_parser.add_argument(
        "--output",
        type=Path,
        help="Optional Campaign JSON output path.",
    )
    campaign_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Mark the written Campaign config as explicitly reviewed.",
    )

    preview_parser = subparsers.add_parser(
        "mapping-preview",
        help="Preview native, reused, or suggested mappings without importing data.",
    )
    preview_parser.add_argument(
        "--input",
        action="append",
        required=True,
        type=Path,
        help="CSV or XLSX creator list. Repeat for multiple sources.",
    )
    preview_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Preview output format.",
    )
    add_mapping_arguments(preview_parser)

    review_parser = subparsers.add_parser(
        "review",
        help="Apply merge review decisions and regenerate the selected Run.",
    )
    review_parser.add_argument("--run", required=True, help="Existing Run ID.")
    review_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Completed merge_review.xlsx.",
    )
    review_parser.add_argument(
        "--sheet",
        help="Worksheet name when the review workbook has multiple non-empty sheets.",
    )
    review_parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("runs"),
        help="Run directory root. Default: ./runs",
    )
    review_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="CLI result format.",
    )

    feedback_parser = subparsers.add_parser(
        "feedback",
        help="Import a feedback template and produce descriptive outcome metrics.",
    )
    feedback_parser.add_argument("--run", required=True, help="Existing Run ID.")
    feedback_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Completed feedback_template.xlsx.",
    )
    feedback_parser.add_argument(
        "--sheet",
        help="Worksheet name when the feedback workbook has multiple non-empty sheets.",
    )
    feedback_parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("runs"),
        help="Run directory root. Default: ./runs",
    )
    feedback_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="CLI result format.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        payload = doctor_report()
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Status: {payload['status']}")
            print(
                "Python: "
                f"{payload['python']['version']} "
                f"({'supported' if payload['python']['supported'] else 'unsupported'})"
            )
            print(f"Package: kol-signal {payload['package']['version']}")
            dependency = payload["dependencies"]["openpyxl"]
            print(
                "OpenPyXL: "
                f"{dependency['version'] if dependency['installed'] else 'missing'}"
            )
            print(
                "Working directory writable: "
                f"{'yes' if payload['working_directory']['writable'] else 'no'}"
            )
            print(
                "Codex Skill installed: "
                f"{'yes' if payload['skill']['installed'] else 'no (optional)'}"
            )
            print("Privacy: no creator files read; no network access; no paths disclosed.")
        return 0 if payload["status"] == "ok" else 2

    if args.command == "diagnostics":
        print("Diagnostics preview — files to be created:")
        for name in diagnostic_file_list():
            print(f"  - {name}")
        print(
            "Excluded: raw cell values, Email, Handle, Profile URL, Campaign text, "
            "Token, and absolute paths."
        )
        try:
            payload = create_diagnostics(
                run_id=args.run,
                runs_dir=args.runs_dir,
                output=args.output,
            )
        except DiagnosticsError as exc:
            print_cli_error("error", exc, "KS_DIAGNOSTICS_001")
            return 2
        except OutputError as exc:
            print_cli_error("output error", exc, "KS_OUTPUT_001")
            return 5
        print(f"Diagnostics created: {args.output.name}")
        print("No original creator values or Campaign text were included.")
        return 0

    if args.command == "demo":
        if args.top < 1:
            parser.error("--top must be at least 1")
        try:
            result = run_demo(args.output, top=args.top)
        except OutputError as exc:
            print_cli_error("output error", exc, "KS_OUTPUT_001")
            return 5
        except PipelineError as exc:
            print_cli_error("error", exc, "KS_PIPELINE_001")
            return 2
        except OSError as exc:
            print_cli_error("output error", exc, "KS_OUTPUT_001")
            return 5
        payload = {
            "demo": True,
            "data_classification": "fully_synthetic",
            "run_id": result.run_id,
            "run_dir": str(result.run_dir),
            "raw_records": result.raw_record_count,
            "canonical_creators": result.creator_count,
            "review_items": result.review_count,
            "outputs": [str(path) for path in result.run_dir.iterdir()],
        }
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("Fully Synthetic Demo complete.")
            print(f"Raw records: {result.raw_record_count}")
            print(f"Canonical creators: {result.creator_count}")
            print(f"Review items: {result.review_count}")
            print(f"Output: {result.run_dir}")
            for output_path in sorted(result.run_dir.iterdir()):
                print(f"  - {output_path.name}")
        return 0

    if args.command == "campaign-preview":
        try:
            if args.confirm and args.output is None:
                raise PipelineError("--confirm requires --output.")
            result = parse_campaign_result(args.brief)
            if args.output:
                write_campaign_config(
                    args.output,
                    brief_path=args.brief,
                    result=result,
                    confirmed=args.confirm,
                    confirmation_source=(
                        "campaign-preview-confirmed"
                        if args.confirm
                        else "campaign-preview"
                    ),
                )
        except OutputError as exc:
            print_cli_error("output error", exc, "KS_OUTPUT_001")
            return 5
        except PipelineError as exc:
            print_cli_error("error", exc, "KS_PIPELINE_001")
            return 2
        payload = {
            **result.to_dict(),
            "confirmed": args.confirm,
            "output": str(args.output) if args.output else None,
        }
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print_campaign_preview(result)
            if args.output:
                print(f"Campaign config: {args.output}")
        return 0

    if args.command == "mapping-preview":
        plans = []
        try:
            sheet_names = parse_sheet_selections(args.sheet, args.input)
            for input_path in args.input:
                sheet_name = sheet_names.get(input_path)
                headers, rows = read_tabular(input_path, sheet_name=sheet_name)
                plans.append(
                    create_mapping_plan(
                        input_path,
                        headers,
                        rows,
                        sheet_name=sheet_name,
                        mapping_dir=args.mapping_dir,
                        explicit_configs=args.mapping,
                    )
                )
        except (PipelineError, ValueError, json.JSONDecodeError) as exc:
            print_cli_error("error", exc, "KS_PIPELINE_001")
            return 2
        if args.format == "json":
            print(
                json.dumps(
                    [
                        {
                            "input": str(plan.input_path),
                            "source": plan.source,
                            "origin": plan.origin,
                            "adapter_validation_level": (
                                plan.adapter_validation_level or "Generic Import"
                            ),
                            "worksheet": plan.sheet_name,
                            "fingerprint": plan.fingerprint,
                            "requires_confirmation": bool(plan.ambiguous),
                            "columns": mapping_preview_rows(plan),
                        }
                        for plan in plans
                    ],
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            for plan in plans:
                print_mapping_preview(plan)
                if plan.ambiguous:
                    columns = ", ".join(item.source_column for item in plan.ambiguous)
                    print(f"Requires confirmation: {columns}")
        return 0

    if args.command == "review":
        try:
            result = review_run(
                run_id=args.run,
                review_input=args.input,
                runs_dir=args.runs_dir,
                review_sheet_name=args.sheet,
            )
        except (PipelineError, json.JSONDecodeError) as exc:
            print_cli_error("error", exc, "KS_PIPELINE_001")
            return 2
        except OSError as exc:
            print_cli_error("output error", exc, "KS_OUTPUT_001")
            return 5
        payload = {
            "run_id": result.run_id,
            "run_dir": str(result.run_dir),
            "raw_records": result.raw_record_count,
            "canonical_creators": result.creator_count,
            "pending_review_items": result.review_count,
            "outputs": [str(path) for path in result.output_files],
        }
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Review applied: {result.run_id}")
            print(f"Canonical creators: {result.creator_count}")
            print(f"Pending review items: {result.review_count}")
            print(f"Output: {result.run_dir}")
        return 0

    if args.command == "feedback":
        try:
            result = import_feedback(
                run_id=args.run,
                feedback_input=args.input,
                runs_dir=args.runs_dir,
                feedback_sheet_name=args.sheet,
            )
        except (PipelineError, json.JSONDecodeError) as exc:
            print_cli_error("error", exc, "KS_PIPELINE_001")
            return 2
        except OSError as exc:
            print_cli_error("output error", exc, "KS_OUTPUT_001")
            return 5
        payload = {
            "run_id": result.run_id,
            "run_dir": str(result.run_dir),
            "feedback_rows": result.feedback_count,
            "notes": result.note_count,
            "warnings": result.warning_count,
            "metrics": {
                metric["key"]: metric["value"] for metric in result.metrics
            },
            "outputs": [str(path) for path in result.output_files],
        }
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Feedback imported: {result.run_id}")
            for metric in result.metrics:
                print(f"{metric['label']}: {format_metric_value(metric)}")
            print(f"Text feedback notes: {result.note_count}")
            print(f"Validation warnings: {result.warning_count}")
            print(f"Output: {result.run_dir}")
        return 0

    if args.top < 1:
        parser.error("--top must be at least 1")

    try:
        campaign_confirmed = False
        confirmation_source = "auto-validated"
        if args.campaign_config:
            campaign_result = load_campaign_config(
                args.campaign_config,
                brief_path=args.brief,
            )
            campaign_confirmed = True
            confirmation_source = "confirmed-config"
            if args.format == "text":
                print_campaign_preview(campaign_result)
        else:
            campaign_result = parse_campaign_result(args.brief)
            campaign_is_interactive = (
                not args.non_interactive
                and args.format == "text"
                and sys.stdin.isatty()
            )
            if campaign_is_interactive:
                print_campaign_preview(campaign_result)
                validate_campaign_for_run(campaign_result, confirmed=True)
                answer = input("Use this Campaign configuration? [y/N]: ").strip().lower()
                if answer not in {"y", "yes"}:
                    raise PipelineError("Campaign configuration was not confirmed.")
                campaign_confirmed = True
                confirmation_source = "interactive-confirmed"
            else:
                validate_campaign_for_run(campaign_result, confirmed=False)

        sheet_names = parse_sheet_selections(args.sheet, args.input)
        text_preview = print_mapping_preview if args.format == "text" else None
        mapping_plans = prepare_input_mappings(
            args.input,
            sheet_names=sheet_names,
            mapping_dir=args.mapping_dir,
            explicit_configs=args.mapping,
            interactive=(
                not args.non_interactive
                and args.format == "text"
                and sys.stdin.isatty()
            ),
            preview_fn=text_preview,
        )
        result = run_pipeline(
            input_paths=args.input,
            brief_path=args.brief,
            output_base=args.output,
            top=args.top,
            mapping_plans=mapping_plans,
            campaign_result=campaign_result,
            campaign_confirmed=campaign_confirmed,
            campaign_confirmation_source=confirmation_source,
        )
    except OutputError as exc:
        print_cli_error("output error", exc, "KS_OUTPUT_001")
        return 5
    except PipelineError as exc:
        print_cli_error("error", exc, "KS_PIPELINE_001")
        return 2
    except OSError as exc:
        print_cli_error("output error", exc, "KS_OUTPUT_001")
        return 5

    payload = {
        "run_id": result.run_id,
        "run_dir": str(result.run_dir),
        "campaign": campaign_result.to_dict(),
        "raw_records": result.raw_record_count,
        "canonical_creators": result.creator_count,
        "review_items": result.review_count,
        "outputs": [str(path) for path in result.output_files],
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Run complete: {result.run_id}")
        print(f"Raw records: {result.raw_record_count}")
        print(f"Canonical creators: {result.creator_count}")
        print(f"Review items: {result.review_count}")
        print(f"Output: {result.run_dir}")
        for output_path in result.output_files:
            print(f"  - {output_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
