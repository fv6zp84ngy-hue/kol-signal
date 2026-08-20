from __future__ import annotations

from contextlib import ExitStack
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path

from .core import PipelineResult, prepare_input_mappings, run_pipeline


DEMO_REFERENCE_TIME = datetime(2026, 7, 31, tzinfo=timezone.utc)
DEMO_RESOURCE_NAMES = (
    "waveinflu_demo.csv",
    "nox_demo.csv",
)


def run_demo(output_base: Path, *, top: int = 20) -> PipelineResult:
    """Run the offline pipeline against package-contained synthetic data."""

    demo_root = resources.files("kol_signal.demo_data")
    with ExitStack() as stack:
        input_paths = [
            stack.enter_context(resources.as_file(demo_root.joinpath(name)))
            for name in DEMO_RESOURCE_NAMES
        ]
        brief_path = stack.enter_context(
            resources.as_file(demo_root.joinpath("campaign.txt"))
        )
        mapping_plans = prepare_input_mappings(
            input_paths,
            mapping_dir=None,
            save_confirmed=False,
        )
        return run_pipeline(
            input_paths=input_paths,
            brief_path=brief_path,
            output_base=output_base,
            top=top,
            mapping_plans=mapping_plans,
            campaign_confirmation_source="packaged-fully-synthetic-demo",
            reference_time=DEMO_REFERENCE_TIME,
            run_type="demo",
            data_classification="fully_synthetic",
        )
