# App Store Gönderim Rehberi — Price Tracker (Fiyat Takibi)

## Proje Referansı
- Bundle ID: `com.algorix.pricetracker`
- Display Name: `Fiyat Takibi`
- iOS Deployment Target: 16.0
- Marketing Version: 1.0.0 (Build 1)

---

## KRİTİK — Gönderim Öncesi Yapılması Zorunlu

### 1. Gerçek AdMob ID'leri Girin

**Dosya:** `project.yml` — Release konfigürasyonu

```yaml
configs:
  Release:
    GAD_APP_ID: "ca-app-pub-XXXXXXXX~XXXXXXXXXX"      # ← gerçek App ID
    GAD_REWARDED_UNIT_ID: "ca-app-pub-XXXXXXXX/XXXXX"  # ← gerçek Rewarded Unit ID
```

**Dosya:** `Sources/PriceTracker/Services/AdService.swift` (satır 23-29)

```swift
enum AdUnitID {
    static let banner       = "ca-app-pub-XXXXXXXX/XXXXX"  // Gerçek Banner ID
    static let rewarded     = "ca-app-pub-XXXXXXXX/XXXXX"  // Gerçek Rewarded ID
    static let interstitial = "ca-app-pub-XXXXXXXX/XXXXX"  // Gerçek Interstitial ID
}
```

AdMob hesabında:
1. App Store'a yükleyeceğiniz bundle ID (`com.algorix.pricetracker`) ile yeni uygulama oluşturun
2. Üç reklam birimi (Banner, Rewarded, Interstitial) tanımlayın
3. ID'leri yukarıdaki yerlere yazın

### 2. App Tracking Transparency (ATT) Entegrasyonu

AdMob reklamları IDFA kullanıyorsa ATT zorunludur.

**Info.plist'e ekleyin:**
```xml
<key>NSUserTrackingUsageDescription</key>
<string>Reklamları size özel gösterebilmek için cihaz tanımlayıcınızı kullanmak istiyoruz.</string>
```

**PrivacyInfo.xcprivacy'de düzeltin:**
```xml
<key>NSPrivacyTracking</key>
<true/>  <!-- false iken true yapın -->
```

**PriceTrackerApp.swift'e ATT izin çağrısı ekleyin:**
```swift
import AppTrackingTransparency

// App aktif olduğunda (scenePhase .active içinde):
ATTrackingManager.requestTrackingAuthorization { _ in }
```

### 3. NSAllowsArbitraryLoads — ATS İstisnası

Web scraping kullanıcının girdiği herhangi bir e-ticaret URL'sine bağlanmak zorunda olduğu için `NSAllowsArbitraryLoads: true` olarak ayarlanmıştır.

Apple Review'a gönderim notlarında mutlaka aşağıdaki gerekçeyi belirtin:

> "Uygulama, kullanıcının eklediği e-ticaret URL'lerinden fiyat bilgisi çekmektedir. Bu sitelerin çoğu HTTPS yanında HTTP de sunmaktadır ve hangi domain'in ekleneceği önceden bilinemediğinden NSAllowsArbitraryLoads açılmıştır. Kullanıcı gizliliği açısından herhangi bir özel veri aktarılmamaktadır."

Her iki dosyada da doğru ayar:

**Info.plist:**
```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
    <key>NSAllowsLocalNetworking</key>
    <true/>
</dict>
```

**project.yml:**
```yaml
NSAppTransportSecurity:
  NSAllowsArbitraryLoads: true
  NSAllowsLocalNetworking: true
```

### 4. In-App Purchase (Premium) — Eksik

`project.yml` içinde premium IAP ürün kimliği tanımlı:
- `IAP_PREMIUM_PRODUCT_ID: com.algorix.pricetracker.premium`

Ancak `SettingsViewModel.swift` içinde StoreKit satın alma kodu **hiç implemente edilmemiş**.

**Yapılması gerekenler:**
1. StoreKit (StoreKit 2) ile `Product` sorgulama ve satın alma akışı ekleyin
2. `SettingsView.swift` içinde "Premium'a Yükselt" butonu ekleyin
3. App Store Connect'te `com.algorix.pricetracker.premium` ürününü oluşturun
4. Test ortamında sandbox tester ile doğrulayın

### 5. Version Numarası Çelişkisi

| Yer | Değer |
|---|---|
| `project.yml` `MARKETING_VERSION` | `1.0.0` |
| `SettingsView.swift:54` (hardcoded) | `2.0.0` |

**Düzeltme:** `SettingsView.swift` satır 54'teki sabit `"2.0.0"` değerini dinamik hale getirin:
```swift
Text(Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "1.0.0")
```

---

## YÜKSEK ÖNCELİKLİ

### 6. AppLogo — 2x ve 3x Görselleri Eksik

`Assets.xcassets/AppLogo.imageset/` içinde **sadece 1x** boyutunda `AppLogo.png` var.
`Contents.json` 2x ve 3x girişleri içeriyor ancak dosyalar yok.

- 2x: 200x200px (veya orijinal boyutun 2 katı)
- 3x: 300x300px (veya orijinal boyutun 3 katı)

