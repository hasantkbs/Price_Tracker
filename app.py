import database
import requests
from bs4 import BeautifulSoup
from tracker import extract_price_from_text

def get_css_selector(element):
    """
    Verilen bir BeautifulSoup elementi için olabildiğince stabil bir CSS seçici üretir.
    Önce ID, sonra class'ları kullanır.
    """
    parts = []
    current = element
    while current.parent and current.parent.name != '[document]':
        selector = current.name
        if current.has_attr('id'):
            # ID varsa, bu tek başına yeterince spesifiktir.
            selector = f"#{current['id']}"
            parts.insert(0, selector)
            break # Döngüyü kır, çünkü ID'den daha spesifik bir şeye gerek yok. 
        
        if current.has_attr('class'):
            classes = ".".join(c for c in current['class'] if c)
            if classes:
                selector = f"{selector}.{classes}"
        
        # Kendi türündeki kaçıncı çocuk olduğunu bul (daha stabil hale getirir)
        siblings = current.find_previous_siblings(current.name)
        nth = len(siblings) + 1
        selector = f"{selector}:nth-of-type({nth})"

        parts.insert(0, selector)
        current = current.parent
        
    return " > ".join(parts)


def main():
    """Ana kalibrasyon ve ürün ekleme uygulaması."""
    database.setup_database()

    url = input("Takip edilecek ürünün URL'sini girin: ")
    if not url:
        return

    price_text = input("Sayfada görünen tam fiyat metnini girin (örn: 229,99 TL): ")
    if not price_text:
        return
        
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")
            
            # Belirtilen metni içeren elementin yüklenmesini bekle (daha güvenilir)
            try:
                page.locator(f'text="{price_text}"').wait_for(timeout=10000) # 10 saniye bekle
            except Exception as e:
                print(f"\nHata: Sayfada '{price_text}' metni 10 saniye içinde bulunamadı.")
                print("Sayfa yavaş yükleniyor olabilir veya metin yanlış olabilir.")
                browser.close()
                return

            html_content = page.content()
            browser.close()

        soup = BeautifulSoup(html_content, "html.parser")

        elements = soup.find_all(string=price_text)
        
        if not elements:
            print("\n--------------------\nHATA\n--------------------")
            print("Belirtilen fiyat metni sayfada bulunamadı.")
            print("İpucu: Tarayıcınızdaki 'İncele' (Inspect) özelliğini kullanarak metnin doğru olduğundan emin olun.")
            return

        print("\nFiyat metni şu HTML konumlarında bulundu:")
        selectors = [get_css_selector(el.parent) for el in elements]
        
        if not selectors:
            print("Bulunan elementler için seçici üretilemedi.")
            return

        for i, sel in enumerate(selectors, 1):
            print(f"\n{i}. {sel}")
        
        chosen_selector = None
        while chosen_selector is None:
            choice_str = input(f"\nLütfen yukarıdaki listeden doğru olanın numarasını girin (1-{len(selectors)}): ")
            try:
                choice = int(choice_str) - 1
                if 0 <= choice < len(selectors):
                    chosen_selector = selectors[choice]
                else:
                    print(f"Geçersiz numara. Lütfen 1 ile {len(selectors)} arasında bir sayı girin.")
            except ValueError:
                print("Geçersiz giriş. Lütfen sadece bir sayı girin.")

        print(f"\nSeçiminiz kaydedildi:\n-> {chosen_selector}")

        target_price_str = input("Hedef fiyatı girin: ")
        target_price = float(target_price_str)
        
        initial_price = extract_price_from_text(price_text)
        if initial_price is None:
            print("Girdiğiniz metinden fiyat çıkarılamadı.")
            return

        database.add_product(url, target_price, initial_price, chosen_selector)

    except requests.exceptions.RequestException as e:
        print(f"Hata: Sayfa alınamadı. {e}")
    except (ValueError, IndexError):
        print("Geçersiz giriş. Lütfen sayısal bir değer girin.")
    except Exception as e:
        print(f"Beklenmedik bir hata oluştu: {e}")

if __name__ == "__main__":
    main()