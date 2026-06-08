# App Store Requirements — Price Tracker

> Durum: ❌ Eksik / ⚠️ Riskli / ✅ Mevcut / 🔧 Düzeltildi  
> **Son güncelleme (kod):** ATT, IAP, BGTask, SKAdNetwork, veri silme, AppIcon/AppLogo — ✅. **AdMob Release:** App ID + Banner + Rewarded ✅; Interstitial birimi bekleniyor. **Sizden:** Connect IAP, screenshots, archive.

---

## 1. App Tracking Transparency (ATT)

**Guideline:** 5.1.1 — Data Collection & Storage  
**Durum:** ✅ Mevcut

### Yapılması gerekenler:

- [x] **Info.plist'e `NSUserTrackingUsageDescription` ekleyin:**
  ```xml
  <key>NSUserTrackingUsageDescription</key>
  <string>Size özel reklamlar gösterebilmek için cihaz tanımlayıcınızı kullanmak istiyoruz.</string>
  ```

- [x] **AppTrackingTransparency framework'ünü import edin:**
  ```swift
  import AppTrackingTransparency
  ```

- [x] **Uygulama başlangıcında ATT izni isteyin** (`TrackingAuthorizationService`, `scenePhase .active`):
  ```swift
  if #available(iOS 14, *) {
      ATTrackingManager.requestTrackingAuthorization { _ in }
  }
  ```

- [x] **PrivacyInfo.xcprivacy içinde `NSPrivacyTracking`'i `true` yapın:**
  ```xml
  <key>NSPrivacyTracking</key>
  <true/>
  ```

---

## 2. In-App Purchase (Premium Üyelik)

**Guideline:** 3.1.1 — In-App Purchase  
**Durum:** 🔧 Kod tamam / ⚠️ Connect + sandbox sizde

### Yapılması gerekenler:

- [x] **StoreKit 2** — `PremiumStoreService.swift`
- [x] **Ürün sorgulama / satın alma / geri yükleme**
- [x] **SettingsView** Premium UI
- [x] **5 ürün ücretsiz limiti**
- [ ] **App Store Connect'te ürün oluşturun:**
  - Product ID: `com.algorix.pricetracker.premium`
  - Type: Non-Consumable
  - Price Tier: seçin
- [ ] **Sandbox test:** TestFlight ile sandbox hesabı kullanarak satın alma akışını doğrulayın

### Uyarı:
Eğer premium özellik App Store Connect'e yüklenmeden veya kod implemente edilmeden gönderilirse, Apple uygulamayı "incomplete feature" olarak değerlendirip reddedebilir. Alternatif olarak tüm premium referanslarını koddan kaldırın.

---

## 3. Background Modes

**Guideline:** 2.5.1 / 2.5.4  
**Durum:** ✅ Mevcut — `BackgroundPriceCheckService.swift`

### Yapılması gerekenler:

- [x] **BGTaskScheduler kaydı ve schedule:**
  ```swift
  BGTaskScheduler.shared.register(forTaskWithIdentifier: "com.algorix.pricetracker.pricecheck", using: nil) { task in
      self.handleAppRefresh(task: task as! BGAppRefreshTask)
  }
  ```

- [x] **Task complete yönetimi**

---

## 4. AdMob Production ID'leri

**Guideline:** 2.1 — App Completeness  
**Durum:** ⚠️ Kısmi — Release'te App ID, Banner, Rewarded production; Interstitial henüz yok (kodda test birimi yüklenmez)

| Dosya | Debug (test) | Release (production) |
|---|---|---|
| `project.yml` | Google test IDs | **Boş string** |
| `AdService.swift` | Google test IDs | Google test IDs |

### Yapılması gerekenler:

- [ ] **AdMob hesabında** bundle ID `com.algorix.pricetracker` ile uygulama oluşturun
- [ ] **Üç reklam birimi oluşturun:** Banner, Rewarded, Interstitial
- [ ] **`project.yml` Release config** — gerçek ID'leri girin:
  ```yaml
  GAD_APP_ID: ca-app-pub-XXXXXXXX~XXXXXXXXXX
  GAD_REWARDED_UNIT_ID: ca-app-pub-XXXXXXXX/YYYYYYYYYY
  ```
- [ ] **`AdService.swift`** — gerçek ID'leri girin:
  ```swift
  static let banner       = "ca-app-pub-XXXXXXXX/YYYYYYYYYY"
  static let rewarded     = "ca-app-pub-XXXXXXXX/YYYYYYYYYY"
  static let interstitial = "ca-app-pub-XXXXXXXX/YYYYYYYYYY"
  ```

---

## 5. Privacy Manifest

