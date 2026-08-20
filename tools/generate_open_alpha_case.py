from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "examples" / "open_alpha_case"

WAVE_HEADERS = [
    "Wave Creator ID",
    "Platform",
    "Platform UID",
    "Username",
    "Profile Link",
    "Creator Name",
    "Followers",
    "Avg Views",
    "Engagement",
    "Country",
    "Primary Language",
    "Business Email",
    "Email Type",
    "Last Post",
    "Last Sponsored Post",
    "Metrics Updated At",
    "Email Checked At",
    "Estimated Metrics",
    "Notes",
]

NOX_HEADERS = [
    "Nox ID",
    "Channel",
    "Channel ID",
    "Handle",
    "URL",
    "Name",
    "Total Followers",
    "Average Views",
    "Engagement Rate",
    "Location",
    "Content Language",
    "Email",
    "Contact Type",
    "Latest Upload",
    "Latest Brand Post",
    "Observed At",
    "Email Observed At",
    "Data Estimated",
    "Notes",
]


def segment(creator_number: int) -> str:
    if creator_number <= 18:
        return "verify_high_conflict"
    if creator_number <= 38:
        return "priority"
    if creator_number <= 46:
        return "excluded_duplicate"
    if creator_number <= 55:
        return "verify_stale_contact"
    if creator_number <= 81:
        return "excluded_stale_contact"
    return "excluded_market"


def common_values(creator_number: int, source: str) -> dict[str, str]:
    creator_key = f"{creator_number:03d}"
    segment_name = segment(creator_number)
    country = "US" if segment_name in {
        "verify_high_conflict",
        "priority",
        "verify_stale_contact",
    } else "BR"
    language = "EN" if country == "US" else "PT"
    followers = (
        "140000"
        if segment_name == "verify_high_conflict" and source == "nox"
        else "100000"
    )
    email_checked = (
        "2026-01-01T08:00:00Z"
        if segment_name in {"verify_stale_contact", "excluded_stale_contact"}
        else "2026-07-30T08:00:00Z"
    )
    return {
        "creator_key": creator_key,
        "segment": segment_name,
        "platform_id": f"tt_open_alpha_{creator_key}",
        "handle": f"openalpha_pet_{creator_key}",
        "display_name": f"Fully Synthetic Creator {creator_key}",
        "followers": followers,
        "country": country,
        "language": language,
        "email": f"creator{creator_key}@open-alpha.example.com",
        "email_checked": email_checked,
    }


def wave_row(creator_number: int, occurrence: int) -> dict[str, str]:
    values = common_values(creator_number, "waveinflu")
    key = values["creator_key"]
    return {
        "Wave Creator ID": f"OA-W-{key}-{occurrence}",
        "Platform": "TikTok",
        "Platform UID": values["platform_id"],
        "Username": f"@{values['handle']}",
        "Profile Link": (
            f"https://tiktok.example.com/@{values['handle']}?"
            "utm_source=open_alpha_case"
        ),
        "Creator Name": values["display_name"],
        "Followers": values["followers"],
        "Avg Views": "30000",
        "Engagement": "4.0%",
        "Country": values["country"],
        "Primary Language": values["language"],
        "Business Email": values["email"],
        "Email Type": "creator",
        "Last Post": "2026-07-29",
        "Last Sponsored Post": "2026-07-10",
        "Metrics Updated At": "2026-07-30T08:00:00Z",
        "Email Checked At": values["email_checked"],
        "Estimated Metrics": "false",
        "Notes": f"Fully Synthetic Open Alpha Case; segment={values['segment']}",
    }


def nox_row(creator_number: int) -> dict[str, str]:
    values = common_values(creator_number, "nox")
    key = values["creator_key"]
    return {
        "Nox ID": f"OA-N-{key}-1",
        "Channel": "Tik Tok",
        "Channel ID": values["platform_id"],
        "Handle": values["handle"].upper(),
        "URL": (
            f"https://tiktok.example.com/@{values['handle']}?"
            "ref=open_alpha_case"
        ),
        "Name": values["display_name"],
        "Total Followers": values["followers"],
        "Average Views": "30000",
        "Engagement Rate": "0.04",
        "Location": values["country"],
        "Content Language": values["language"],
        "Email": values["email"],
        "Contact Type": "creator",
        "Latest Upload": "2026-07-29",
        "Latest Brand Post": "2026-07-10",
        "Observed At": "2026-07-30T08:00:00Z",
        "Email Observed At": values["email_checked"],
        "Data Estimated": "false",
        "Notes": f"Fully Synthetic Open Alpha Case; segment={values['segment']}",
    }


def build_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    wave_rows: list[dict[str, str]] = []
    nox_rows: list[dict[str, str]] = []
    for creator_number in range(1, 215):
        if creator_number <= 20:
            wave_rows.append(wave_row(creator_number, 1))
            wave_rows.append(wave_row(creator_number, 2))
            nox_rows.append(nox_row(creator_number))
        elif creator_number <= 46:
            wave_rows.append(wave_row(creator_number, 1))
            nox_rows.append(nox_row(creator_number))
        elif creator_number <= 120:
            wave_rows.append(wave_row(creator_number, 1))
        else:
            nox_rows.append(nox_row(creator_number))
    assert len(wave_rows) == 140
    assert len(nox_rows) == 140
    return wave_rows, nox_rows


def write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def generate(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    wave_rows, nox_rows = build_rows()
    write_csv(output / "waveinflu_case.csv", WAVE_HEADERS, wave_rows)
    write_csv(output / "nox_case.csv", NOX_HEADERS, nox_rows)
    (output / "campaign.txt").write_text(
        "品牌：Open Alpha Smart Pet Example。\n"
        "这是一个完全合成案例，只展示宠物智能硬件出海名单审计工作流。\n"
        "目标市场为美国，内容语言为英语。\n"
        "平台优先 TikTok。\n"
        "粉丝量 10K–500K。\n"
        "最近 30 天内需要发布过内容。\n"
        "需要存在可用的商务联系路径。\n",
        encoding="utf-8",
    )
    expected = {
        "schema_version": 1,
        "data_classification": "fully_synthetic",
        "business_effect_inference_allowed": False,
        "metrics": {
            "raw_records": 280,
            "canonical_creators": 214,
            "duplicate_groups": 46,
            "review_candidates": 0,
            "high_conflict_fields": 18,
            "stale_critical_fields": 35,
            "action_levels": {
                "Excluded": 167,
                "Priority": 20,
                "Verify": 27,
            },
        },
    }
    (output / "expected_metrics.json").write_text(
        json.dumps(expected, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the fully synthetic Open Alpha case inputs."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    args = parser.parse_args()
    generate(args.output.resolve())


if __name__ == "__main__":
    main()
