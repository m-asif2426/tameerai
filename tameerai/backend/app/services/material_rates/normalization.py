"""
TameerAI - Material Rate Normalization & Canonical Unit Conversion Pipeline (Stage 2A / 2B.1)

Standardizes:
- Category resolution (cement, steel, bricks, sand, crush, blocks, tiles).
- Measurement units (bag_50kg, metric_ton, 1000_bricks, cft, sqft, piece).
- Reversible unit conversions with lossless Decimal arithmetic.
- Geographic semantics: separates buyer market city from quarry origin, river basin, and plant.
- Publication date normalization: preserves None for undated indicative estimates.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from typing import Any, Optional, Tuple, Union

from app.services.material_rates.contracts import NormalizedCategory


# Standard Pakistani Construction Cities Map (English, Urdu, Transliterations)
PAKISTAN_CITIES_CANONICAL = {
    "lahore": "Lahore",
    "lhr": "Lahore",
    "لاہور": "Lahore",
    "karachi": "Karachi",
    "khi": "Karachi",
    "کراچی": "Karachi",
    "islamabad": "Islamabad",
    "isb": "Islamabad",
    "اسلام آباد": "Islamabad",
    "rawalpindi": "Rawalpindi",
    "rwp": "Rawalpindi",
    "راولپنڈی": "Rawalpindi",
    "peshawar": "Peshawar",
    "پشاور": "Peshawar",
    "multan": "Multan",
    "ملتان": "Multan",
    "faisalabad": "Faisalabad",
    "fsd": "Faisalabad",
    "فیصل آباد": "Faisalabad",
    "quetta": "Quetta",
    "کوئٹہ": "Quetta",
    "gujranwala": "Gujranwala",
    "گوجرانوالہ": "Gujranwala",
    "sialkot": "Sialkot",
    "سیالکوٹ": "Sialkot",
    "hyderabad": "Hyderabad",
    "حیدرآباد": "Hyderabad",
    "attock": "Attock",
    "sahiwal": "Sahiwal",
    "jhang": "Jhang",
    "bahawalpur": "Bahawalpur",
    "d. g. khan": "Dera Ghazi Khan",
    "dg khan": "Dera Ghazi Khan",
    "khushab": "Khushab",
    "sargodha": "Sargodha",
    "sukkur": "Sukkur",
    "larkana": "Larkana",
}

# Known Natural Resource Origins (Quarries, Basins, Plants)
# These represent material extraction or processing sites, NOT buyer market cities.
KNOWN_QUARRIES = {
    "margalla": "Margalla",
    "sargodha": "Sargodha",
    "dina": "Dina",
    "sakhi sarwar": "Sakhi Sarwar",
    "chhablat": "Chhablat",
    "hub": "Hub",
    "manghopir": "Manghopir",
    "taxila": "Taxila",
}

KNOWN_RIVER_BASINS = {
    "chenab": "Chenab",
    "ravi": "Ravi",
    "indus": "Indus",
    "soan": "Soan",
    "bolan": "Bolan",
    "lawrencepur": "Lawrencepur",
    "ghazi": "Ghazi",
    "haro": "Haro",
}

KNOWN_MFR_PLANTS = {
    "hattar": "Hattar",
    "iskanderabad": "Iskanderabad",
    "daud khel": "Daud Khel",
    "wah": "Wah",
    "chakwal": "Chakwal",
    "pezu": "Pezu",
    "khairpur": "Khairpur",
}

# Canonical Target Units:
# - Cement: bag_50kg
# - Steel: metric_ton (1 metric_ton = 1000 kg)
# - Bricks: 1000_bricks (1 1000_bricks = 1000 pieces)
# - Sand: cft (1 100_cft = 100 cft)
# - Crush: cft (1 100_cft = 100 cft)
# - Blocks: piece (1 100_blocks = 100 pieces)
# - Tiles: sqft (1 sqm = 10.7639 sqft)

# Unit Aliases & Multipliers from raw unit price to canonical unit price
# Formula: canonical_price = raw_price * multiplier
UNIT_NORMALIZATION_MAP = {
    # Cement -> bag_50kg
    "bag": ("bag_50kg", Decimal("1.0")),
    "bag_50kg": ("bag_50kg", Decimal("1.0")),
    "50kg bag": ("bag_50kg", Decimal("1.0")),
    "50 kg bag": ("bag_50kg", Decimal("1.0")),
    "bori": ("bag_50kg", Decimal("1.0")),
    "بوری": ("bag_50kg", Decimal("1.0")),
    "cement bag": ("bag_50kg", Decimal("1.0")),

    # Steel / Rebar -> metric_ton
    # 1 metric ton = 1,000 kg. If raw is per-kg, price-per-ton = raw_price * 1000
    "ton": ("metric_ton", Decimal("1.0")),
    "metric ton": ("metric_ton", Decimal("1.0")),
    "metric_ton": ("metric_ton", Decimal("1.0")),
    "m ton": ("metric_ton", Decimal("1.0")),
    "tonne": ("metric_ton", Decimal("1.0")),
    "ٹن": ("metric_ton", Decimal("1.0")),
    "sutar ton": ("metric_ton", Decimal("1.0")),
    "kg": ("metric_ton", Decimal("1000.0")),
    "kilogram": ("metric_ton", Decimal("1000.0")),
    "per kg": ("metric_ton", Decimal("1000.0")),
    "/ kg": ("metric_ton", Decimal("1000.0")),

    # Bricks / Clay masonry -> 1000_bricks
    # If raw is per-piece, price-per-thousand = raw_price * 1000
    "1000 bricks": ("1000_bricks", Decimal("1.0")),
    "1000_bricks": ("1000_bricks", Decimal("1.0")),
    "1000 nos": ("1000_bricks", Decimal("1.0")),
    "thousand_nos": ("1000_bricks", Decimal("1.0")),
    "hazar eent": ("1000_bricks", Decimal("1.0")),
    "ہزار اینٹ": ("1000_bricks", Decimal("1.0")),
    "per thousand": ("1000_bricks", Decimal("1.0")),
    "per 1000": ("1000_bricks", Decimal("1.0")),
    "per piece": ("1000_bricks", Decimal("1000.0")),
    "piece": ("1000_bricks", Decimal("1000.0")),
    "nos": ("1000_bricks", Decimal("1000.0")),
    "brick": ("1000_bricks", Decimal("1000.0")),
    "/ brick": ("1000_bricks", Decimal("1000.0")),

    # Sand & Aggregate (Crush) -> cft
    # If raw is per-100-cft truck, price-per-cft = raw_price * 0.01
    "cft": ("cft", Decimal("1.0")),
    "cubic feet": ("cft", Decimal("1.0")),
    "cu.ft": ("cft", Decimal("1.0")),
    "cuft": ("cft", Decimal("1.0")),
    "کیوبک فٹ": ("cft", Decimal("1.0")),
    "feet": ("cft", Decimal("1.0")),
    "foot": ("cft", Decimal("1.0")),
    "/ cft": ("cft", Decimal("1.0")),
    "per cft": ("cft", Decimal("1.0")),
    "100 cft": ("cft", Decimal("0.01")),
    "100_cft": ("cft", Decimal("0.01")),
    "hundred_cft": ("cft", Decimal("0.01")),
    "per hundred cft": ("cft", Decimal("0.01")),
    "100 cft truck": ("cft", Decimal("0.01")),

    # Blocks -> piece
    "block": ("piece", Decimal("1.0")),
    "concrete block": ("piece", Decimal("1.0")),
    "100 blocks": ("piece", Decimal("0.01")),
    "100 nos": ("piece", Decimal("0.01")),

    # Tiles -> sqft
    "sqft": ("sqft", Decimal("1.0")),
    "sq ft": ("sqft", Decimal("1.0")),
    "square feet": ("sqft", Decimal("1.0")),
    "مربع فٹ": ("sqft", Decimal("1.0")),
    "meter": ("sqft", Decimal("10.7639")),
    "sqm": ("sqft", Decimal("10.7639")),
}


# Regional / Province scopes that cannot be used as city-level market pricing locations
PROHIBITED_REGIONS = {
    "punjab",
    "sindh",
    "kpk",
    "khyber pakhtunkhwa",
    "balochistan",
    "gilgit baltistan",
    "azad kashmir",
    "ajk",
    "pakistan",
    "national",
    "all pakistan",
    "پنجاب",
    "سندھ",
    "بلوچستان",
    "خیبر پختونخوا",
    "گلگت بلتستان",
    "آزاد کشمیر",
    "پاکستان",
}


class NormalizationError(ValueError):
    """Raised when critical fields cannot be normalized into valid domain forms."""
    pass


class NormalizedLocation(tuple):
    """
    Structured geographic representation that behaves as a 3-tuple:
    (canonical_city, locality_or_district, raw_location)
    while also exposing distinct resource provenance:
    - canonical_city (Optional[str])
    - locality_or_district (Optional[str])
    - raw_location (str)
    - quarry_origin (Optional[str])
    - river_basin (Optional[str])
    - manufacturing_plant (Optional[str])
    """

    def __new__(
        cls,
        canonical_city: Optional[str],
        locality_or_district: Optional[str],
        raw_location: str,
        quarry_origin: Optional[str] = None,
        river_basin: Optional[str] = None,
        manufacturing_plant: Optional[str] = None,
    ):
        instance = super().__new__(cls, (canonical_city, locality_or_district, raw_location))
        instance.canonical_city = canonical_city
        instance.locality_or_district = locality_or_district
        instance.raw_location = raw_location
        instance.quarry_origin = quarry_origin
        instance.river_basin = river_basin
        instance.manufacturing_plant = manufacturing_plant
        return instance


def normalize_location(raw_location: Optional[str]) -> NormalizedLocation:
    """
    Normalizes Pakistani construction location into distinct concepts:
    1. canonical_city (buyer market city, or None if only quarry/basin is known)
    2. locality_or_district (e.g. 'Lahore Cantt', 'Karachi South')
    3. raw_location (original string preserved verbatim)
    4. quarry_origin (e.g. 'Margalla', 'Sargodha')
    5. river_basin (e.g. 'Chenab', 'Ravi', 'Lawrencepur')
    6. manufacturing_plant (e.g. 'Hattar', 'Iskanderabad')

    Raises NormalizationError for missing, empty, or ambiguous regional/province scopes.
    """
    if not raw_location or not str(raw_location).strip():
        raise NormalizationError("Missing location/city name in market record")

    raw_stripped = str(raw_location).strip()
    clean = " ".join(re.sub(r"[^\w\s\u0600-\u06FF-]", " ", raw_stripped).split()).lower()

    if clean in PROHIBITED_REGIONS:
        raise NormalizationError(f"Ambiguous or regional non-city location: '{raw_stripped}'")

    # Detect natural resource and plant origins
    quarry = None
    for k, v in KNOWN_QUARRIES.items():
        if re.search(r"\b" + re.escape(k) + r"\b", clean):
            quarry = v
            break

    river = None
    for k, v in KNOWN_RIVER_BASINS.items():
        if re.search(r"\b" + re.escape(k) + r"\b", clean):
            river = v
            break

    plant = None
    for k, v in KNOWN_MFR_PLANTS.items():
        if re.search(r"\b" + re.escape(k) + r"\b", clean):
            plant = v
            break

    # 1. Exact match against canonical market city dictionary
    if clean in PAKISTAN_CITIES_CANONICAL:
        canonical = PAKISTAN_CITIES_CANONICAL[clean]
        return NormalizedLocation(
            canonical_city=canonical,
            locality_or_district=None,
            raw_location=raw_stripped,
            quarry_origin=quarry,
            river_basin=river,
            manufacturing_plant=plant,
        )

    # 2. Check for city embedded with locality/district details (e.g. 'Lahore Cantt', 'Karachi South')
    for key, canonical in sorted(PAKISTAN_CITIES_CANONICAL.items(), key=lambda x: -len(x[0])):
        pattern = r"\b" + re.escape(key) + r"\b"
        if re.search(pattern, clean):
            return NormalizedLocation(
                canonical_city=canonical,
                locality_or_district=raw_stripped,
                raw_location=raw_stripped,
                quarry_origin=quarry,
                river_basin=river,
                manufacturing_plant=plant,
            )

    # 3. If source only references a quarry or river basin and NO market city is given,
    # DO NOT invent a market city; leave canonical_city=None
    if quarry or river or plant:
        return NormalizedLocation(
            canonical_city=None,
            locality_or_district=raw_stripped,
            raw_location=raw_stripped,
            quarry_origin=quarry,
            river_basin=river,
            manufacturing_plant=plant,
        )

    # 4. Unknown specific municipality/town
    words = raw_stripped.split()
    if len(words) == 1:
        return NormalizedLocation(
            canonical_city=words[0].title(),
            locality_or_district=None,
            raw_location=raw_stripped,
        )
    return NormalizedLocation(
        canonical_city=words[0].title(),
        locality_or_district=raw_stripped,
        raw_location=raw_stripped,
    )


def normalize_city(raw_city: Optional[str]) -> Optional[str]:
    """Normalizes Pakistani city name to standard canonical string, or None if purely regional origin."""
    try:
        norm_loc = normalize_location(raw_city)
        return norm_loc.canonical_city
    except NormalizationError:
        return None


def convert_price(
    price: Union[Decimal, float, str, int],
    from_unit: str,
    to_unit: str,
    *,
    vehicle_capacity_cft: Optional[Union[Decimal, float, int]] = None,
) -> Decimal:
    """
    Explicit, reversible, lossless unit converter using Decimal arithmetic.
    Supported bidirectional conversions:
    - kg <-> metric_ton (1 metric_ton = 1000 kg)
    - 100_cft <-> cft (1 100_cft = 100 cft)
    - piece <-> 1000_bricks (1 1000_bricks = 1000 pieces)
    - 100_blocks <-> piece (1 100_blocks = 100 pieces)
    - sqm <-> sqft (1 sqm = 10.7639 sqft)
    - truckload -> cft ONLY if vehicle_capacity_cft is explicitly declared (> 0)
    """
    d_price = Decimal(str(price)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    f = from_unit.strip().lower()
    t = to_unit.strip().lower()

    if f == t:
        return d_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Truckload -> CFT explicitly guarded
    if f in ("truck", "truckload", "dumper", "trolley") and t in ("cft", "cuft", "cubic feet"):
        if vehicle_capacity_cft is not None and Decimal(str(vehicle_capacity_cft)) > 0:
            return (d_price / Decimal(str(vehicle_capacity_cft))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        raise NormalizationError(
            f"Cannot convert '{from_unit}' to '{to_unit}' without explicitly declared vehicle capacity. "
            "Universal truck capacity must never be assumed."
        )

    # Steel: kg <-> metric_ton
    if f in ("kg", "kilogram") and t in ("metric_ton", "ton", "tonne"):
        return (d_price * Decimal("1000.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if f in ("metric_ton", "ton", "tonne") and t in ("kg", "kilogram"):
        return (d_price * Decimal("0.001")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Sand / Crush: 100_cft <-> cft
    if f in ("100_cft", "100 cft", "hundred_cft") and t in ("cft", "cuft", "cubic feet"):
        return (d_price * Decimal("0.01")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if f in ("cft", "cuft", "cubic feet") and t in ("100_cft", "100 cft", "hundred_cft"):
        return (d_price * Decimal("100.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Bricks: piece <-> 1000_bricks
    if f in ("piece", "nos", "brick") and t in ("1000_bricks", "1000 bricks", "thousand_nos"):
        return (d_price * Decimal("1000.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if f in ("1000_bricks", "1000 bricks", "thousand_nos") and t in ("piece", "nos", "brick"):
        return (d_price * Decimal("0.001")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Blocks: 100_blocks <-> piece
    if f in ("100_blocks", "100 blocks", "100 nos") and t in ("piece", "block"):
        return (d_price * Decimal("0.01")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if f in ("piece", "block") and t in ("100_blocks", "100 blocks", "100 nos"):
        return (d_price * Decimal("100.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Tiles: sqm <-> sqft
    if f in ("sqm", "meter", "sq_meter") and t in ("sqft", "sq_ft", "square feet"):
        return (d_price * Decimal("10.7639")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if f in ("sqft", "sq_ft", "square feet") and t in ("sqm", "meter", "sq_meter"):
        return (d_price / Decimal("10.7639")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    raise NormalizationError(f"Unsupported conversion pair: '{from_unit}' to '{to_unit}'")


def normalize_unit_and_price(
    raw_price: Any,
    raw_unit: Optional[str],
    *,
    vehicle_capacity_cft: Optional[Union[Decimal, float, int]] = None,
) -> Tuple[Decimal, str, Decimal, str]:
    """
    Validates and normalizes raw price and measurement unit.
    Returns: (observed_price_pkr, observed_unit, normalized_price_pkr, normalized_unit)

    Truckload Rule:
    Never assume every truck has the same capacity.
    Truckload-to-CFT conversion requires an explicitly declared vehicle capacity.
    If capacity is unavailable, the original unit is retained with factor 1.0 rather than inventing a conversion.
    """
    if raw_price is None or str(raw_price).strip() == "":
        raise NormalizationError("Missing price value in market record")

    # Clean price string
    clean_price_str = str(raw_price).replace(",", "").replace("PKR", "").replace("Rs.", "").replace("Rs", "").strip()
    try:
        observed_price = Decimal(clean_price_str).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as e:
        raise NormalizationError(f"Invalid numeric price format: '{raw_price}'") from e

    if observed_price < 0:
        raise NormalizationError(f"Negative price is invalid: {observed_price}")

    if not raw_unit or not str(raw_unit).strip():
        raise NormalizationError("Missing unit of measurement in market record")

    clean_unit = str(raw_unit).strip().lower()
    clean_unit_key = " ".join(re.sub(r"[^\w\s\u0600-\u06FF/]", " ", clean_unit).split())

    # Bulk transport / truck check
    is_bulk_truck = any(t in clean_unit_key for t in ("truck", "truckload", "dumper", "trolley"))
    if is_bulk_truck and "100 cft" not in clean_unit_key:
        if vehicle_capacity_cft is not None and Decimal(str(vehicle_capacity_cft)) > 0:
            cap = Decimal(str(vehicle_capacity_cft))
            norm_info = ("cft", (Decimal("1.0") / cap))
        else:
            # Retain original unit without assuming unverified capacity
            norm_info = (clean_unit_key.replace(" ", "_"), Decimal("1.0"))
    else:
        # Direct match or alias
        norm_info = UNIT_NORMALIZATION_MAP.get(clean_unit_key)
        if not norm_info:
            # Partial pattern checks
            if "bag" in clean_unit_key or "bori" in clean_unit_key:
                norm_info = ("bag_50kg", Decimal("1.0"))
            elif "kg" in clean_unit_key or "kilo" in clean_unit_key:
                norm_info = ("metric_ton", Decimal("1000.0"))
            elif "ton" in clean_unit_key:
                norm_info = ("metric_ton", Decimal("1.0"))
            elif "100 cft" in clean_unit_key or "hundred cft" in clean_unit_key:
                norm_info = ("cft", Decimal("0.01"))
            elif "cft" in clean_unit_key or "feet" in clean_unit_key:
                norm_info = ("cft", Decimal("1.0"))
            elif "piece" in clean_unit_key or "brick" in clean_unit_key:
                norm_info = ("1000_bricks", Decimal("1000.0"))
            elif "1000" in clean_unit_key or "hazar" in clean_unit_key:
                norm_info = ("1000_bricks", Decimal("1.0"))
            else:
                norm_info = (clean_unit_key.replace(" ", "_"), Decimal("1.0"))

    normalized_unit, factor = norm_info
    normalized_price = (observed_price * factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return observed_price, str(raw_unit).strip(), normalized_price, normalized_unit


def normalize_published_date(raw_date: Any) -> Optional[datetime]:
    """
    Normalizes raw publication timestamp to UTC-aware datetime.
    Returns None if date is missing/undated (to prevent inventing fake dates for indicative estimates).
    """
    if raw_date is None or str(raw_date).strip() in ("", "None", "null", "undated"):
        return None

    if isinstance(raw_date, datetime):
        if raw_date.tzinfo is None:
            return raw_date.replace(tzinfo=timezone.utc)
        return raw_date.astimezone(timezone.utc)

    if isinstance(raw_date, date):
        return datetime(raw_date.year, raw_date.month, raw_date.day, 12, 0, 0, tzinfo=timezone.utc)

    if isinstance(raw_date, str):
        clean_str = raw_date.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(clean_str)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            pass

        # Try common Pakistani formats
        for fmt in (
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%d %b %Y",
            "%d %B %Y",
            "%B, %Y",
            "%B %Y",
        ):
            try:
                parsed = datetime.strptime(clean_str, fmt)
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

    raise NormalizationError(f"Unsupported publication date format: '{raw_date}'")
