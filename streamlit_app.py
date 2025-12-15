import streamlit as st

import database
from calibrate import calibrate_and_add_product
from tracker import get_product_price


@st.cache_resource
def init_db():
    database.setup_database()
    return True


def page_add_product():
    st.header("Yeni Ürün Ekle")
    st.write(
        "Takip etmek istediğiniz ürünün linkini ve sayfada gördüğünüz fiyatı girin. "
        "Fiyat elementi otomatik bulunup kaydedilecektir."
    )

    with st.form("add_product_form"):
        url = st.text_input("Ürün URL")
        name = st.text_input(
            "Ürün adı",
            placeholder="Örn: TriArte T-Shirt",
        )
        visible_price = st.text_input(
            "Sayfada gördüğünüz fiyat",
            placeholder="Örn: 229,99 TL (kopyala-yapıştır da olur)",
        )
        target_price = st.text_input(
            "Hedef fiyat",
            placeholder="Örn: 199,99",
        )

        submitted = st.form_submit_button("Ürünü ekle ve kalibre et")

    if submitted:
        init_db()
        try:
            result = calibrate_and_add_product(url, visible_price, target_price, name=name or None)
            st.success("Ürün başarıyla eklendi ve takip edilmeye başlandı.")
            with st.expander("Detaylar"):
                st.write(f"Ad: {result.get('name') or '(isim verilmedi)'}")
                st.write(f"URL: {result['url']}")
                st.write(f"İlk fiyat: {result['initial_price']}")
                st.write(f"Hedef fiyat: {result['target_price']}")
                st.code(result["selector"], language="text")
        except Exception as exc:
            st.error(f"İşlem başarısız: {exc}")


def page_list_and_check():
    st.header("Takip Edilen Ürünler")
    init_db()
    products = database.get_all_products()

    if not products:
        st.info("Henüz takip edilen ürün yok. Önce 'Yeni Ürün Ekle' sekmesinden ürün ekleyin.")
        return

    # Ürünleri isim odaklı bir tablo olarak göster
    rows = []
    for p in products:
        rows.append(
            {
                "Ürün Adı": p.get("name") or "(isim yok)",
                "URL": p["url"],
                "İlk Fiyat": p["initial_price"],
                "Hedef Fiyat": p["target_price"],
                "Son Fiyat": p["current_price"],
                "Son Kontrol": p["last_checked_at"],
            }
        )
    st.table(rows)

    if st.button("Tüm ürünlerin fiyatlarını şimdi kontrol et"):
        for p in products:
            url = p["url"]
            selector = p["price_selector"] if "price_selector" in p.keys() else None
            try:
                current_price = get_product_price(url, selector)
                database.update_product_price(p["id"], current_price)
                status = (
                    "HEDEFİN ALTINDA ✅"
                    if current_price <= p["target_price"]
                    else "Takipte"
                )
                st.success(
                    f"{p.get('name') or p['url']} -> {current_price} (Hedef: {p['target_price']}) - {status}"
                )
            except Exception as exc:
                st.error(f"{p.get('name') or p['url']} için hata: {exc}")

    st.markdown("---")
    st.subheader("Ürün linkleri")
    for p in products:
        label = p.get("name") or p["url"]
        st.link_button(f"Ürüne git: {label}", p["url"])


def main():
    st.set_page_config(page_title="Price Tracker", layout="wide")
    st.title("💰 Price Tracker")
    st.write(
        "Ürün fiyatlarını web sayfasından otomatik tespit edip hedef fiyata düşünceye kadar takip eden basit bir araç."
    )

    tab1, tab2 = st.tabs(["Yeni Ürün Ekle", "Takip & Liste"])

    with tab1:
        page_add_product()
    with tab2:
        page_list_and_check()


if __name__ == "__main__":
    main()


