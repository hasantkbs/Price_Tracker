from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import database
from calibrate import calibrate_and_add_product, recalibrate_product
from tracker import get_product_price

app = FastAPI(title="Price Tracker API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database.setup_database()


# ── Dependency ───────────────────────────────────────────────────────────────

async def get_user_id(x_user_id: Optional[str] = Header(None)):
    if not x_user_id:
        # For development/testing we might allow a default, 
        # but for production it should probably be required.
        # Apple might require a more robust auth if data is synced,
        # but a unique device ID is a good start for isolation.
        return "default_user"
    return x_user_id


# ── Request / Response modelleri ─────────────────────────────────────────────

class AddProductRequest(BaseModel):
    url: str
    name: Optional[str] = None
    price_text: str
    target_price: float
    alert_price: Optional[float] = None


class UpdateProductRequest(BaseModel):
    name: Optional[str] = None
    target_price: Optional[float] = None
    alert_price: Optional[float] = None
    alert_enabled: Optional[bool] = None


class RecalibrateRequest(BaseModel):
    current_price_text: str


# ── Yardımcı ─────────────────────────────────────────────────────────────────

def _product_or_404(product_id: int, user_id: str):
    p = database.get_product_by_id(product_id, user_id)
    if not p:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    return p


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/products")
def get_products(user_id: str = Depends(get_user_id)):
    return [dict(p) for p in database.get_all_products(user_id)]


@app.get("/products/{product_id}")
def get_product(product_id: int, user_id: str = Depends(get_user_id)):
    return dict(_product_or_404(product_id, user_id))


@app.post("/products", status_code=201)
def add_product(req: AddProductRequest, user_id: str = Depends(get_user_id)):
    try:
        result = calibrate_and_add_product(
            user_id, req.url, req.price_text, req.target_price, name=req.name
        )
        if req.alert_price is not None:
            product = database.get_product_by_url(user_id, req.url)
            if product:
                database.update_product_alert(product["id"], user_id, req.alert_price, True)
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/products/{product_id}")
def update_product(product_id: int, req: UpdateProductRequest, user_id: str = Depends(get_user_id)):
    _product_or_404(product_id, user_id)
    database.update_product_fields(
        product_id,
        user_id,
        name=req.name,
        target_price=req.target_price,
        alert_price=req.alert_price,
        alert_enabled=req.alert_enabled,
    )
    return {"success": True, "data": dict(database.get_product_by_id(product_id, user_id))}


@app.delete("/products/{product_id}")
def delete_product(product_id: int, user_id: str = Depends(get_user_id)):
    _product_or_404(product_id, user_id)
    database.delete_product(product_id, user_id)
    return {"success": True}


@app.post("/products/{product_id}/check")
def check_product_price(product_id: int, user_id: str = Depends(get_user_id)):
    """
    Ürün fiyatını tüm stratejilerle (JSON-LD, meta, seçici vb.) anlık çeker.
    Hangi stratejinin başarılı olduğunu 'source' alanında döner.
    """
    product = _product_or_404(product_id, user_id)
    selector = product["price_selector"]
    fail_count = product["selector_fail_count"] or 0
    active_selector = None if fail_count >= 3 else selector

    try:
        price, source = get_product_price(
            product["url"], active_selector, product["initial_price"]
        )
    except Exception as e:
        database.record_selector_failure(product_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))

    database.update_product_price(product_id, price, source)
    database.add_price_history(product_id, price, source)

    updated = database.get_product_by_id(product_id, user_id)
    alert_triggered = (
        updated["alert_enabled"] == 1
        and updated["alert_price"] is not None
        and price <= updated["alert_price"]
    )
    return {
        "success": True,
        "current_price": price,
        "source": source,
        "alert_triggered": alert_triggered,
        "selector_used": active_selector is not None,
        "product": dict(updated),
    }


@app.post("/products/{product_id}/recalibrate")
def recalibrate(product_id: int, req: RecalibrateRequest, user_id: str = Depends(get_user_id)):
    """
    Seçici stale olduğunda (veya kullanıcı istediğinde) sayfadan yeni seçici bulur.
    current_price_text: sayfada şu an görünen fiyat metni (örn: '1.299,00 TL')
    """
    _product_or_404(product_id, user_id)
    try:
        result = recalibrate_product(product_id, user_id, req.current_price_text)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/products/{product_id}/history")
def get_price_history(product_id: int, user_id: str = Depends(get_user_id), limit: int = 60):
    """Son N fiyat kaydını döner (varsayılan 60)."""
    _product_or_404(product_id, user_id)
    rows = database.get_price_history(product_id, limit)
    return [dict(r) for r in rows]


@app.post("/check-all")
def check_all_prices():
    """Tüm ürünlerin fiyatını toplu kontrol eder (arka plan işi gibi çalışır)."""
    # Not: Bu tüm kullanıcıların ürünlerini kontrol eder.
    products = database.get_all_products()
    results = []
    for product in products:
        pid = product["id"]
        fail_count = product["selector_fail_count"] or 0
        active_selector = None if fail_count >= 3 else product["price_selector"]
        try:
            price, source = get_product_price(
                product["url"], active_selector, product["initial_price"]
            )
            database.update_product_price(pid, price, source)
            database.add_price_history(pid, price, source)
            alert_triggered = (
                product["alert_enabled"] == 1
                and product["alert_price"] is not None
                and price <= product["alert_price"]
            )
            results.append({
                "id": pid,
                "name": product["name"],
                "current_price": price,
                "source": source,
                "alert_triggered": alert_triggered,
            })
        except Exception as e:
            database.record_selector_failure(pid, str(e))
            results.append({"id": pid, "error": str(e)})
    return {"results": results}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
