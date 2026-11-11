"""
TameerAI - Canonical SHA-256 Fingerprint Engine for Material Rate Observations

Provides deterministic, collision-resistant, and versioned hashing for
construction material price observations across Pakistani markets.

Identity fields defining a unique market rate observation:
1. canonical_version: Algorithm version ("tameerai:material-rate-observation:v1")
2. source_id: UUID of the data source / provider
3. product_id: UUID of canonical catalog product
4. city: Normalized market city (e.g. "lahore", "karachi", "islamabad")
5. published_date: UTC calendar date ("YYYY-MM-DD") representing quotation or publication day
6. normalized_price_pkr: Canonical decimal rate formatted to exactly 2 decimal places
7. normalized_unit: Standard measurement unit (e.g. "bag_50kg", "metric_ton", "cft", "1000_bricks")
8. dealer_id: Optional UUID of submitting dealer (or null if official statistical source)

Volatile ingestion metadata excluded from identity:
- collected_at / created_at (differ per crawl/scrape run)
- background_job_id (differs per worker run)
- raw_payload / scrape logs / transient HTTP response metrics
"""

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import unicodedata
import uuid
from typing import Any, Dict, Optional, Union


FINGERPRINT_VERSION_V1 = "tameerai:material-rate-observation:v1"


def _normalize_string(val: Optional[str]) -> str:
    """Performs NFKC Unicode normalization, strips outer whitespace, and converts to lowercase."""
    if val is None:
        return ""
    normalized = unicodedata.normalize("NFKC", str(val).strip().lower())
    # Collapse multiple consecutive whitespaces
    return " ".join(normalized.split())


def _normalize_date(val: Union[datetime, date, str, None]) -> str:
    """Normalizes datetime or date to ISO UTC date string (YYYY-MM-DD), or 'undated' if None."""
    if val is None or str(val).strip() in ("", "None", "null", "undated"):
        return "undated"
    if isinstance(val, datetime):
        if val.tzinfo is not None:
            val_utc = val.astimezone(timezone.utc)
            return val_utc.date().isoformat()
        return val.date().isoformat()
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, str):
        # Parse ISO or date string
        clean_str = val.strip()
        # Handle trailing Z or offset
        if "T" in clean_str or " " in clean_str:
            dt = datetime.fromisoformat(clean_str.replace("Z", "+00:00"))
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc)
            return dt.date().isoformat()
        # Just date part
        d = date.fromisoformat(clean_str[:10])
        return d.isoformat()
    raise ValueError(f"Unsupported date type: {type(val)}")


def _normalize_decimal(val: Union[Decimal, float, int, str, None]) -> str:
    """Normalizes numeric price to string with exactly 2 decimal places."""
    if val is None:
        raise ValueError("Price value is required for observation fingerprinting")
    try:
        if isinstance(val, Decimal):
            d = val
        elif isinstance(val, (int, str)):
            d = Decimal(str(val).strip())
        elif isinstance(val, float):
            d = Decimal(str(val))
        else:
            raise ValueError(f"Unsupported numeric type: {type(val)}")
        quantized = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"{quantized:.2f}"
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Invalid decimal value for fingerprint: {val}") from e


def _normalize_uuid(val: Union[uuid.UUID, str, None]) -> Optional[str]:
    """Normalizes UUID object or string to standard lowercase 36-char hyphenated string."""
    if val is None or str(val).strip() == "":
        return None
    if isinstance(val, uuid.UUID):
        return str(val).lower()
    return str(uuid.UUID(str(val).strip())).lower()


def generate_observation_fingerprint(
    *,
    source_id: Union[uuid.UUID, str],
    product_id: Union[uuid.UUID, str],
    city: str,
    published_at: Union[datetime, date, str],
    normalized_price_pkr: Union[Decimal, float, int, str],
    normalized_unit: str,
    dealer_id: Optional[Union[uuid.UUID, str]] = None,
    version: str = FINGERPRINT_VERSION_V1,
) -> str:
    """
    Computes a deterministic, canonical SHA-256 fingerprint for a material rate observation.
    
    Returns 64-character lowercase hex SHA-256 digest.
    """
    norm_source_id = _normalize_uuid(source_id)
    if not norm_source_id:
        raise ValueError("Valid source_id is required for observation fingerprint")

    norm_product_id = _normalize_uuid(product_id)
    if not norm_product_id:
        raise ValueError("Valid product_id is required for observation fingerprint")

    norm_city = _normalize_string(city)
    if not norm_city:
        raise ValueError("Valid city is required for observation fingerprint")

    norm_date = _normalize_date(published_at)
    norm_price = _normalize_decimal(normalized_price_pkr)
    norm_unit = _normalize_string(normalized_unit)
    if not norm_unit:
        raise ValueError("Valid normalized_unit is required for observation fingerprint")

    norm_dealer_id = _normalize_uuid(dealer_id)

    # Construct canonical payload with sorted keys
    canonical_payload: Dict[str, Any] = {
        "city": norm_city,
        "dealer_id": norm_dealer_id,
        "normalized_price_pkr": norm_price,
        "normalized_unit": norm_unit,
        "product_id": norm_product_id,
        "published_date": norm_date,
        "source_id": norm_source_id,
        "version": version,
    }

    # Stable JSON serialization (UTF-8, sorted keys, no redundant whitespace)
    serialized_bytes = json.dumps(
        canonical_payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(serialized_bytes).hexdigest()

