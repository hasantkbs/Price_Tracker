import time
import re
import requests
from bs4 import BeautifulSoup
import database
from calibrate import fetch_html
from price_utils import extract_price_from_text
from calibrate import fetch_html

def get_product_price(url, selector=None):
    """
    Bir ürün sayfasından fiyatı çıkarır.
    Kalibrasyonla aynı Playwright akışını kullanarak (popup kapatma, scroll vb.)
    HTML içerik alınıp, önce kayıtlı CSS seçici, sonra genel fallback denenir.
    """
    # Sayfayı, kalibrasyon tarafındaki ile aynı mantıkla getir.
    html_content = fetch_html(url)
    soup = BeautifulSoup(html_content, "html.parser")

    # --- Strateji 1: Kayıtlı CSS Seçiciyi Kullan ---
    if selector:
        price_element = soup.select_one(selector)
        if price_element:
            price = extract_price_from_text(price_element.get_text(strip=True))
            if price is not None:
                return price
        print(
            f"   Uyarı: Kayıtlı seçici '{selector}' ile fiyat alınamadı. "
            "Fallback denenecek."
        )

    # --- Fallback Stratejisi: Genel arama ---
    all_candidates = []
    price_tags = soup.find_all(class_=re.compile(r"price", re.IGNORECASE))
    for tag in price_tags:
        text = tag.get_text(strip=True)
        price = extract_price_from_text(text)
        if price:
            all_candidates.append({"price": price, "text_len": len(text)})

    if not all_candidates:
        # Fallback'in de fallback'i: Genel etiketleri ara
        general_tags = soup.find_all(["span", "div", "p", "strong", "b"])
        for tag in general_tags:
            text = tag.get_text(strip=True)
            price = extract_price_from_text(text)
            if price:
                all_candidates.append({"price": price, "text_len": len(text)})

    if not all_candidates:
        raise ValueError("Sayfada fiyat adayı bulunamadı.")

    # Fiyat adaylarını metin uzunluğuna göre filtrele
    short_text_candidates = [
        cand["price"] for cand in all_candidates if cand["text_len"] < 30
    ]
    if short_text_candidates:
        return min(short_text_candidates)

    # Eğer sadece uzun metinlerde fiyat bulunduysa, en küçük fiyatı döndür
    if all_candidates:
        return min(cand["price"] for cand in all_candidates)

    raise ValueError("Fallback sonrası geçerli fiyat bulunamadı.")


def check_prices():
    """Veritabanındaki tüm ürünlerin fiyatlarını kontrol eder."""
    products = database.get_all_products()
    print(f"Kontrol ediliyor: {len(products)} ürün...")

    for product in products:
        print(f"\n-> {product['url']}")
        try:
            # Ürünün kendine özel bir seçicisi var mı kontrol et
            selector = product["price_selector"] if "price_selector" in product.keys() else None

            current_price = get_product_price(product["url"], selector)
            database.update_product_price(product["id"], current_price)
            print(
                f"   Mevcut Fiyat: {current_price} "
                f"(Hedef: {product['target_price']})"
            )

            if current_price <= product["target_price"]:
                print("   🔥 FİYAT HEDEFİN ALTINA DÜŞTÜ! 🔥")

        except Exception as e:
            print(f"   Hata: Fiyat alınamadı - {e}")


def run_loop(check_interval_minutes: int = 1):
    """Belirtilen aralıkla sürekli fiyat kontrol döngüsü çalıştırır."""
    database.setup_database()
    print("\nFiyat takip botu başlatıldı. (Çıkmak için CTRL+C)")
    while True:
        check_prices()
        print(
            f"\n---\nSonraki kontrol {check_interval_minutes} dakika sonra.\n---"
        )
        time.sleep(check_interval_minutes * 60)


if __name__ == "__main__":
    run_loop()