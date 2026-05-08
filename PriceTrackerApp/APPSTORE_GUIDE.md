# App Store Yayımlama Rehberi — Fiyat Takibi

Bu dosya, uygulamayı App Store'a göndermek için yapmanız gereken tüm adımları listeler.
**Kodda eksik kalan tek şey: uygulama logosu ve tam adı.**

---

## İçindekiler

1. [Ön Koşullar](#1-ön-koşullar)
2. [Uygulama Adı ve Bundle ID](#2-uygulama-adı-ve-bundle-id)
3. [Uygulama Logosu](#3-uygulama-logosu)
4. [AdMob Kurulumu](#4-admob-kurulumu)
5. [In-App Purchase (Premium)](#5-in-app-purchase-premium)
6. [Signing & Capabilities](#6-signing--capabilities)
7. [App Store Connect — Uygulama Kaydı](#7-app-store-connect--uygulama-kaydı)
8. [Ekran Görüntüleri](#8-ekran-görüntüleri)
9. [Build, Archive & Submit](#9-build-archive--submit)
10. [İnceleme Notları](#10-i̇nceleme-notları)

---

## 1. Ön Koşullar

| Gereksinim | Nereden | Ücret |
|---|---|---|
| Apple Developer Program | developer.apple.com/programs | $99/yıl |
| AdMob hesabı | admob.google.com | Ücretsiz |
| Uygulama ikonu | Kendiniz tasarlayın (1024×1024 PNG) | — |
| Gizlilik Politikası URL | Bir URL oluşturun (zorunlu) | — |

---

## 2. Uygulama Adı ve Bundle ID

### Xcode'da değiştirin:

1. `PriceTrackerApp/project.yml` dosyasını açın
2. Aşağıdaki satırları güncelleyin:

```yaml
settings:
  base:
    PRODUCT_DISPLAY_NAME: "Uygulamanızın Adı"        # görünen isim
    PRODUCT_BUNDLE_IDENTIFIER: com.SIRKETINIZ.UYGULAMANIZ  # eşsiz olmalı
```

3. Sonra projeyi yeniden oluşturun:

```bash
cd PriceTrackerApp
xcodegen generate
```

### App Store Connect'te kontrol edin:
Bundle ID'nin **developer.apple.com/account → Identifiers** bölümünde
kayıtlı olduğundan emin olun.

---

## 3. Uygulama Logosu

### Gereksinimler:
- **Boyut:** 1024 × 1024 piksel, PNG formatı
- **Alfa kanalı yok** (şeffaf arka plan kabul edilmez)
- **Köşe yuvarlama yok** (iOS otomatik uygular)

### Nasıl eklenir:

1. `PriceTrackerApp/Resources/Assets.xcassets/AppIcon.appiconset/` klasörüne gidin
2. Logonuzu `AppIcon.png` adıyla bu klasöre kopyalayın
3. `Contents.json` dosyasını şu içerikle güncelleyin:

```json
{
  "images": [
    {
      "filename": "AppIcon.png",
      "idiom": "universal",
      "platform": "ios",
      "size": "1024x1024"
    }
  ],
  "info": {
    "author": "xcode",
    "version": 1
  }
}
```

4. Xcode otomatik olarak diğer boyutları üretir.

---

## 4. AdMob Kurulumu

### 4.1 AdMob Hesabı Oluşturun

1. [admob.google.com](https://admob.google.com) adresine gidin
2. Google hesabınızla giriş yapın
3. "Uygulama Ekle" → iOS → Mevcut uygulama yok (henüz yayımlanmadı)
4. Uygulama adını girin → **App ID** alın (`ca-app-pub-XXXXXXXX~XXXXXXXXXX`)

### 4.2 Rewarded Ad Birimi Oluşturun

1. AdMob panelinde uygulamanızı seçin
2. "Reklam Birimleri" → "Ekle" → **Ödüllü (Rewarded)**
3. Ad birimini oluşturun → **Ad Unit ID** alın (`ca-app-pub-XXXXXXXX/XXXXXXXXXX`)

### 4.3 Xcode'da Yapılandırın

`project.yml` içinde `Release` konfigürasyonunu güncelleyin:

```yaml
configs:
  Debug:
    GAD_APP_ID: ca-app-pub-3940256099942544~1458002511        # Google test ID (değiştirme)
    GAD_REWARDED_UNIT_ID: ca-app-pub-3940256099942544/1712485313  # Google test ID (değiştirme)
  Release:
    GAD_APP_ID: "ca-app-pub-XXXXXXXX~XXXXXXXXXX"             # Kendi App ID'niz
    GAD_REWARDED_UNIT_ID: "ca-app-pub-XXXXXXXX/XXXXXXXXXX"   # Kendi Ad Unit ID'niz
```

Ardından:
```bash
xcodegen generate
```

---

## 5. In-App Purchase (Premium)

### 5.1 App Store Connect'te IAP Oluşturun

1. [appstoreconnect.apple.com](https://appstoreconnect.apple.com) → Uygulamanız
2. "Para Kazanma" → "Uygulama İçi Satın Alma" → "+"
3. **Tür:** Non-Consumable (Tüketilemeyen)
4. **Ürün Kimliği:** `com.algorix.pricetracker.premium` (veya kendi bundle ID'nize uygun)
5. Fiyatı ve lokalizasyonu doldurun
6. Durum: **Onay için Hazır**

### 5.2 Ürün Kimliğini Güncelleyin

`project.yml` içinde:
```yaml
settings:
  base:
    IAP_PREMIUM_PRODUCT_ID: com.SIRKETINIZ.UYGULAMANIZ.premium
```

---

## 6. Signing & Capabilities

### 6.1 Xcode'da İmzalama

1. Xcode'da projeyi açın (`PriceTracker.xcodeproj`)
2. Sol panelde `PriceTracker` hedefini seçin
3. **Signing & Capabilities** sekmesi:
   - "Automatically manage signing" işaretleyin
   - **Team:** Apple Developer hesabınızı seçin
   - **Bundle Identifier:** doğru olduğunu kontrol edin

### 6.2 Push Notifications Capability

1. "+ Capability" butonuna tıklayın
2. **Push Notifications** ekleyin

> Not: Uygulamamız lokal bildirim kullanıyor. Push gerekmez ama ilerisi için eklenmesi önerilir. Lokale geçmek isterseniz bu adımı atlayabilirsiniz.

### 6.3 In-App Purchase Capability

1. "+ Capability" butonuna tıklayın
2. **In-App Purchase** ekleyin

---

## 7. App Store Connect — Uygulama Kaydı

1. [appstoreconnect.apple.com](https://appstoreconnect.apple.com) → "Uygulamalarım" → "+"
2. **Platform:** iOS
3. **Ad:** Uygulamanızın App Store'da görünecek adı (maks. 30 karakter)
4. **Birincil Dil:** Türkçe
5. **Bundle ID:** Dropdown'dan seçin
6. **SKU:** `pricetracker-001` (dahili, kullanıcı görmez)

### Zorunlu Bilgiler:

| Alan | Öneri |
|---|---|
| Açıklama | Fiyat düşüşü takibi, bildirim, premium |
| Anahtar Kelimeler | fiyat takip, indirim alarm, alışveriş |
| Destek URL | Kendi web siteniz veya GitHub |
| Gizlilik Politikası URL | **Zorunlu** — hazırlamanız gerekiyor |
| Kategorie | Alışveriş |
| Yaş Derecelendirmesi | 4+ |

### Gizlilik Politikası (Zorunlu):

En az şunları içermeli:
- Hangi veri toplanıyor: **"Hiçbir kişisel veri toplanmaz"**
- Reklam: **"Google AdMob üçüncül taraf reklamları gösterebilir"**
- İletişim e-postası

[Ücretsiz gizlilik politikası oluşturucu](https://www.privacypolicygenerator.info)

---

## 8. Ekran Görüntüleri

### Zorunlu Boyutlar:

| Cihaz | Boyut | Miktar |
|---|---|---|
| iPhone 6.9" (iPhone 16 Pro Max) | 1320 × 2868 px | En az 1 |
| iPhone 6.5" (iPhone 14 Plus) | 1284 × 2778 px | En az 1 |
| iPad Pro 12.9" (3. nesil+) | 2048 × 2732 px | En az 1 (iPad desteği varsa) |

### Simulator'da ekran görüntüsü almak için:

```bash
# Simulator çalışırken:
xcrun simctl io booted screenshot screenshot_001.png
```

Veya Simulator'da **File → Save Screen** (Cmd+S).

### Önerilen ekranlar:
1. Ürün listesi (fiyat değişim yüzdeli)
2. Ürün ekleme akışı
3. Fiyat geçmişi sayfası
4. Ayarlar — Premium karşılaştırma
5. Fiyat alarm bildirimi (mock)

---

## 9. Build, Archive & Submit

### 9.1 Son Kontroller

```bash
cd PriceTrackerApp
xcodegen generate   # project.yml'den projeyi yenile
```

Xcode'da:
- Scheme: **PriceTracker**
- Destination: **Any iOS Device (arm64)**

### 9.2 Archive

1. Xcode menü: **Product → Archive**
2. Build tamamlanana kadar bekleyin (~5-10 dk ilk seferinde)
3. **Organizer** penceresi otomatik açılır

### 9.3 Validate

1. Organizer'da archive'ı seçin → **Validate App**
2. Tüm uyarıları ve hataları giderin
3. Özellikle kontrol edin:
   - `NSAllowsArbitraryLoads` uyarısı (project.yml'de kapatıldı ✓)
   - Missing icons hatası (logonuzu ekleyin ✓)
   - Provisioning profile hatası (Team seçili olmalı ✓)

### 9.4 Upload

1. **Distribute App** → **App Store Connect** → **Upload**
2. Seçenekler: Strip Swift symbols ✓ | Upload symbols ✓
3. Upload tamamlanınca App Store Connect'te **TestFlight** altında görünür

### 9.5 App Store Connect'te Yayımla

1. **TestFlight** → Internal Testing ile kendi cihazınızda test edin
2. Hazırsa **App Store** → "Submit for Review" → İncelemeye gönderin
3. Apple inceleme süresi: genellikle 1-3 iş günü

---

## 10. İnceleme Notları

Apple inceleme sırasında sorabileceği konular ve cevapları:

### "NSAllowsLocalNetworking neden açık?"
> "Uygulama, kullanıcının kendi VPS'inde kurduğu backend servise bağlanmaktadır. Bu bağlantı yerel ağ üzerinden yapılabilir."

### "Reklamlı model açıklaması"
> "Ücretsiz kullanıcılar, ürün eklemek için kısa bir ödüllü reklam izler. Premium kullanıcılar reklamsız sınırsız ürün ekleyebilir."

### "Kullanıcı hesabı olmadan premium satın alma"
> "Uygulama, Apple kimliği üzerinden otomatik olarak satın alma durumunu doğrular (StoreKit 2 Transaction.currentEntitlements)."

### Demo hesap gerekmez
Uygulamada giriş sistemi yoktur. İncelemeci herhangi bir cihazda test edebilir.

---

## Özet Kontrol Listesi

```
[ ] Apple Developer hesabı aktif ($99/yıl)
[ ] Bundle ID kayıtlı (developer.apple.com)
[ ] Uygulama adı belirlendi
[ ] Logo hazır (1024×1024 PNG, alfa yok)
[ ] AdMob hesabı oluşturuldu
[ ] AdMob App ID project.yml'e girildi (Release)
[ ] AdMob Rewarded Ad Unit ID girildi (Release)
[ ] IAP ürünü App Store Connect'te oluşturuldu
[ ] IAP ürün kimliği project.yml'de doğru
[ ] Gizlilik politikası URL hazır
[ ] Ekran görüntüleri hazır (en az 1320×2868)
[ ] Signing → Team seçili
[ ] Push Notifications capability eklendi
[ ] In-App Purchase capability eklendi
[ ] xcodegen generate çalıştırıldı
[ ] Archive → Validate → hata yok
[ ] Upload tamamlandı
[ ] App Store Connect metadata eksiksiz
[ ] TestFlight'ta test edildi
[ ] İncelemeye gönderildi
```
