import re
from typing import Tuple, Optional
from decimal import Decimal

def parse_price_and_unit(raw_str: str, default_unit: str = "metric_ton") -> Tuple[Optional[Decimal], str]:
    """
    Deterministic steel price and unit parser.
    Handles currency prefixes (Rs., PKR, Rs), comma-separated numbers,
    and unit suffixes ('per ton', 'per metric ton', 'per kg', '/ ton', etc.).
    """
    if not raw_str or not raw_str.strip():
        return None, default_unit

    text = raw_str.strip()

    # 1. Detect unit from text
    unit = default_unit
    lower = text.lower()
    if "per kg" in lower or "/kg" in lower or "kg" in lower.split():
        unit = "kg"
    elif "per ton" in lower or "per metric ton" in lower or "/ton" in lower or "tonne" in lower or "ton" in lower.split():
        unit = "metric_ton"

    # 2. Strip currency prefixes and unit suffixes
    # Clean out currency symbols and words
    cleaned = re.sub(r"(?i)\b(rs\.?|pkr|rupees)\b", "", text)
    # Clean out unit phrases
    cleaned = re.sub(r"(?i)\b(per\s+(metric\s+)?ton|per\s+kg|/\s*ton|/\s*kg|metric\s+ton|ton|kg)\b", "", cleaned)
    # Remove commas in numbers (e.g. 223,000 -> 223000)
    cleaned = cleaned.replace(",", "").strip()

    # 3. Extract continuous numeric token (including optional decimal point)
    match = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    if not match:
        return None, unit

    price_dec = Decimal(match.group(1))
    return price_dec, unit

def test_deterministic_parser():
    test_cases = [
        ("Rs. 223,000", Decimal("223000"), "metric_ton"),
        ("PKR 223,000", Decimal("223000"), "metric_ton"),
        ("223000", Decimal("223000"), "metric_ton"),
        ("223,000 per ton", Decimal("223000"), "metric_ton"),
        ("Rs. 223,000 per metric ton", Decimal("223000"), "metric_ton"),
        ("Rs. 257.00 per kg", Decimal("257.00"), "kg"),
        ("PKR 260,500/ton", Decimal("260500"), "metric_ton"),
    ]

    print("=== TESTING DETERMINISTIC STEEL PRICE PARSER ===")
    all_passed = True
    for raw, expected_price, expected_unit in test_cases:
        p, u = parse_price_and_unit(raw)
        passed = (p == expected_price and u == expected_unit)
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] Input: '{raw:30}' -> Price: {p} (Expected: {expected_price}), Unit: '{u}' (Expected: '{expected_unit}')")
        if not passed:
            all_passed = False

    assert all_passed, "Some parser unit tests failed!"
    print("\nALL 7 PARSER UNIT TESTS PASSED DETERMINISTICALLY!")

if __name__ == "__main__":
    test_deterministic_parser()

