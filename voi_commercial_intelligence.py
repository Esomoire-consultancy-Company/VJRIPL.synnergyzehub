from __future__ import annotations

import hashlib
import json
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
SIGNAL_WEIGHTS = {
    "PRODUCT_VIEW": 0.05,
    "ADD_TO_CART": 0.25,
    "PURCHASE": 1.0,
    "RETURN": -1.0,
    "STOCKOUT": 0.5,
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


def _canonical_json(payload: dict) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256_id(payload: dict) -> str:
    return "sha256:" + hashlib.sha256(
        _canonical_json(payload).encode("utf-8")
    ).hexdigest()


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

    integrity = bundle.get("integrity")
    if not isinstance(integrity, dict):
        raise CommercialIntelligenceValidationError("integrity is required")
    if integrity.get("algorithm") != "SHA-256":
        raise CommercialIntelligenceValidationError(
            "integrity algorithm must be SHA-256"
        )

    canonical_payload = _canonical_json(payload)
    expected_digest = "sha256:" + hashlib.sha256(
        canonical_payload.encode("utf-8")
    ).hexdigest()
    if bundle_id != expected_digest or integrity.get("digest") != expected_digest:
        raise CommercialIntelligenceValidationError("integrity digest mismatch")
    if integrity.get("canonicalPayload") != canonical_payload:
        raise CommercialIntelligenceValidationError(
            "integrity canonical payload mismatch"
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


def _snapshot_by_sku(inventory_bundle: dict) -> dict[str, dict]:
    return {
        item["sku"]: item
        for item in inventory_bundle["payload"]["snapshots"]
    }


def _days_cover(snapshot: dict) -> float | None:
    demand = float(snapshot["avgDailyDemand"])
    if demand == 0:
        return None
    return (
        float(snapshot["available"]) + float(snapshot["confirmedInbound"])
    ) / demand


def build_demand_matrix(
    inventory_bundle: dict,
    demand_signals: list[dict] | None = None,
) -> list[dict]:
    validate_inventory_bundle(inventory_bundle)
    snapshots = _snapshot_by_sku(inventory_bundle)
    raw_by_region_sku: dict[tuple[str, str], float] = {}

    if demand_signals:
        for signal in demand_signals:
            key = (signal["regionId"], signal["sku"])
            raw_by_region_sku[key] = raw_by_region_sku.get(key, 0.0) + (
                SIGNAL_WEIGHTS[signal["signalType"]] * float(signal["signalValue"])
            )
        regions = sorted({signal["regionId"] for signal in demand_signals})
        for region in regions:
            for sku in snapshots:
                raw_by_region_sku.setdefault((region, sku), 0.0)
    else:
        window = int(inventory_bundle["payload"]["demandWindowDays"])
        for sku, snapshot in snapshots.items():
            raw_by_region_sku[("UNSCOPED", sku)] = (
                float(snapshot["avgDailyDemand"]) * window
            )

    clamped = {
        key: max(0.0, value)
        for key, value in raw_by_region_sku.items()
    }
    maxima: dict[str, float] = {}
    for (region, _sku), value in clamped.items():
        maxima[region] = max(maxima.get(region, 0.0), value)

    rows = []
    for (region, sku), raw in sorted(clamped.items()):
        snapshot = snapshots[sku]
        maximum = maxima[region]
        rows.append(
            {
                "sku": sku,
                "regionId": region,
                "rawIntent": raw,
                "demandScore": (raw / maximum * 100.0) if maximum > 0 else 0.0,
                "available": float(snapshot["available"]),
                "confirmedInbound": float(snapshot["confirmedInbound"]),
                "avgDailyDemand": float(snapshot["avgDailyDemand"]),
                "leadTimeDays": int(snapshot["leadTimeDays"]),
                "daysCover": _days_cover(snapshot),
                "evidenceRefs": sorted(set(snapshot["evidenceRefs"])),
            }
        )
    return rows


def route_ready_goods(
    demand_matrix: list[dict],
    *,
    target_days_cover: int = 14,
) -> list[dict]:
    if target_days_cover <= 0:
        raise CommercialIntelligenceValidationError(
            "target_days_cover must be positive"
        )

    routes = []
    for row in demand_matrix:
        route = dict(row)
        total_stock = float(row["available"]) + float(row["confirmedInbound"])
        if float(row["avgDailyDemand"]) > 0 and total_stock == 0:
            route_class = "INVESTIGATE"
            rule = "DEMAND_WITHOUT_READY_OR_INBOUND_STOCK"
        elif (
            float(row["avgDailyDemand"]) > 0
            and row["daysCover"] is not None
            and float(row["daysCover"]) < target_days_cover
            and float(row["available"]) > 0
        ):
            route_class = "REPLENISH"
            rule = "LOW_DAYS_COVER_WITH_READY_GOODS"
        else:
            route_class = "HOLD"
            rule = "SUFFICIENT_COVER_OR_NO_ACTIONABLE_DEMAND"

        route["routeClass"] = route_class
        route["routeRule"] = rule
        routes.append(route)

    return routes


def build_replenishment_recommendations(
    routes: list[dict],
    *,
    target_days_cover: int = 14,
) -> list[dict]:
    recommendations = []
    for row in routes:
        if row["routeClass"] != "REPLENISH":
            continue

        target_stock = float(row["avgDailyDemand"]) * target_days_cover
        quantity = max(
            0.0,
            target_stock
            - float(row["available"])
            - float(row["confirmedInbound"]),
        )
        recommendations.append(
            {
                "decisionClass": "REPLENISH",
                "sku": row["sku"],
                "regionId": row["regionId"],
                "recommendedQty": quantity,
                "targetDaysCover": target_days_cover,
                "reason": {
                    "rule": row["routeRule"],
                    "daysCover": row["daysCover"],
                    "demandScore": row["demandScore"],
                },
                "authorityState": "RECOMMENDED_ONLY",
                "evidenceRefs": sorted(set(row["evidenceRefs"])),
            }
        )

    return sorted(
        recommendations,
        key=lambda item: (item["regionId"], item["sku"]),
    )


def detect_assortment_risks(
    inventory_bundle: dict,
    *,
    slow_stock_days: int = 45,
) -> tuple[list[dict], dict]:
    validate_inventory_bundle(inventory_bundle)
    if slow_stock_days <= 0:
        raise CommercialIntelligenceValidationError(
            "slow_stock_days must be positive"
        )

    snapshots = inventory_bundle["payload"]["snapshots"]
    risks = []

    for snapshot in snapshots:
        available = float(snapshot["available"])
        demand = float(snapshot["avgDailyDemand"])
        cover = _days_cover(snapshot)
        if available > 0 and (
            demand == 0
            or (cover is not None and cover > slow_stock_days)
        ):
            risks.append(
                {
                    "riskType": "SLOW_STOCK",
                    "sku": snapshot["sku"],
                    "daysCover": cover,
                    "available": available,
                    "evidenceRefs": sorted(set(snapshot["evidenceRefs"])),
                }
            )

    lineage_ready = all(
        "styleId" in item and "size" in item
        for item in snapshots
    )
    capability = {
        "brokenSizeDetection": (
            "AVAILABLE"
            if lineage_ready
            else "INSUFFICIENT_STYLE_SIZE_EVIDENCE"
        )
    }

    if lineage_ready:
        by_style: dict[str, list[dict]] = {}
        for snapshot in snapshots:
            by_style.setdefault(str(snapshot["styleId"]), []).append(snapshot)

        for style_id, items in sorted(by_style.items()):
            present = sorted(
                str(item["size"])
                for item in items
                if float(item["available"]) > 0
            )
            missing = sorted(
                str(item["size"])
                for item in items
                if float(item["available"]) == 0
            )
            if present and missing:
                evidence_refs = sorted(
                    {
                        ref
                        for item in items
                        for ref in item["evidenceRefs"]
                    }
                )
                risks.append(
                    {
                        "riskType": "BROKEN_SIZE",
                        "styleId": style_id,
                        "presentSizes": present,
                        "missingSizes": missing,
                        "evidenceRefs": evidence_refs,
                    }
                )

    risks.sort(
        key=lambda item: (
            item["riskType"],
            item.get("styleId", ""),
            item.get("sku", ""),
        )
    )
    return risks, capability


def build_recommendation_ledger(
    inventory_bundle: dict,
    recommendations: list[dict],
    risks: list[dict],
    capability_state: dict,
    *,
    model_version: str = MODEL_VERSION,
) -> dict:
    validate_inventory_bundle(inventory_bundle)
    source_bundle_id = inventory_bundle["bundleId"]

    with_ids = []
    for recommendation in recommendations:
        business_payload = {
            "modelVersion": model_version,
            "sourceBundleId": source_bundle_id,
            "recommendation": recommendation,
        }
        with_ids.append(
            {
                "recommendationId": _sha256_id(business_payload),
                **recommendation,
            }
        )

    canonical = {
        "schemaVersion": "1.0.0",
        "contract": "VOI-COMMERCIAL-INTELLIGENCE-001",
        "modelVersion": model_version,
        "sourceBundleId": source_bundle_id,
        "evidenceObservedAt": inventory_bundle["payload"]["observedAt"],
        "recommendations": sorted(
            with_ids,
            key=lambda item: item["recommendationId"],
        ),
        "risks": sorted(risks, key=lambda item: _canonical_json(item)),
        "capabilityState": dict(sorted(capability_state.items())),
    }
    ledger_id = _sha256_id(canonical)
    return {
        **canonical,
        "integrity": {
            "algorithm": "SHA-256",
            "digest": ledger_id,
        },
        "ledgerId": ledger_id,
    }
