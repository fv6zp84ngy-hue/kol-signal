from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AdapterValidationLevel(str, Enum):
    """Public evidence level for an input adapter or import path."""

    VERIFIED = "Verified"
    EXPERIMENTAL = "Experimental"
    GENERIC_IMPORT = "Generic Import"
    NOT_TESTED = "Not Tested"


@dataclass(frozen=True, slots=True)
class NativeAdapter:
    """A versioned, deterministic mapping for a known export schema."""

    name: str
    version: str
    signature: frozenset[str]
    mapping: dict[str, str]
    validation_level: AdapterValidationLevel
    evidence_ids: tuple[str, ...]

    def matches(self, headers: list[str]) -> bool:
        return self.signature.issubset(set(headers))


WAVEINFLU_ADAPTER = NativeAdapter(
    name="waveinflu",
    version="1",
    signature=frozenset({"Wave Creator ID", "Platform UID", "Profile Link"}),
    mapping={
        "Wave Creator ID": "source_record_id",
        "Platform": "platform",
        "Platform UID": "platform_creator_id",
        "Username": "handle",
        "Profile Link": "profile_url",
        "Creator Name": "display_name",
        "Followers": "followers",
        "Avg Views": "average_views",
        "Engagement": "engagement_rate",
        "Country": "country",
        "Primary Language": "language",
        "Business Email": "email",
        "Email Type": "email_role",
        "Last Post": "latest_post_at",
        "Last Sponsored Post": "latest_sponsored_post_at",
        "Metrics Updated At": "observed_at",
        "Email Checked At": "email_observed_at",
        "Estimated Metrics": "is_estimated",
    },
    validation_level=AdapterValidationLevel.NOT_TESTED,
    evidence_ids=(
        "fixture_suite_v1",
        "waveinflu_public_product_metadata_2026_07_31",
    ),
)


NOX_ADAPTER = NativeAdapter(
    name="nox",
    version="1",
    signature=frozenset({"Nox ID", "Channel ID", "URL"}),
    mapping={
        "Nox ID": "source_record_id",
        "Channel": "platform",
        "Channel ID": "platform_creator_id",
        "Handle": "handle",
        "URL": "profile_url",
        "Name": "display_name",
        "Total Followers": "followers",
        "Average Views": "average_views",
        "Engagement Rate": "engagement_rate",
        "Location": "country",
        "Content Language": "language",
        "Email": "email",
        "Contact Type": "email_role",
        "Latest Upload": "latest_post_at",
        "Latest Brand Post": "latest_sponsored_post_at",
        "Observed At": "observed_at",
        "Email Observed At": "email_observed_at",
        "Data Estimated": "is_estimated",
    },
    validation_level=AdapterValidationLevel.NOT_TESTED,
    evidence_ids=(
        "fixture_suite_v1",
        "nox_public_product_metadata_2026_07_31",
    ),
)


NATIVE_ADAPTERS = (WAVEINFLU_ADAPTER, NOX_ADAPTER)


def detect_native_adapter(headers: list[str]) -> NativeAdapter | None:
    for adapter in NATIVE_ADAPTERS:
        if adapter.matches(headers):
            return adapter
    return None