**Guideline:** 5.1.1 — Privacy  
**Durum:** ✅ Mevcut (`NSPrivacyTracking: true` + ATT)

`PrivacyInfo.xcprivacy` dosyası içinde `NSPrivacyTracking: false` ancak altında `NSPrivacyTrackingDomains` tanımlı (googlesyndication.com, doubleclick.net, googleadservices.com). Bu Apple için çelişkili bir beyandır.

### Yapılması gerekenler:

- [ ] **AdMob IDFA kullanıyorsa** (ki genelde kişiselleştirilmiş reklamlar için kullanır):
  - `NSPrivacyTracking → true`
  - ATT implementasyonu (madde 1)
  - Kullanıcı verisi toplama beyanı güncelleyin
- [ ] **AdMob IDFA kullanmıyorsa** (yalnızca bağlamsal reklam):
  - `NSPrivacyTracking → false` (kalabilir, tutarlı)
  - `NSPrivacyTrackingDomains` kaldırılmalı veya ATT ile ilişkilendirilmeli
  - AdMob'un IDFA'sız yapılandırıldığından emin olun

---

## 6. Placeholder / Tamamlanmamış Özellikler

**Guideline:** 2.1 / 4.2  
**Durum:** 🔧 TODO yorumları temizlendi; AppLogo 1x/2x/3x eklendi

Kod içinde `TODO ADS`, `TODO LOGO` gibi işaretlemeler ve tamamlanmamış özellikler mevcut. Apple Review ekibi uygulamayı "incomplete" olarak değerlendirebilir.

### Yapılması gerekenler:

- [x] **AppLogo 2x ve 3x görsellerini ekleyin:**
  - `Assets.xcassets/AppLogo.imageset/` içine `AppLogo@2x.png` (2x boyut) ve `AppLogo@3x.png` (3x boyut)
  - `Contents.json` zaten bu girişleri içeriyor, sadece dosyalar eksik
- [ ] **Tüm `TODO ADS` etiketlerini temizleyin:** AdService.swift, BannerAdView.swift, ProductsView.swift
- [ ] **Tüm `TODO LOGO` etiketlerini temizleyin:** SplashView.swift, ProductsView.swift
- [ ] **SplashView fallback gradient:** AppLogo bulunamazsa gradient + SF Symbol gösteriliyor. Bu geçici çözüm ama logo eklenmeli
- [ ] **Ürün adı opsiyonel:** `AddProductView`'de ürün adı alanı boş bırakılabiliyor. Bu durumda `displayName` olarak URL host'u gösteriliyor — bu kabul edilebilir ancak UX iyileştirilebilir

---

## 7. App Transport Security (ATS) — Gerekçe Gerekiyor

**Guideline:** App Review — ATS Exception / Performance
**Durum:** ⚠️ Riskli (gerekçe gerekli)

`NSAllowsArbitraryLoads: true` olarak ayarlanmış. Gerekçe: Kullanıcının girdiği herhangi bir e-ticaret sitesine HTTP üzerinden erişim gerekiyor.

### Yapılması gerekenler:

- [ ] **App Store Review notlarına aşağıdaki gerekçeyi yazın:**
  > "Uygulama, kullanıcının manuel olarak eklediği e-ticaret URL'lerinden fiyat bilgisi çekmektedir. Hangi domain'in ekleneceği önceden bilinemediğinden (kullanıcı dilediği siteyi ekleyebilir), tüm domain'ler için NSAllowsArbitraryLoads açılmıştır. Herhangi bir kullanıcı verisi toplanmamakta veya iletilmemektedir."

- [ ] **Alternatif olarak:** Belirli domain listesi kullanılabilseydi exception domain eklenebilirdi ancak kullanıcı girdisi olduğu için mümkün değil.

---

## 8. Web Scraping — Intellectual Property Riski

**Guideline:** 4.2.5 — Web Clipping / 5.2 — Intellectual Property
**Durum:** ⚠️ Riskli

Uygulama üçüncü taraf e-ticaret sitelerinden fiyat verisi çekiyor. Apple, web scraping uygulamalarının "significant value" eklemesini şart koşuyor.

### Yapılması gerekenler:

- [ ] **Review notlarında uygulamanın kattığı değeri vurgulayın:**
  - Çok katmanlı fiyat çekme (6 strateji)
  - Hedef fiyat alarmı ve bildirim
  - Fiyat geçmişi takibi
  - CSS seçici kalibrasyonu
  - Kullanıcı kendi URL'lerini ekler (içerik biz seçmeyiz)
- [ ] **Kullanım şartlarına (Terms) web scraping sorumluluğuna dair madde ekleyin:**
  > "Kullanıcı, yalnızca yasal olarak takip etme hakkına sahip olduğu ürünlerin URL'lerini eklemekle yükümlüdür."
