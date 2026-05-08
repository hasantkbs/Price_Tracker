# Price Tracker

E-ticaret sitelerindeki ürün fiyatlarını takip eden, hedef fiyata düşünce iOS bildirimi gönderen uygulama.

## Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                        iOS App (SwiftUI)                    │
│  Tab 1: Ürünler          │  Tab 2: Ayarlar                  │
│  • Ürün listesi          │  • Premium / Ücretsiz            │
│  • Fiyat geçmişi         │  • API adresi                    │
│  • Alarm kurma           │                                  │
│  • Reklamlı ürün ekleme  │                                  │
└──────────────┬──────────────────────────────────────────────┘
               │ REST (HTTP/JSON)
               ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (api.py)                   │
│  /products CRUD  │  /check  │  /history  │  /recalibrate   │
└──────┬──────────────────────────────────────────────────────┘
       │
       ├── calibrate.py   CSS seçici tespiti & yeniden kalibrasyon
       ├── tracker.py     6 katmanlı fiyat çekme motoru
       ├── price_utils.py Fiyat metin ayrıştırıcı
       └── database.py    SQLite (products + price_history)
```

## Fiyat Çekme Stratejileri (Öncelik Sırası)

| # | Strateji | Açıklama |
|---|---|---|
| 1 | `json_ld` | `<script type="application/ld+json">` — en güvenilir |
| 2 | `meta_tags` | `og:price:amount`, `product:price:amount` |
| 3 | `microdata` | `itemprop="price"` |
| 4 | `selector` | Kalibrasyon sırasında kaydedilen CSS seçici |
| 5 | `class_search` | Class'ında "price/fiyat" geçen elementler |
| 6 | `general` | Son çare: kısa text node taraması |

CSS seçici 3 kez başarısız olursa "stale" işaretlenir; diğer stratejiler devreye girer.

## Dosya Yapısı

```
Price_Tracker/
├── api.py                  FastAPI REST API (ana giriş noktası)
├── calibrate.py            Sayfa analizi ve CSS seçici tespiti
├── tracker.py              Çok katmanlı fiyat çekme motoru
├── database.py             SQLite CRUD + price_history
├── price_utils.py          Fiyat metin ayrıştırıcı
├── requirements.txt        Python bağımlılıkları
│
├── Dockerfile              Üretim image (3 aşamalı, Playwright dahil)
├── docker-compose.yml      Üretim servisleri
├── docker-compose.dev.yml  Geliştirme (hot-reload)
├── Caddyfile               HTTPS reverse proxy
├── Makefile                Kısa yol komutları
├── env.example             Ortam değişkeni şablonu
│
└── PriceTrackerApp/        iOS SwiftUI uygulaması
    ├── project.yml         XcodeGen konfigürasyonu
    └── Sources/PriceTracker/
        ├── Models/
        ├── Services/       APIService, AdService, NotificationService
        ├── ViewModels/
        └── Views/
```

## API Endpoints

| Method | Endpoint | Açıklama |
|---|---|---|
| GET | `/health` | Sağlık kontrolü |
| GET | `/products` | Tüm ürünler |
| POST | `/products` | Ürün ekle + kalibre et |
| GET | `/products/{id}` | Tekil ürün |
| PUT | `/products/{id}` | Güncelle (ad, hedef, alarm) |
| DELETE | `/products/{id}` | Sil |
| POST | `/products/{id}/check` | Anlık fiyat kontrolü |
| POST | `/products/{id}/recalibrate` | CSS seçiciyi yenile |
| GET | `/products/{id}/history` | Fiyat geçmişi |
| POST | `/check-all` | Tüm ürünleri toplu kontrol |

Swagger UI: `http://localhost:8001/docs`

## Yerel Geliştirme

```bash
# Bağımlılıkları kur
pip install -r requirements.txt
playwright install chromium

# API'yi başlat
uvicorn api:app --reload --port 8001
```

## Docker ile Üretim

```bash
# .env dosyasını oluştur
cp env.example .env

# Build + başlat
make deploy

# HTTPS ile (Caddy)
DOMAIN=api.siteadin.com make up-proxy

# Yönetim
make logs        # canlı loglar
make shell       # container bash
make db-backup   # SQLite yedeği
make down        # durdur
```

## iOS Uygulaması

```bash
cd PriceTrackerApp
brew install xcodegen
xcodegen generate
open PriceTracker.xcodeproj
```

Ayarlar ekranından API adresini yapılandır: `http://<sunucu-ip>:8001`

## Notlar

- Ücretsiz kullanımda ürün ekleme reklamlı (5 sn rewarded ad).
- Premium üyeler reklamsız sınırsız ürün takip eder.
- Gerçek AdMob entegrasyonu için `PriceTrackerApp/Sources/PriceTracker/Services/AdService.swift` dosyasını güncelle.
- Gerçek StoreKit satın alma için `SettingsViewModel.swift` → `purchasePremium()` metodunu güncelle.
