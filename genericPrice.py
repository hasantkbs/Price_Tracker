import time
import re
import requests
from bs4 import BeautifulSoup

PRICE_PATTERNS = [
    r"\d{1,3}(?:\.\d{3})*(?:,\d{2})",
    r"\d{1,3}(?:,\d{3})*(?:\.\d{2})",
    r"\d+,\d{2}",
    r"\d+\.\d{2}",
    r"\d+",
]

CURRENCY_SYMBOLS = ["₺", "TL", "TRY", "$", "€", "EUR", "USD"]

def extract_price_from_text(text):
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
            except:
                continue
    return None

def get_product_price(url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    resp = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")

    candidates = []

    for tag in soup.find_all(["span", "div", "p", "strong", "b"]):
        text = tag.get_text(strip=True)
        price = extract_price_from_text(text)
        if price:
            candidates.append(price)

    if not candidates:
        raise ValueError("Sayfada fiyat bulunamadı.")

    return min(candidates)


if __name__ == "__main__":
    url = input("Ürün linkini girin: ")
    target_price = float(input("Hedef fiyatı girin: "))

    print("\nTakip başlatıldı...\n")

    while True:
        try:
            current_price = get_product_price(url)
            print(f"Mevcut fiyat: {current_price}")

            if current_price <= target_price:
                print("\n🔥 FİYAT HEDEFİN ALTINA DÜŞTÜ! 🔥")
                print(f"👉 Ürün hedef fiyata ulaştı: {current_price}")
                break

        except Exception as e:
            print("Hata:", e)

        time.sleep(60)  # 60 saniyede bir kontrol (istersen artırabiliriz)