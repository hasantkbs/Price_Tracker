"""
Basit komut satırı arayüzü:

- Yeni ürün ekle (kalibrasyon + veritabanına kaydet)
- Tüm ürünlerin fiyatlarını bir kez kontrol et
- Belirli aralıkla sürekli takip başlat
"""

import sys
from typing import Optional

import database
import tracker
import calibrate


def _print_menu() -> None:
    print("\n=== Price Tracker ===")
    print("1) Yeni ürün ekle (URL + mevcut fiyat + hedef fiyat)")
    print("2) Fiyatları şimdi bir kez kontrol et")
    print("3) Sürekli takip başlat")
    print("4) Çık")


def _input_int(prompt: str, default: Optional[int] = None) -> Optional[int]:
    value = input(prompt).strip()
    if not value and default is not None:
        return default
    try:
        return int(value)
    except ValueError:
        print("Lütfen sayısal bir değer girin.")
        return None


def main() -> None:
    database.setup_database()

    while True:
        _print_menu()
        choice = input("\nSeçiminiz: ").strip()

        if choice == "1":
            # Kullanıcıyı kalibrasyon akışına gönder
            calibrate.main()

        elif choice == "2":
            # Mevcut ürünlerin fiyatlarını bir kere kontrol et
            tracker.check_prices()

        elif choice == "3":
            # Sürekli döngülü takip
            interval = None
            while interval is None:
                interval = _input_int(
                    "Dakika cinsinden kontrol aralığı (varsayılan 1): ", default=1
                )
            tracker.run_loop(interval)

        elif choice == "4":
            print("Çıkılıyor...")
            sys.exit(0)

        else:
            print("Geçersiz seçim. Lütfen 1-4 arasında bir seçenek girin.")


if __name__ == "__main__":
    main()