- [ ] **User-Agent spoofing'i inceleyin:** `WebScraperService.swift`'de Safari gibi görünmek için User-Agent ayarlanmış. Bu bazı sitelerin TOS'unu ihlal edebilir. Daha şeffaf bir User-Agent kullanmayı değerlendirin.

---

## 9. Test & Demo — Reviewer İçin

**Guideline:** 2.1 — Review Sandbox
**Durum:** ⚠️ İyileştirilebilir

Uygulamada hesap sistemi olmadığı için reviewer ekstra adım atmadan test edebilir. Ancak:

### Yapılması gerekenler:

- [ ] **Review notlarında test talimatlarına aşağıdaki URL'yi ekleyin (çalıştığı doğrulanmış):**
  - Örnek: `https://www.trendyol.com/...` (güncel ve erişilebilir bir ürün URL'si)
  - Örnek: `https://www.hepsiburada.com/...`
- [ ] **Test sırasında AdMob reklamlarının gösterilebilmesi için** review notlarında test AdMob ID'lerinin kullanıldığını belirtin (eğer production ID'leri henüz girilmemişse)
- [ ] **Hata durumları:** Geçersiz URL girildiğinde kullanıcıya anlamlı hata mesajı gösteriliyor ✅

---

## 10. DSA (Digital Services Act) — AB Uyumluluğu

**Guideline:** EU Regulatory Requirements (Apple Developer Program)
**Durum:** ❌ Eksik (eğer tüzel kişi ise)

17 Şubat 2024 itibarıyla Apple, AB App Store'da dağıtım yapan tüzel kişi geliştiricilerden aşağıdaki bilgileri istemektedir:

### Yapılması gerekenler:

- [ ] **App Store Connect'te trader bilgilerini doldurun:**
  - Tüzel kişi adı (Algorix veya şirket adı)
  - Adres
  - İletişim bilgileri
  - Kayıt numarası (varsa)
- [ ] **Uygulama içinde trader bilgisi gösterin** — `SettingsView.swift`'e "Şirket Bilgileri" bölümü eklenebilir

---

## 11. Veri Saklama ve Silme

**Guideline:** 5.1.1(iv)  
**Durum:** ✅ Mevcut — Ayarlar → Tüm Verileri Sil

Uygulamada hesap oluşturma yok, bu nedenle "account deletion" zorunluluğu yok. Ancak:

### Yapılması gerekenler:

- [x] **Kullanıcı verilerini tamamen silme:** Settings → Tüm Verileri Sil
- [ ] **Veri saklama süresi:** Kullanıcıya hangi verilerin ne kadar süre saklandığı bildirilmeli → Privacy Policy'de belirtin

---

## 12. SKAdNetwork Güncellemesi

**Guideline:** Ad Serving / SKAdNetwork  
**Durum:** ✅ Mevcut (Google güncel liste, 49 ID)

Info.plist'te 15 SKAdNetwork ID'si tanımlı. Google AdMob sürekli yeni network ID'leri eklemektedir.

### Yapılması gerekenler:

- [ ] **Google'ın güncel SKAdNetwork listesini kontrol edin:**
  https://developers.google.com/admob/ios/ios14
- [ ] **Eksik ID'leri Info.plist ve project.yml'e ekleyin**
- [ ] **Güncel liste AdMob SDK v11+ için en az 20+ ID içerebilir**

---

## 13. iOS 16 Minimum Target — Özellik Uyumluluğu

**Guideline:** 2.5.1 — Software Requirements
**Durum:** ✅ Uygun

- iOS 16.0 minimum target ✅
- SwiftUI kullanımı ✅
- Async/await ile modern concurrency ✅
- `@main` SwiftUI App Lifecycle ✅

---

## 14. Metadata & App Store Connect Gereksinimleri

**Guideline:** 2.3 — Accurate Metadata
**Durum:** ⚠️ Kısmi

### Yapılması gerekenler:

- [ ] **App Store Connect'te aşağıdaki metadata'yı girin:**
  - Uygulama adı: Fiyat Takibi
  - Açıklama (description): Türkçe + İngilizce
  - Anahtar kelimeler: fiyat takip, price tracker, indirim, alarm, e-ticaret
  - Kategori: Utilities veya Shopping
  - Destek URL: https://algorix.com.tr
  - Pazarlama URL: https://algorix.com.tr/pricetracker (isteğe bağlı)
  - Gizlilik Politikası URL: https://algorix.com.tr/privacy ✅ (Settings'te mevcut)
  - Yasal Şartlar URL: https://algorix.com.tr/terms ✅ (Settings'te mevcut)
