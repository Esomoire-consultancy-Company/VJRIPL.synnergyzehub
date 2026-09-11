from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


class EvidenceValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SourceFileEvidence:
    source_name: str
    path: str
    sha256: str
    row_count: int


def parse_datetime(value: str, field: str) -> datetime:
    text = (value or "").strip()
    if not text:
        raise EvidenceValidationError(f"{field} is required")
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EvidenceValidationError(f"{field} must be ISO-8601: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_date(value: str, field: str) -> datetime:
    text = (value or "").strip()
    if not text:
        raise EvidenceValidationError(f"{field} is required")
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EvidenceValidationError(
            f"{field} must be an ISO-8601 date or datetime: {value}"
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_float(value: str, field: str, *, minimum: float | None = None) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceValidationError(f"{field} must be numeric: {value}") from exc
    if not math.isfinite(parsed):
        raise EvidenceValidationError(f"{field} must be finite: {value}")
    if minimum is not None and parsed < minimum:
        raise EvidenceValidationError(f"{field} must be >= {minimum}: {value}")
    return parsed


def parse_int(value: str, field: str, *, minimum: int | None = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceValidationError(f"{field} must be an integer: {value}") from exc
    if minimum is not None and parsed < minimum:
        raise EvidenceValidationError(f"{field} must be >= {minimum}: {value}")
    return parsed


def read_csv(
    path: Path,
    source_name: str,
) -> tuple[list[dict[str, str]], SourceFileEvidence, list[str]]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames:
        raise EvidenceValidationError(f"{source_name} has no header row")

    headers = [(header or "").strip() for header in reader.fieldnames]
    if any(not header for header in headers):
        raise EvidenceValidationError(f"{source_name} contains a blank column header")
    if len(set(headers)) != len(headers):
        raise EvidenceValidationError(f"{source_name} contains duplicate column headers")
    reader.fieldnames = headers

    rows: list[dict[str, str]] = []
    for row_number, row in enumerate(reader, start=2):
        if None in row:
            raise EvidenceValidationError(
                f"{source_name} row {row_number} contains more fields than the header"
            )
        normalized_row: dict[str, str] = {}
        for key, value in row.items():
            if isinstance(value, list):
                raise EvidenceValidationError(
                    f"{source_name} row {row_number} contains malformed extra fields"
                )
            normalized_row[key] = (value or "").strip()
        rows.append(normalized_row)

    return rows, SourceFileEvidence(source_name, path.name, digest, len(rows)), headers


def require_columns(
    rows: list[dict[str, str]],
    headers: Iterable[str],
    columns: Iterable[str],
    source_name: str,
    *,
    allow_empty: bool = False,
) -> None:
    available = set(headers)
    missing = [column for column in columns if column not in available]
    if missing:
        raise EvidenceValidationError(
            f"{source_name} missing required columns: {', '.join(missing)}"
        )
    if not rows and not allow_empty:
        raise EvidenceValidationError(f"{source_name} contains no data rows")


def canonical_json(payload: dict) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"
