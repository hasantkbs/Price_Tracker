# AdMob Production Kurulumu

## Durum (güncel)

| Ayar | Debug | Release |
|------|-------|---------|
| `GAD_APP_ID` | Google test | **Production** `ca-app-pub-2093076492549135~7958038767` |
| `GAD_BANNER_UNIT_ID` | Google test | **Production** `ca-app-pub-2093076492549135/5977753004` |
| `GAD_REWARDED_UNIT_ID` | Google test | **Production** `ca-app-pub-2093076492549135/4561719237` |
| `GAD_INTERSTITIAL_UNIT_ID` | Google test | **Geçici Google test** — App Store öncesi değiştirin |

Production App ID, Banner ve Rewarded birimleri `project.yml` ve `PriceTracker.xcodeproj` içinde Release yapılandırmasına işlendi. Debug yapılandırması yalnızca Google örnek test ID'lerini kullanır.

### Eksik: Interstitial reklam birimi

Interstitial için henüz production ad unit ID verilmedi. Release şu an geçici olarak Google test interstitial ID'sini kullanıyor (`ca-app-pub-3940256099942544/4411468910`). **App Store gönderiminden önce** AdMob konsolunda Interstitial birimi oluşturup `GAD_INTERSTITIAL_UNIT_ID` değerini Release'te güncelleyin.

## 1. AdMob konsolu

1. https://admob.google.com → Uygulama ekle (veya mevcut uygulama)
2. Platform: iOS, Bundle ID: `com.tagtrack.app`
3. Reklam birimleri:
   - Banner — oluşturuldu (`5977753004`)
   - Rewarded — oluşturuldu (`4561719237`)
   - **Interstitial — oluşturun** ve ID'yi projeye ekleyin

## 2. Xcode build settings

`PriceTracker` target → Build Settings → arama: `GAD_`

Release için güncel production değerleri:

| Ayar | Production değer |
|------|------------------|
| `GAD_APP_ID` | `ca-app-pub-2093076492549135~7958038767` |
| `GAD_BANNER_UNIT_ID` | `ca-app-pub-2093076492549135/5977753004` |
| `GAD_REWARDED_UNIT_ID` | `ca-app-pub-2093076492549135/4561719237` |
| `GAD_INTERSTITIAL_UNIT_ID` | *(AdMob'da oluşturup buraya yapıştırın)* |

Alternatif: `project.yml` içinde `configs → Release → GAD_INTERSTITIAL_UNIT_ID` güncelleyip `xcodegen generate` çalıştırın (veya `project.pbxproj` Release satırlarını elle düzenleyin).

## 3. Doğrulama

Archive (Release) aldıktan sonra üretilen uygulama `Info.plist` içinde:

- `GADApplicationIdentifier` → production App ID
- `GADBannerAdUnitID` / `GADRewardedAdUnitID` → production birim ID'leri
- `GADInterstitialAdUnitID` → production interstitial (test ID kalmamalı)

```bash
xcodebuild -project PriceTracker.xcodeproj -scheme PriceTracker \
  -configuration Release -destination 'generic/platform=iOS' \
  CODE_SIGNING_ALLOWED=NO build
```
