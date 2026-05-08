"""
tracker.py — Çok katmanlı fiyat çekme motoru.

Strateji öncelik sırası:
  1. CSS Selector  (kalibrasyon sırasında kaydedilen)
  2. JSON-LD       (application/ld+json structured data)
  3. Meta Tags     (og:price, product:price:amount vb.)
  4. Microdata     (itemprop="price")
  5. Class Search  (class'ında "price"/"fiyat" geçen elementler)
  6. General       (tüm kısa text node'lar)

Selector 3 kez üst üste başarısız olursa "stale" işaretlenir;
sonraki kontrollerde diğer stratejiler ön plana geçer.
"""

import json
import re
import time

from bs4 import BeautifulSoup

import database
from calibrate import fetch_html, calibrate_and_add_product
from price_utils import extract_price_from_text

# Seçici kaç kez üst üste başarısız olursa stale sayılır
SELECTOR_STALE_THRESHOLD = 3

# Fiyat mantık kontrolü: initial_price'ın kaç katına kadar kabul edilir
PRICE_SANITY_FACTOR = 10.0


# ── Strateji fonksiyonları ────────────────────────────────────────────────────

def _try_selector(soup: BeautifulSoup, selector: str):
    try:
        el = soup.select_one(selector)
        if el:
            return extract_price_from_text(el.get_text(strip=True))
    except Exception:
        pass
    return None


def _try_json_ld(soup: BeautifulSoup):
    """
    <script type="application/ld+json"> içindeki Product/Offer fiyatını çeker.
    Trendyol, Hepsiburada, Amazon gibi sitelerde çok güvenilir.
    """
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue

        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            price = _extract_ld_price(node)
            if price is not None:
                return price
    return None


def _extract_ld_price(node):
    if not isinstance(node, dict):
        return None

    type_str = str(node.get("@type", "")).lower()

    # Offer / AggregateOffer
    if type_str in {"offer", "aggregateoffer"}:
        raw = node.get("price") or node.get("lowPrice")
        if raw is not None:
            return extract_price_from_text(str(raw))

    # Product → offers
    if type_str == "product":
        offers = node.get("offers")
        if isinstance(offers, dict):
            p = _extract_ld_price(offers)
            if p is not None:
                return p
        if isinstance(offers, list):
            prices = [_extract_ld_price(o) for o in offers if isinstance(o, dict)]
            prices = [p for p in prices if p is not None]
            if prices:
                return min(prices)

    # Graph içindeki tüm node'ları dene
    for val in node.values():
        if isinstance(val, (dict, list)):
            inner = val if isinstance(val, list) else [val]
            for item in inner:
                p = _extract_ld_price(item)
                if p is not None:
                    return p
    return None


def _try_meta_tags(soup: BeautifulSoup):
    """og:price:amount, product:price:amount, twitter:data1 gibi meta etiketleri."""
    candidates = [
        ("meta", {"property": "product:price:amount"}),
        ("meta", {"property": "og:price:amount"}),
        ("meta", {"name": "twitter:data1"}),
        ("meta", {"itemprop": "price"}),
    ]
    for tag_name, attrs in candidates:
        el = soup.find(tag_name, attrs=attrs)
        if el:
            content = el.get("content", "")
            price = extract_price_from_text(str(content))
            if price is not None:
                return price
    return None


def _try_microdata(soup: BeautifulSoup):
    """itemprop="price" veya itemprop="lowPrice" attribute'larını tarar."""
    for attr in ("price", "lowPrice"):
        el = soup.find(attrs={"itemprop": attr})
        if el:
            content = el.get("content") or el.get_text(strip=True)
            price = extract_price_from_text(str(content))
            if price is not None:
                return price
    return None


def _try_class_search(soup: BeautifulSoup):
    """class adında 'price' veya 'fiyat' geçen, kısa metinli elementleri tarar."""
    candidates = []
    for el in soup.find_all(True, class_=True):
        cls = " ".join(el.get("class", [])).lower()
        if not ("price" in cls or "fiyat" in cls):
            continue
        if any(bad in cls for bad in ("old", "original", "previous", "crossed", "before")):
            continue
        text = el.get_text(strip=True)
        price = extract_price_from_text(text)
        if price and len(text) < 40:
            candidates.append(price)
    return min(candidates) if candidates else None


def _try_general(soup: BeautifulSoup):
    """Tüm kısa text node'lardan en küçük makul fiyatı döndürür."""
    candidates = []
    for el in soup.find_all(["span", "div", "p", "strong", "b", "td"]):
        if el.find(["div", "span", "p"]):
            continue
        text = el.get_text(strip=True)
        if len(text) > 35:
            continue
        price = extract_price_from_text(text)
        if price:
            candidates.append(price)
    return min(candidates) if candidates else None


# ── Fiyat doğrulama ───────────────────────────────────────────────────────────

