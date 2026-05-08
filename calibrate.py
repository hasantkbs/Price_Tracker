"""
calibrate.py — Sayfa analizi, CSS seçici tespiti ve yeniden kalibrasyon.
"""

import database
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from price_utils import extract_price_from_text


POPUP_SELECTORS = [
    "button:has-text('Kabul Et')",
    "button:has-text('Kapat')",
    "button:has-text('Tamam')",
    "button:has-text('X')",
    "[class*='close']",
    "[class*='modal-close']",
    "[id*='cookie'] button",
    "[class*='cookie'] button",
]


def close_popups(page):
    for selector in POPUP_SELECTORS:
        try:
            page.locator(selector).click(timeout=1500)
        except Exception:
            pass


def fetch_html(url: str) -> str:
    """
    Playwright ile tam render; başarısız olursa requests fallback.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--window-size=1920,1080",
                ],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
            )
            page = context.new_page()
            page.set_default_timeout(20000)
            page.goto(url, wait_until="networkidle")
            close_popups(page)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
            page.wait_for_timeout(1500)
            html = page.content()
            browser.close()
            return html
    except Exception:
        resp = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            },
            timeout=20,
        )
        resp.raise_for_status()
        return resp.text


def get_css_selector(element) -> str:
    """Element için stabil CSS selector üretir. ID bulursa kısa yol keser."""
    parts = []
    current = element
    while current.parent and current.parent.name != "[document]":
        if current.has_attr("id"):
            parts.insert(0, f"#{current['id']}")
            break
        tag = current.name
        if current.has_attr("class"):
            classes = ".".join(c for c in current["class"] if c)
            tag = f"{tag}.{classes}"
        siblings = current.find_previous_siblings(current.name)
        tag = f"{tag}:nth-of-type({len(siblings) + 1})"
        parts.insert(0, tag)
        current = current.parent
    return " > ".join(parts)


def _score_element(el) -> int:
    score = 0
    tag = (el.name or "").lower()

    if tag in {"span", "strong", "b", "em"}:
        score += 3
    elif tag in {"div", "p"}:
        score += 1

    for parent in el.parents:
        if parent.name in {"head", "script", "style", "noscript"}:
            score -= 10
            break

    cls = " ".join(el.get("class", [])).lower()
    if "price" in cls or "fiyat" in cls:
        score += 5
    if any(bad in cls for bad in ("old", "original", "previous", "crossed", "before", "strike")):
        score -= 3

    text = el.get_text(strip=True)
    length = len(text)
    if 0 < length < 25:
        score += 3
    elif length < 40:
        score += 1
    elif length > 80:
        score -= 2

    return score


def _find_best_match(soup: BeautifulSoup, target_value: float):
    """
    Sayfada target_value'ya en yakın fiyatı taşıyan elementi bulur.
    Tam eşleşme → öncelikli; ±%5 tolerans → kabul edilir.
    """
    candidate_elements = []

    # 1. Önce price/fiyat class'lı elementler
    for el in soup.find_all(True, class_=True):
        cls = " ".join(el.get("class", [])).lower()
        if "price" in cls or "fiyat" in cls:
            candidate_elements.append(el)

    # 2. Yoksa tüm text node parent'ları
    if not candidate_elements:
        for node in soup.find_all(string=True):
            parent = node.parent
            if parent and parent.name not in {"script", "style", "noscript"}:
                candidate_elements.append(parent)

    exact, close = [], []
    for el in candidate_elements:
        text = el.get_text(strip=True)
        val = extract_price_from_text(text)
        if val is None:
            continue
        if abs(val - target_value) < 0.01:
            exact.append(el)
        elif abs(val - target_value) / (target_value or 1) < 0.05:
            close.append(el)

    pool = exact if exact else close
    if not pool:
        raise RuntimeError(
            f"'{target_value}' fiyatı DOM'da bulunamadı. "
            "Sayfadaki fiyat ile girilen değer uyuşmuyor olabilir."
        )
    return max(pool, key=_score_element)


def calibrate_and_add_product(user_id: str, url: str, price_text: str,
                               target_price: float, name: str | None = None) -> dict:
    """
    URL kalibre eder, CSS seçiciyi bulur ve ürünü veritabanına ekler.
    """
    url = url.strip()
    price_text = price_text.strip()

    if not url or not price_text:
        raise ValueError("URL ve fiyat metni boş bırakılamaz.")

    initial_value = extract_price_from_text(price_text)
    if initial_value is None:
        raise ValueError("Girilen metinden fiyat çıkarılamadı.")

    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    best = _find_best_match(soup, initial_value)
    selector = get_css_selector(best)

    if isinstance(target_price, str):
        target_price = float(target_price.replace(",", "."))

    database.add_product(user_id, url, target_price, initial_value, selector, name=name)

    return {
        "url": url,
        "name": name,
        "selector": selector,
        "initial_price": initial_value,
        "target_price": target_price,
    }


def recalibrate_product(product_id: int, user_id: str, current_price_text: str) -> dict:
    """
    Mevcut bir ürünün CSS seçicisini yeniler.
    Kullanıcı sayfada gördüğü güncel fiyatı girer; sistem yeni seçiciyi bulur ve kaydeder.
    """
    product = database.get_product_by_id(product_id, user_id)
    if not product:
        raise ValueError(f"Ürün bulunamadı: {product_id}")

    current_value = extract_price_from_text(current_price_text.strip())
    if current_value is None:
        raise ValueError("Girilen metinden fiyat çıkarılamadı.")

    html = fetch_html(product["url"])
    soup = BeautifulSoup(html, "html.parser")

    best = _find_best_match(soup, current_value)
    new_selector = get_css_selector(best)

    database.update_product_selector(product_id, new_selector)

    return {
        "product_id": product_id,
        "new_selector": new_selector,
        "detected_price": current_value,
    }


def main():
    database.setup_database()
    url = input("Takip edilecek ürün URL: ").strip()
    name = input("Ürün adı (opsiyonel): ").strip() or None
    price_text = input("Sayfada görünen fiyat (örn: 1.299,00 TL): ").strip()
    target_str = input("Hedef fiyat: ").strip()

    try:
        result = calibrate_and_add_product(url, price_text, target_str, name=name)
        print(f"\nSelector: {result['selector']}")
        print(f"İlk fiyat: {result['initial_price']}")
        print(f"Hedef: {result['target_price']}")
        print("Ürün başarıyla eklendi.")
    except Exception as exc:
        print(f"\nHata: {exc}")


if __name__ == "__main__":
    main()