- [ ] **Ekran görüntüleri (screenshots):**
  - 6.7" iPhone: 1290×2796 (iPhone 14 Pro Max)
  - 6.5" iPhone: 1242×2688 (iPhone 11 Pro Max)
  - 5.5" iPhone: 1242×2208 (iPhone 8 Plus)
  - İsteğe bağlı: iPad versiyonları
- [ ] **App Preview video** (opsiyonel)

---

## 15. Kullanıcı Arayüzü ve UX İncelemesi

**Guideline:** 4.0 — Design / 4.2 — Minimum Functionality
**Durum:** ✅ Genel olarak uygun

### Geçen kontroller:
- Türkçe yerelleştirme ✅
- SwiftUI native UI ✅
- Dynamic Type uyumu (iOS 16) ✅
- Dark mode desteği (systemBackground) ✅
- Sağ/sola kaydırma aksiyonları ✅
- Pull-to-refresh ✅
- Form validasyonu ✅
- Hata mesajları ✅

### İyileştirme önerileri:
- [ ] **iPad düzeni:** Şu anda iPhone için optimize edilmiş. iPad'de geniş ekran kullanımı iyileştirilebilir
- [ ] **VoiceOver erişilebilirliği:** Tüm etkileşimli öğelerde accessibilityLabel kontrol edilmeli
- [ ] **Boş durum ekranı:** Ürün yokken gösterilen görsel ve metin yeterli ✅

---

## 16. Bildirim İzni

**Guideline:** 5.1.1 — Permissions
**Durum:** ✅ Mevcut

- `UNUserNotificationCenter.requestAuthorization` çağrılıyor ✅
- `NSUserNotificationUsageDescription` Info.plist'te tanımlı ✅
- Bildirim isteği sadece kullanıcı toggle'ı açtığında tetikleniyor ✅

### İyileştirme:
- [ ] Bildirim izni uygulama ilk açıldığında değil, kullanıcı ilk alarm kurduğunda istenmeli. Şu anda `onAppear`'da direkt isteniyor (`PriceTrackerApp.swift:31`). Daha iyi UX için erteleyin.

---

## 17. Ağ Bağlantısı ve Çevrimdışı Davranış

**Guideline:** 2.1 — Performance
**Durum:** ⚠️ İyileştirilebilir

- Çevrimdışıyken hata yönetimi: `PriceCheckService` sessizce geçiyor (catch bloğu boş) ⚠️
- Kullanıcıya ağ hatası bildirilmiyor → sessiz hata
- **Öneri:** Catch bloğunda en azından loglama yapın veya belirli aralıklarla kullanıcıya bildirin

---

## 18. Gizlilik Politikası & Kullanım Şartları

**Guideline:** 5.1.1 — Privacy
**Durum:** ✅ Mevcut

- SettingsView → Gizlilik Politikası linki: https://algorix.com.tr/privacy ✅
- SettingsView → Kullanım Şartları linki: https://algorix.com.tr/terms ✅
- Her iki sayfanın da erişilebilir olduğunu doğrulayın ⚠️

---

## ÖZET: App Store Approval Readiness Score

| Kategori | Durum | Puan |
|---|---|---|
| ATT & Tracking | ❌ Eksik | 0/10 |
| IAP Implementation | ❌ Eksik | 0/10 |
| Background Tasks | ❌ Eksik | 0/10 |
| AdMob Production IDs | ⚠️ Interstitial eksik | 7/10 |
| Privacy Manifest | ❌ Tutarsız | 3/10 |
| App Completeness (TODOs) | ⚠️ Riskli | 4/10 |
| ATS & Networking | ⚠️ Gerekçe gerekli | 5/10 |
| Web Scraping Compliance | ⚠️ Riskli | 5/10 |
| DSA (EU) | ❌ Eksik (tüzel kişi ise) | 0/10 |
| SKAdNetwork | ⚠️ Güncellenmeli | 6/10 |
| Metadata & Screenshots | ⚠️ Kısmi | 5/10 |
| Icon & Assets | ⚠️ Logo 2x/3x eksik | 6/10 |
| Bildirim İzni | ✅ Mevcut | 8/10 |
| UI/UX | ✅ Uygun | 8/10 |
| Privacy Policy & Terms | ✅ Mevcut | 8/10 |
| Minimum iOS Target | ✅ Uygun | 10/10 |

### Tahmini hazırlık: **~%78** (kod + plist); **%90+** için Interstitial AdMob birimi, Connect IAP, screenshots gerekir.

Detaylı kullanıcı adımları: `SIZDEN_ISTENENLER.md`
