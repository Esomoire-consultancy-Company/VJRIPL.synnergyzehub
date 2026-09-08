from __future__ import annotations

import math
from datetime import datetime, timezone


MODEL_VERSION = "VOI-CI-R0.1"
EVIDENCE_CONTRACT = "VOI-INVENTORY-EVIDENCE-001"
ALLOWED_SIGNAL_TYPES = {
    "PRODUCT_VIEW",
    "ADD_TO_CART",
    "PURCHASE",
    "RETURN",
    "STOCKOUT",
}
REQUIRED_SNAPSHOT_FIELDS = {
    "sku",
    "available",
    "avgDailyDemand",
    "confirmedInbound",
    "leadTimeDays",
    "unitCost",
    "campaignUpliftPct",
    "observedAt",
    "evidenceRefs",
}


class CommercialIntelligenceValidationError(ValueError):
    pass


def _parse_datetime(value: str, field: str) -> datetime:
    text = (value or "").strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise CommercialIntelligenceValidationError(
            f"{field} must be ISO-8601: {value}"
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _finite_non_negative(value, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise CommercialIntelligenceValidationError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or number < 0:
        raise CommercialIntelligenceValidationError(
            f"{field} must be finite and non-negative"
        )
    return number


def validate_inventory_bundle(bundle: dict) -> dict:
    if not isinstance(bundle, dict) or bundle.get("contract") != EVIDENCE_CONTRACT:
        raise CommercialIntelligenceValidationError(
            f"expected contract {EVIDENCE_CONTRACT}"
        )

    payload = bundle.get("payload")
    if not isinstance(payload, dict):
        raise CommercialIntelligenceValidationError("payload is required")

    bundle_id = bundle.get("bundleId")
    if not isinstance(bundle_id, str) or not bundle_id.startswith("sha256:"):
        raise CommercialIntelligenceValidationError(
            "bundleId must be a sha256 digest"
        )

    _parse_datetime(payload.get("observedAt"), "payload.observedAt")
    snapshots = payload.get("snapshots")
    if not isinstance(snapshots, list) or not snapshots:
        raise CommercialIntelligenceValidationError(
            "payload.snapshots must be a non-empty list"
        )

    seen = set()
    for index, snapshot in enumerate(snapshots):
        if not isinstance(snapshot, dict):
            raise CommercialIntelligenceValidationError(
                f"snapshot[{index}] must be an object"
            )
        missing = REQUIRED_SNAPSHOT_FIELDS - set(snapshot)
        if missing:
            raise CommercialIntelligenceValidationError(
                f"snapshot[{index}] missing required fields: "
                f"{', '.join(sorted(missing))}"
            )

        sku = str(snapshot["sku"]).strip()
        if not sku or sku in seen:
            raise CommercialIntelligenceValidationError(
                f"duplicate or blank snapshot sku: {sku}"
            )
        seen.add(sku)

        for field in (
            "available",
            "avgDailyDemand",
            "confirmedInbound",
            "unitCost",
            "campaignUpliftPct",
        ):
            _finite_non_negative(snapshot[field], f"snapshot[{sku}].{field}")

        try:
            lead_time_days = int(snapshot["leadTimeDays"])
        except (TypeError, ValueError) as exc:
            raise CommercialIntelligenceValidationError(
                f"snapshot[{sku}].leadTimeDays must be an integer"
            ) from exc
        if lead_time_days < 1:
            raise CommercialIntelligenceValidationError(
                f"snapshot[{sku}].leadTimeDays must be >= 1"
            )

        _parse_datetime(snapshot["observedAt"], f"snapshot[{sku}].observedAt")
        if not isinstance(snapshot["evidenceRefs"], list):
            raise CommercialIntelligenceValidationError(
                f"snapshot[{sku}].evidenceRefs must be a list"
            )

    return bundle


def normalize_demand_signals(
    rows: list[dict[str, str]],
    *,
    inventory_bundle: dict,
) -> list[dict]:
    validate_inventory_bundle(inventory_bundle)
    evidence_time = _parse_datetime(
        inventory_bundle["payload"]["observedAt"],
        "payload.observedAt",
    )
    known_skus = {
        item["sku"] for item in inventory_bundle["payload"]["snapshots"]
    }

    normalized = []
    for index, row in enumerate(rows):
        sku = (row.get("sku") or "").strip()
        region = (row.get("region_id") or "").strip()
        signal_type = (row.get("signal_type") or "").strip().upper()

        if sku not in known_skus:
            raise CommercialIntelligenceValidationError(f"unknown sku: {sku}")
        if not region:
            raise CommercialIntelligenceValidationError(
                f"signal[{index}].region_id is required"
            )
        if signal_type not in ALLOWED_SIGNAL_TYPES:
            raise CommercialIntelligenceValidationError(
                f"unknown signal type: {signal_type}"
            )

        signal_value = _finite_non_negative(
            row.get("signal_value"),
            f"signal[{index}].signal_value",
        )
        signal_time = _parse_datetime(
            row.get("observed_at"),
            f"signal[{index}].observed_at",
        )
        if signal_time > evidence_time:
            raise CommercialIntelligenceValidationError(
                "signal observed_at is after evidence observation time"
            )

        normalized.append(
            {
                "sku": sku,
                "regionId": region,
                "signalType": signal_type,
                "signalValue": signal_value,
                "observedAt": signal_time.isoformat().replace("+00:00", "Z"),
            }
        )

    return sorted(
        normalized,
        key=lambda item: (
            item["regionId"],
            item["sku"],
            item["signalType"],
            item["observedAt"],
            item["signalValue"],
        ),
    )
