import database
from bs4 import BeautifulSoup
from tracker import extract_price_from_text
from playwright.sync_api import sync_playwright


POPUP_SELECTORS = [
    "button:has-text('Kabul Et')",
    "button:has-text('Kapat')",
    "button:has-text('Tamam')",
    "button:has-text('X')",
    "[class*='close']",
    "[class*='modal-close']"
]


def close_popups(page):
    for selector in POPUP_SELECTORS:
        try:
            page.locator(selector).click(timeout=1500)
        except:
            pass


def fetch_html(url: str) -> str:
    """Trendyol gibi sitelerde popupları kapatarak fiyatın DOM'a düşmesini sağlar."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # kullanıcı pencere görmez
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1920,1080"
            ]
        )
        page = browser.new_page()
        page.set_default_timeout(15000)
        page.goto(url, wait_until="networkidle")

        # popup killer (arka planda)
        close_popups(page)

        # scroll → lazy load fiyatı yukarı taşır
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        page.wait_for_timeout(1500)

        # Trendyol fiyat class'ları
        price_candidates = [
            "span[class*='prc-dsc']",   # indirimli fiyat
            "span[class*='prc-org']",   # indirimsiz fiyat
            "span[class*='selling-price']",
            "span[class*='product-price']"
        ]

        html = None
        for selector in price_candidates:
            try:
                page.wait_for_selector(selector, timeout=8000)
                html = page.content()
                break
            except:
                pass

        if html is None:
            html = page.content()

        browser.close()
        return html


def get_css_selector(element):
    """Bulunan element için stabil CSS selector üretir."""
    parts = []
    current = element
    while current.parent and current.parent.name != '[document]':
        selector = current.name
        if current.has_attr('id'):
            selector = f"#{current['id']}"
            parts.insert(0, selector)
            break
        if current.has_attr('class'):
            classes = ".".join(current['class'])
            selector = f"{selector}.{classes}"
        siblings = current.find_previous_siblings(current.name)
        selector = f"{selector}:nth-of-type({len(siblings) + 1})"
        parts.insert(0, selector)
        current = current.parent
    return " > ".join(parts)


def main():
    database.setup_database()

    url = input("Takip edilecek ürün URL: ").strip()
    price_text = input("Sayfada görünen tam fiyat: ").strip()

    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    matches = soup.find_all(string=lambda t: price_text in t)
    if not matches:
        print("\n❌ Fiyat metni DOM'da bulunamadı.")
        print("Sebep: Kullanıcının girdiği fiyat sayfada birebir farklı olabilir.")
        print("Yardım: İşaretle → kopyala yapıştır yöntemi ile fiyatı tekrar ekle.")
        return

    selectors = [get_css_selector(el.parent) for el in matches]
    print("\n📌 Fiyat konumu:")
    for i, sel in enumerate(selectors, 1):
        print(f"{i}. {sel}")

    index = int(input("\nDoğru olan numara: ")) - 1
    selector = selectors[index]

    target_price = float(input("Hedef fiyat: "))
    initial_price = extract_price_from_text(price_text)

    database.add_product(url, target_price, initial_price, selector)
    print("\n🎉 Ürün başarıyla eklendi ve takip edilmeye başlandı.")


if __name__ == "__main__":
    main()