def _is_sane(price: float, initial_price: float | None) -> bool:
    """Fiyat, başlangıç fiyatının mantıklı bir katındaysa True döner."""
    if initial_price is None or initial_price <= 0:
        return price > 0
    ratio = price / initial_price
    return (1 / PRICE_SANITY_FACTOR) <= ratio <= PRICE_SANITY_FACTOR


def _pick_best(results: dict, initial_price: float | None) -> tuple[float, str]:
    """
    Strateji sonuçları arasından en güveniliri seç.
    Önce tüm sonuçların doğrulanmış olanlarını birbirine yakınlık açısından karşılaştır.
    """
    priority = ["selector", "json_ld", "meta_tags", "microdata", "class_search", "general"]
    sane = {k: v for k, v in results.items() if _is_sane(v, initial_price)}

    if not sane:
        # Sanity check geçilemeyen sonuçlar da yoksa tüm sonuçlara bak
        sane = results

    if not sane:
        raise ValueError("Hiçbir strateji geçerli fiyat bulamadı.")

    # Birden fazla strateji varsa ve hepsi birbirine yakınsa en öncelikliyi döndür
    values = list(sane.values())
    avg = sum(values) / len(values)
    consistent = {k: v for k, v in sane.items() if abs(v - avg) / (avg or 1) < 0.15}

    pool = consistent if len(consistent) >= 2 else sane

    for key in priority:
        if key in pool:
            return pool[key], key

    key = next(iter(pool))
    return pool[key], key


# ── Ana fiyat çekme fonksiyonu ────────────────────────────────────────────────

def get_product_price(url: str, selector: str | None = None,
                      initial_price: float | None = None) -> tuple[float, str]:
    """
    URL'den fiyat çeker. Tüm stratejileri dener, en güvenilir sonucu döndürür.
    Returns: (price, source_strategy)
    """
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    results: dict[str, float] = {}

    # 1. JSON-LD (en güvenilir, siteye özel değil)
    p = _try_json_ld(soup)
    if p: results["json_ld"] = p

    # 2. Meta tags
    p = _try_meta_tags(soup)
    if p: results["meta_tags"] = p

    # 3. Microdata
    p = _try_microdata(soup)
    if p: results["microdata"] = p

    # 4. CSS Selector (kalibrasyondan gelen)
    if selector:
        p = _try_selector(soup, selector)
        if p:
            results["selector"] = p

    # 5. Class-based search
    p = _try_class_search(soup)
    if p: results["class_search"] = p

    # 6. Genel arama (son çare)
    if not results:
        p = _try_general(soup)
        if p: results["general"] = p

    if not results:
        raise ValueError("Sayfada hiçbir stratejiyle fiyat bulunamadı.")

    return _pick_best(results, initial_price)


# ── Toplu fiyat kontrol ───────────────────────────────────────────────────────

def check_prices():
    products = database.get_all_products()
    print(f"\nKontrol ediliyor: {len(products)} ürün...")

    for product in products:
        pid = product["id"]
        url = product["url"]
        selector = product["price_selector"]
        fail_count = product["selector_fail_count"] or 0
        initial = product["initial_price"]

        # Seçici stale ise bu turda kullanma
        active_selector = None if fail_count >= SELECTOR_STALE_THRESHOLD else selector

        print(f"\n[{pid}] {product.get('name') or url[:60]}")
        if fail_count >= SELECTOR_STALE_THRESHOLD:
            print(f"   ⚠ Seçici stale ({fail_count} başarısız) — diğer stratejiler kullanılacak.")

        try:
            price, source = get_product_price(url, active_selector, initial)
            database.update_product_price(pid, price, source)
            database.add_price_history(pid, price, source)
            print(f"   Fiyat: {price} TL  [kaynak: {source}]")
            print(f"   Hedef: {product['target_price']} TL")

            if selector and active_selector:
                pass  # seçici çalışıyorsa fail_count 0'a sıfırlanır (update_product_price içinde)
            elif selector and not active_selector:
                print("   (stale seçici atlandı, fallback kullanıldı)")

            if price <= product["target_price"]:
                print("   HEDEF FIYATA ULASTI!")

            if product["alert_enabled"] and product["alert_price"] and price <= product["alert_price"]:
                print(f"   ALARM TETIKLENDI! {price} <= {product['alert_price']}")

        except Exception as exc:
            database.record_selector_failure(pid, str(exc))
            print(f"   HATA: {exc}")


def run_loop(check_interval_minutes: int = 30):
    database.setup_database()
    print("Fiyat takip botu başlatıldı. (Çıkmak için CTRL+C)")
    while True:
        check_prices()
        print(f"\n--- Sonraki kontrol {check_interval_minutes} dakika sonra. ---\n")
        time.sleep(check_interval_minutes * 60)


if __name__ == "__main__":
    run_loop()
