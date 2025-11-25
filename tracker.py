import time
import re
import requests
from bs4 import BeautifulSoup
import database

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

def get_product_price(url, selector=None):
    """
    Bir ürün sayfasından fiyatı çıkarır. Playwright kullanarak dinamik içerikleri de işler.
    Önce verilen CSS seçiciyi kullanır ve elementin yüklenmesini bekler,
    başarısız olursa veya seçici yoksa genel arama (fallback) yöntemlerini dener.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # 'networkidle' event'ini beklemek, AJAX isteklerinin tamamlanması için daha iyidir.
        page.goto(url, wait_until="networkidle") 
        
        # Eğer özel bir seçici varsa, o elementin yüklenmesini bekle
        if selector:
            try:
                page.locator(selector).wait_for(timeout=10000)
            except Exception:
                print(f"   Uyarı: Kayıtlı seçici '{selector}' 10 saniyede bulunamadı. Sayfa yapısı değişmiş olabilir.")
        else:
            # Genel bir fallback beklemesi
            page.wait_for_timeout(3000)

        html_content = page.content()
        browser.close()

    soup = BeautifulSoup(html_content, "html.parser")

    # --- Strateji 1: Kayıtlı CSS Seçiciyi Kullan ---
    if selector:
        price_element = soup.select_one(selector)
        if price_element:
            price = extract_price_from_text(price_element.get_text(strip=True))
            if price is not None:
                return price
        print(f"   Uyarı: Kayıtlı seçici '{selector}' ile fiyat alınamadı. Fallback denenecek.")

    # --- Fallback Stratejisi: Genel arama ---
    all_candidates = []
    price_tags = soup.find_all(class_=re.compile(r'price', re.IGNORECASE))
    for tag in price_tags:
        text = tag.get_text(strip=True)
        price = extract_price_from_text(text)
        if price:
            all_candidates.append({'price': price, 'text_len': len(text)})
    
    if not all_candidates:
        # Fallback'in de fallback'i: Genel etiketleri ara
        general_tags = soup.find_all(["span", "div", "p", "strong", "b"])
        for tag in general_tags:
            text = tag.get_text(strip=True)
            price = extract_price_from_text(text)
            if price:
                all_candidates.append({'price': price, 'text_len': len(text)})

    if not all_candidates:
        raise ValueError("Sayfada fiyat adayı bulunamadı.")

    # Fiyat adaylarını metin uzunluğuna göre filtrele
    short_text_candidates = [cand['price'] for cand in all_candidates if cand['text_len'] < 30]
    if short_text_candidates:
        return min(short_text_candidates)
    
    # Eğer sadece uzun metinlerde fiyat bulunduysa, en küçük fiyatı döndür
    if all_candidates:
        return min(cand['price'] for cand in all_candidates)

    raise ValueError("Fallback sonrası geçerli fiyat bulunamadı.")


def check_prices():
    """Veritabanındaki tüm ürünlerin fiyatlarını kontrol eder."""
    products = database.get_all_products()
    print(f"Kontrol ediliyor: {len(products)} ürün...")

    for product in products:
        print(f"\n-> {product['url']}")
        try:
            # Ürünün kendine özel bir seçicisi var mı kontrol et
            selector = product['price_selector'] if 'price_selector' in product.keys() else None
            
            current_price = get_product_price(product['url'], selector)
            database.update_product_price(product['id'], current_price)
            print(f"   Mevcut Fiyat: {current_price} (Hedef: {product['target_price']})")

            if current_price <= product['target_price']:
                print("   🔥 FİYAT HEDEFİN ALTINA DÜŞTÜ! 🔥")

        except Exception as e:
            print(f"   Hata: Fiyat alınamadı - {e}")


if __name__ == "__main__":
    database.setup_database()
    print("\nFiyat takip botu başlatıldı. (Çıkmak için CTRL+C)")
    check_interval_minutes = 1 
    while True:
        check_prices()
        print(f"\n---\nSonraki kontrol {check_interval_minutes} dakika sonra.\n---")
        time.sleep(check_interval_minutes * 60)