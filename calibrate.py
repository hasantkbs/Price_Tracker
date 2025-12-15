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
]


def close_popups(page):
    """Sayfadaki klasik çerez / popup diyaloglarını kapatmaya çalışır."""
    for selector in POPUP_SELECTORS:
        try:
            page.locator(selector).click(timeout=1500)
        except Exception:
            pass


def fetch_html(url: str) -> str:
    """
    Sayfayı Playwright ile yükler, popupları kapatır ve biraz scroll ederek
    fiyatın DOM'a düşmesini sağlar.
    """
    # 1) Önce Playwright ile tam render etmeyi dene
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
            page = browser.new_page()
            page.set_default_timeout(15000)
            page.goto(url, wait_until="networkidle")

            # popup killer (arka planda)
            close_popups(page)

            # scroll → lazy load fiyatı yukarı taşır
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            page.wait_for_timeout(1500)

            html = page.content()
            browser.close()
            return html
    except Exception:
        # 2) Eğer Playwright yoksa veya browser açılamazsa (özellikle Streamlit Cloud gibi
        # ortamlarda), basit bir requests + BeautifulSoup fallback'i kullan.
        resp = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.text


def get_css_selector(element):
    """Bulunan element için stabil CSS selector üretir."""
    parts = []
    current = element
    while current.parent and current.parent.name != "[document]":
        selector = current.name
        if current.has_attr("id"):
            selector = f"#{current['id']}"
            parts.insert(0, selector)
            break
        if current.has_attr("class"):
            classes = ".".join(current["class"])
            selector = f"{selector}.{classes}"
        siblings = current.find_previous_siblings(current.name)
        selector = f"{selector}:nth-of-type({len(siblings) + 1})"
        parts.insert(0, selector)
        current = current.parent
    return " > ".join(parts)


def _choose_best_element(candidates):
    """
    Birden fazla eşleşen element varsa, kullanıcıya sormadan en mantıklı olanı seç.
    - <head>, <script>, <style> içindekileri geri plana at
    - class'ında 'price' veya 'fiyat' geçenleri öne al
    - Metin uzunluğu kısa olanları tercih et
    """
    def score(el):
        score = 0
        # Etiket adı
        tag_name = el.name.lower() if el.name else ""
        if tag_name in {"span", "strong", "b"}:
            score += 3
        if tag_name in {"div", "p"}:
            score += 1

        # Üst ataları kontrol et (head/script/style içinde mi?)
        in_bad_parent = False
        for parent in el.parents:
            if parent.name in {"head", "script", "style", "noscript"}:
                in_bad_parent = True
                break
        if in_bad_parent:
            score -= 5

        # class ismi
        classes = " ".join(el.get("class", []))
        cls_lower = classes.lower()
        if "price" in cls_lower or "fiyat" in cls_lower:
            score += 5
        if "old-price" in cls_lower or "previous" in cls_lower:
            # Eski fiyatları biraz geri plana it
            score -= 1

        # Metin uzunluğu
        text = el.get_text(strip=True)
        if text:
            length = len(text)
            # Çok uzun metinleri (uzun açıklama) biraz cezalandır
            if length < 30:
                score += 2
            elif length > 80:
                score -= 2
        return score

    best = max(candidates, key=score)
    return best


def calibrate_and_add_product(url: str, price_text: str, target_price: float):
    """
    Verilen URL ve fiyat metni ile sayfayı analiz eder, doğru fiyat elementini
    otomatik bulur ve ürünü veritabanına ekler.

    Streamlit gibi arayüzlerden çağrılabilmesi için input/print yerine
    parametre ve exception kullanır.
    """
    url = url.strip()
    price_text = price_text.strip()

    if not url or not price_text:
        raise ValueError("URL ve fiyat metni boş bırakılamaz.")

    # Kullanıcının girdiği metinden sayısal fiyatı çıkar
    target_price_value = extract_price_from_text(price_text)
    if target_price_value is None:
        raise ValueError(
            "Girdiğiniz metinden fiyat çıkarılamadı. Lütfen sayıyı içeren bir metin girin."
        )

    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    # 1) Önce sınıfında 'price' veya 'price-wrapper' vb. geçen etiketleri tara
    candidate_elements = []
    for tag in soup.find_all(True, class_=True):
        class_str = " ".join(tag.get("class", []))
        if "price" in class_str.lower() or "fiyat" in class_str.lower():
            candidate_elements.append(tag)

    # 2) Eğer orada bulamazsak, genel tüm text node'larda ara (script/style hariç)
    if not candidate_elements:
        for text_node in soup.find_all(string=True):
            parent = text_node.parent
            if parent.name in {"script", "style", "noscript"}:
                continue
            candidate_elements.append(parent)

    # Aynı sayısal fiyatı taşıyan elementleri filtrele
    matches = []
    for el in candidate_elements:
        text = el.get_text(strip=True)
        value = extract_price_from_text(text)
        if value is not None and abs(value - target_price_value) < 0.001:
            matches.append(el)

    if not matches:
        raise RuntimeError(
            "Fiyat metni DOM'da bulunamadı. "
            "Sayfada görünen fiyat ile girilen değer birebir uyuşmuyor olabilir."
        )

    # Kullanıcıya HTML selector seçtirmek yerine, en iyi adayı otomatik seçiyoruz.
    best_element = _choose_best_element(matches)
    selector = get_css_selector(best_element)

    # Verilen target_price string olabilir; burada float'a güvenli şekilde çevir.
    if isinstance(target_price, str):
        target_price = float(target_price.replace(",", "."))

    initial_price = target_price_value

    database.add_product(url, target_price, initial_price, selector)

    return {
        "url": url,
        "selector": selector,
        "initial_price": initial_price,
        "target_price": target_price,
    }


def main():
    """
    Komut satırı üzerinden kullanıcıdan bilgi alır ve kalibrasyon + ekleme yapar.
    """
    database.setup_database()

    url = input("Takip edilecek ürün URL: ").strip()
    price_text = input(
        "Sayfada görünen tam fiyat (örn: 229,99 TL veya sadece 229,99): "
    ).strip()
    target_str = input("Hedef fiyat: ").strip()

    try:
        result = calibrate_and_add_product(url, price_text, target_str)
        print("\n📌 Fiyat elementi otomatik olarak bulundu ve kaydedildi.")
        print(f"URL: {result['url']}")
        print(f"Selector: {result['selector']}")
        print(f"İlk fiyat: {result['initial_price']}")
        print(f"Hedef fiyat: {result['target_price']}")
        print("\n🎉 Ürün başarıyla eklendi ve takip edilmeye başlandı.")
    except Exception as exc:
        print(f"\n❌ İşlem başarısız: {exc}")


if __name__ == "__main__":
    main()
