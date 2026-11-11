import re
from typing import Tuple, Optional
from decimal import Decimal

def deterministic_parse_price_and_unit(raw_str: str) -> Tuple[Optional[Decimal], Optional[str]]:
    """
    Deterministic steel price and unit parser for SteelRateToday.
    - Accurately identifies currency tokens (Rs., PKR, Rupees).
    - Distinguishes bar dimensions (e.g., '12mm', '3/8 inch', '4 sutar') from monetary prices.
    - Detects explicit units ('per ton', 'per metric ton', '/ton', 'per kg', '/kg').
    - Returns unit=None when unit is not established in the raw text (NO silent defaulting).
    """
    if not raw_str or not raw_str.strip():
        return None, None

    text = raw_str.strip()
    lower = text.lower()

    # 1. Detect unit explicitly
    unit: Optional[str] = None
    if re.search(r"\b(per\s+kg|/\s*kg|\bkg\b)", lower):
        unit = "kg"
    elif re.search(r"\b(per\s+(metric\s+)?ton|/\s*ton|/\s*tonne|\btonne\b|\bton\b)", lower):
        unit = "metric_ton"

    # 2. Separate dimensions/specifications (e.g. '12mm', '4 sutar') from price
    # Replace dimension tokens like '12mm', '10 mm', '4 sutar', 'Grade 60', 'Grade 40' with whitespace
    cleaned = re.sub(r"(?i)\bgrade\s*\d+\b", " ", text)
    cleaned = re.sub(r"(?i)\b\d+(\.\d+)?\s*(mm|sutar|inch|\"|meter|m)\b", " ", cleaned)

    # 3. Look for currency-anchored price: e.g. "Rs. 223,000", "PKR 250,000", "Rs 257.00"
    currency_match = re.search(r"(?i)(?:rs\.?|pkr|rupees)\s*[:.]?\s*([\d,]+(?:\.\d+)?)", cleaned)
    if currency_match:
        price_str = currency_match.group(1).replace(",", "").strip()
        try:
            return Decimal(price_str), unit
        except Exception:
            pass

    # 4. If no currency prefix, find largest monetary number (> 1000 or with commas)
    # Remove unit phrases
    cleaned = re.sub(r"(?i)\b(per\s+(metric\s+)?ton|per\s+kg|/\s*ton|/\s*kg|metric\s+ton|ton|kg)\b", " ", cleaned)
    numbers = re.findall(r"[\d,]+(?:\.\d+)?", cleaned)
    valid_numbers = []
    for n in numbers:
        n_clean = n.replace(",", "").strip()
        if n_clean:
            try:
                val = Decimal(n_clean)
                valid_numbers.append(val)
            except Exception:
                pass

    if not valid_numbers:
        return None, unit

    # If multiple numbers exist, the price is the largest number (e.g., 223000 vs size 12)
    price = max(valid_numbers)
    return price, unit


def run_tests():
    test_cases = [
        ("Rs. 223,000", Decimal("223000"), None),
        ("PKR 223,000", Decimal("223000"), None),
        ("223000", Decimal("223000"), None),
        ("223,000 per ton", Decimal("223000"), "metric_ton"),
        ("Rs. 257.00 per kg", Decimal("257.00"), "kg"),
        ("Grade 60, 12mm, Rs. 223,000 per ton", Decimal("223000"), "metric_ton"),
        ("Grade 40, 12mm, PKR 250,000/ton", Decimal("250000"), "metric_ton"),
        ("Unknown unit steel rate 245000", Decimal("245000"), None),
        ("12mm rebar Rs. 260,000 per ton", Decimal("260000"), "metric_ton"),
    ]

    print("=== TASK 7 PARSER TESTS ===")
    all_passed = True
    for raw, exp_p, exp_u in test_cases:
        p, u = deterministic_parse_price_and_unit(raw)
        passed = (p == exp_p and u == exp_u)
        print(f"[{'PASS' if passed else 'FAIL'}] '{raw}' -> Price: {p} (Exp: {exp_p}), Unit: {u} (Exp: {exp_u})")
        if not passed:
            all_passed = False

    assert all_passed, "Test cases failed"
    print("\nALL TASK 7 PARSER TEST CASES PASSED PERFECTLY!")

if __name__ == "__main__":
    run_tests()