SplashView'de kullanıldığı için Retina ekranlarda bulanık görünecektir.

### 7. Background Modes Gerekçesi

Info.plist'te `UIBackgroundModes` → `fetch` ve `processing` tanımlı.

Review notlarında gerekçe olarak belirtin:
> "Arka planda periyodik fiyat kontrolü yaparak kullanıcıya hedef fiyat düştüğünde bildirim göndermek için `fetch` ve `processing` background modları kullanılmaktadır. Kullanıcı tarafından ayarlanabilir kontrol aralığı (1-24 saat) ile BGTaskScheduler üzerinden çalışır."

### 8. Web Scraping — 4.2.5 Uyumluluğu

App Store Guideline 4.2.5: "Scraping/clipping apps must add significant value."

Bu uygulama:
- Çok katmanlı fiyat çekme motoru (JSON-LD, meta, microdata, HTML pattern)
- Hedef fiyat alarmı ile bildirim
- Fiyat geçmişi takibi
- CSS seçici kalibrasyonu

Review notlarında bu katma değer vurgulanmalıdır.

### 9. Test Bilgileri (Reviewer'a)

App Store Review notlarına aşağıdaki test talimatlarını ekleyin:
1. Uygulama açılır → Splash ekranı gösterilir → Ürün listesi (boş) görünür
2. Sağ üstteki `+` butonuna basın
3. Bir e-ticaret URL'si girin (örn. https://www.trendyol.com/...)
4. "Fiyatı Otomatik Çek" butonuna tıklayın
5. Fiyat çekilir, hedef fiyat girin, kaydedin
6. Ürün listesinde göründüğünü doğrulayın
7. Ayarlar → Bildirim toggle'ı çalışır
8. Premium satın alma (implementasyon tamamlandıysa)

---

## ORTA ÖNCELİKLİ

### 10. SKAdNetwork Listesi Güncellemesi

Info.plist'te 15 SKAdNetwork ID'si tanımlı. Google'ın güncel listesini https://developers.google.com/admob/ios/ios14 adresinden kontrol edip eksikleri ekleyin.

### 11. Entitlements Dosyası

`PriceTracker.entitlements` dosyası boş (`<dict/>`). Uygulamanın ihtiyacı yoksa sorun değil, ancak ileride push notification, iCloud vb. eklenirse güncellenmelidir.

### 12. App Store Connect Metadata (Kod Dışı)

Aşağıdaki öğeler App Store Connect'te manuel girilir, kodda bulunmaz:

| Öğe | Değer (öneri) |
|---|---|
| Açıklama | "E-ticaret sitelerindeki ürün fiyatlarını takip edin, hedef fiyata düşünce anında bildirim alın." |
| Anahtar Kelimeler | fiyat takip, price tracker, indirim, alarm, e-ticaret |
| Destek URL | https://algorix.com.tr |
| Pazarlama URL | https://algorix.com.tr/pricetracker |
| Gizlilik Politikası URL | https://algorix.com.tr/privacy |
| Yasal Şartlar URL | https://algorix.com.tr/terms |
| İletişim | Geliştirici adı: Algorix |

### 13. Ekran Görüntüleri (Screenshot) Boyutları

App Store Connect için gerekli screenshot boyutları:
- 6.7" iPhone: 1290x2796 (iPhone 14 Pro Max)
- 6.5" iPhone: 1242x2688 (iPhone 11 Pro Max)
- 5.5" iPhone: 1242x2208 (iPhone 8 Plus)
- 12.9" iPad: 2048x2732 (iPad Pro)

---

## GÖNDERİM ÖNCESİ KONTROL LİSTESİ

- [ ] **AdMob** — Gerçek App ID ve Ad Unit ID'ler girildi
- [ ] **ATT** — `NSUserTrackingUsageDescription` eklendi; `ATTrackingManager.requestTrackingAuthorization` çağrılıyor
- [ ] **Privacy Manifest** — `NSPrivacyTracking: true` (AdMob IDFA kullanıyorsa)
- [ ] **ATS** — `NSAllowsArbitraryLoads: false` (proje ayarı doğru); Review notuna gerekçe yazıldı
- [ ] **IAP** — StoreKit implementasyonu tamam; App Store Connect'te ürün oluşturuldu
- [ ] **Version** — SettingsView'de dynamic version kullanılıyor, marketing version 1.0.0
- [ ] **AppLogo** — 2x ve 3x görseller eklendi
- [ ] **Background Modes** — Review notunda gerekçe belirtildi
- [ ] **SKAdNetwork** — Güncel liste kullanılıyor
- [ ] **Test URL** — Geçerli bir e-ticaret URL'si ile test edildi
- [ ] **Screenshots** — Tüm gerekli boyutlarda ekran görüntüleri yüklendi
- [ ] **Privacy Policy** — Settings'te link çalışıyor; App Store Connect'te URL girildi
- [ ] **Terms of Service** — Settings'te link çalışıyor; App Store Connect'te URL girildi
- [ ] **Review Notes** — Test talimatları ve scraping gerekçesi eklendi
- [ ] **Build** — `xcodegen generate` çalışıyor; Xcode'da arşiv alınabiliyor
