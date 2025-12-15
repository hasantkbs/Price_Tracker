import re

PRICE_PATTERNS = [
    r"\d{1,3}(?:\.\d{3})*(?:,\d{2})",
    r"\d{1,3}(?:,\d{3})*(?:\.\d{2})",
    r"\d+,\d{2}",
    r"\d+\.\d{2}",
    r"\d+",
]

CURRENCY_SYMBOLS = ["₺", "TL", "TRY", "$", "€", "EUR", "USD"]


def extract_price_from_text(text: str):
    """Serbest metinden fiyat sayısını (float) çıkarır."""
    for symbol in CURRENCY_SYMBOLS:
        text = text.replace(symbol, "")
    text = text.strip()

    for pattern in PRICE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            price_str = match.group(0)
            price_str = price_str.replace(".", "").replace(",", ".")
            try:
                return float(price_str)
            except Exception:
                continue
    return None


