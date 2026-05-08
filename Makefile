COMPOSE      = docker compose
COMPOSE_DEV  = $(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml
IMAGE        = price-tracker-api
TAG         ?= latest

.PHONY: help build build-no-cache up down restart logs shell \
        dev dev-down test health db-backup db-restore deploy

# ── Varsayılan hedef ─────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  Price Tracker — Docker komutları"
	@echo ""
	@echo "  Üretim:"
	@echo "    make build         Image'ı oluştur"
	@echo "    make up            Servisleri başlat (arka planda)"
	@echo "    make down          Servisleri durdur"
	@echo "    make restart       Yeniden başlat"
	@echo "    make logs          Canlı log izle"
	@echo "    make shell         API container'ına bash aç"
	@echo "    make health        Sağlık durumunu kontrol et"
	@echo "    make deploy        Build + Up (tam yayımlama)"
	@echo ""
	@echo "  HTTPS (Caddy) ile üretim:"
	@echo "    DOMAIN=api.ornek.com make up-proxy"
	@echo ""
	@echo "  Geliştirme:"
	@echo "    make dev           Hot-reload ile geliştirme ortamını başlat"
	@echo "    make dev-down      Geliştirme ortamını durdur"
	@echo ""
	@echo "  Veritabanı:"
	@echo "    make db-backup     SQLite'ı yerel dizine yedekle"
	@echo "    make db-restore F=yedek.db   Yedeği geri yükle"
	@echo ""

# ── Üretim ───────────────────────────────────────────────────────────────────
build:
	$(COMPOSE) build --pull

build-no-cache:
	$(COMPOSE) build --no-cache --pull

up:
	$(COMPOSE) up -d
	@echo ""
	@echo "  API çalışıyor: http://localhost:$$(grep API_PORT .env 2>/dev/null | cut -d= -f2 || echo 8001)"
	@echo "  Swagger UI:   http://localhost:$$(grep API_PORT .env 2>/dev/null | cut -d= -f2 || echo 8001)/docs"

up-proxy:
	$(COMPOSE) --profile proxy up -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart api

logs:
	$(COMPOSE) logs -f api

shell:
	$(COMPOSE) exec api bash

health:
	@curl -sf http://localhost:$$(grep API_PORT .env 2>/dev/null | cut -d= -f2 || echo 8001)/health \
	  | python3 -m json.tool \
	  && echo "  Sunucu sağlıklı." \
	  || echo "  Sunucu yanıt vermiyor!"

deploy: build up health

# ── Geliştirme ────────────────────────────────────────────────────────────────
dev:
	$(COMPOSE_DEV) up

dev-down:
	$(COMPOSE_DEV) down

# ── Veritabanı ────────────────────────────────────────────────────────────────
db-backup:
	@STAMP=$$(date +%Y%m%d_%H%M%S); \
	$(COMPOSE) exec api sh -c \
	  "sqlite3 /app/data/price_tracker.db '.backup /tmp/backup.db'" && \
	$(COMPOSE) cp api:/tmp/backup.db ./backup_$$STAMP.db && \
	echo "  Yedek oluşturuldu: backup_$$STAMP.db"

db-restore:
	@if [ -z "$(F)" ]; then echo "Kullanım: make db-restore F=yedek.db"; exit 1; fi
	$(COMPOSE) cp $(F) api:/tmp/restore.db
	$(COMPOSE) exec api sh -c \
	  "cp /app/data/price_tracker.db /app/data/price_tracker.db.bak && \
	   sqlite3 /app/data/price_tracker.db '.restore /tmp/restore.db'"
	@echo "  Geri yükleme tamamlandı. Eski DB: price_tracker.db.bak"
