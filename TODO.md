# Proje TODO Listesi

## Mevcut Sorunlar

- **Fiyat Bilgisi Alınamıyor:** Trendyol gibi gelişmiş bot korumasına sahip web sitelerinden fiyat bilgisi çekilemiyor. `requests` ve `playwright` ile yapılan denemeler, sitelerin otomasyonu algılayıp engellediğini gösteriyor. Bu sorunu aşmak için daha gelişmiş anti-bot teknikleri (proxy, CAPTCHA çözümü, daha kapsamlı stealth eklentileri) araştırılmalı.

## Gelecek Planları

- **Mobil Uygulama:** Projenin bir mobil versiyonunun (iOS/Android) geliştirilmesi planlanıyor. Bu uygulama, kullanıcıların takip ettikleri ürünleri ve fiyat değişikliklerini anlık bildirimlerle almasını sağlayacak.
- **Gelişmiş Web Arayüzü:** Kullanıcıların takip ettikleri ürünleri listeleyebileceği, düzenleyebileceği ve geçmiş fiyat verilerini grafiksel olarak görebileceği bir web arayüzü oluşturulabilir.
- **Proxy Entegrasyonu:** Bot engellemelerini aşmak için rotasyonlu proxy servisleri ile entegrasyon yapılabilir.
- **Genişletilmiş Site Desteği:** Farklı e-ticaret siteleri için özel parser'lar geliştirilerek desteklenen site sayısı artırılabilir.
