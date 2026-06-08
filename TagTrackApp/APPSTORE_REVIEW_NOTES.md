# App Store Review Notes (kopyala-yapıştır)

Aşağıdaki metni App Store Connect → App Review Information → **Notes** alanına yapıştırın.

---

## Test hesabı

Hesap gerekmez. Uygulama tamamen yerel çalışır; kayıt veya giriş yoktur.

## Test adımları

1. Uygulamayı açın → splash ekranı → boş ürün listesi görünür.
2. Sağ üst **+** → bir e-ticaret ürün URL'si girin (örnek aşağıda).
3. **Fiyatı Otomatik Çek** → fiyat gelir → hedef fiyat girin → **Kaydet**.
4. Listede ürün görünür; sola kaydırarak **Kontrol Et** ile fiyat yenilenir.
5. **Ayarlar** sekmesi → bildirim toggle, kontrol aralığı, Premium (sandbox), gizlilik linkleri.

## Örnek test URL

Güncel bir ürün sayfası URL'si kullanın, örneğin Trendyol veya Hepsiburada ürün linki.

## App Transport Security (NSAllowsArbitraryLoads)

Uygulama, kullanıcının **manuel olarak eklediği** e-ticaret URL'lerinden fiyat bilgisi çeker. Hangi domain'in ekleneceği önceden bilinemediği için geniş ATS istisnası gereklidir. Kullanıcı kimlik bilgisi veya özel veri toplanmaz; yalnızca herkese açık ürün sayfası HTML'i okunur.

## Background modes (fetch / processing)

Kullanıcının ayarladığı aralıkta (1–24 saat) arka planda fiyat kontrolü yapılır; hedef fiyata ulaşıldığında yerel bildirim gönderilir. `BGTaskScheduler` identifier: `com.algorix.pricetracker.pricecheck`.

## Web scraping ve katma değer (Guideline 4.2.5)

Uygulama yalnızca URL kopyalama değil; çok katmanlı fiyat çıkarma (JSON-LD, meta, microdata, HTML), fiyat geçmişi, hedef fiyat alarmı ve bildirim sunar. İçerik kataloğu biz sağlamayız; kullanıcı kendi takip ettiği ürünleri ekler.

## Reklamlar ve ATT

AdMob kullanılmaktadır. App Tracking Transparency izni, reklam kişiselleştirmesi için uygulama aktif olduğunda istenir. Premium satın alımında reklamlar kapatılır.

## In-App Purchase (sandbox)

Product ID: `com.algorix.pricetracker.premium` (Non-Consumable). Sandbox test hesabı ile Ayarlar → Premium satın alma test edilebilir.

---
