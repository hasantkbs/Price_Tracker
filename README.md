## Price Tracker

A Python-based backend + Streamlit frontend to track product prices from e‑commerce websites.

### Description

This project monitors the price of products given their URLs.  
It stores product information (URL, initial price, current price, target price, and a stable CSS selector for the price element) in a local SQLite database.  
A tracker periodically loads the product pages (with Playwright), extracts the current price, updates the database, and marks products whose price fell below the target.

The project uses:
- `playwright` to handle dynamic, JavaScript-heavy websites.
- An automatic calibration routine (`calibrate.py`) to identify the correct price element on the page using the visible price you entered.
- A small command-line menu (`app.py`) and a Streamlit web UI (`streamlit_app.py`) for normal users.

### Features

- **Automatic Price Calibration**:  
  Users only provide the product URL and the visible price text (e.g. `229,99 TL`); the system automatically finds the correct HTML element and stores a stable CSS selector.
- **Dynamic Content Handling**:  
  Uses `playwright` (Chromium) to render JavaScript on web pages, handle cookie dialogs/popups, scroll, and wait until the price is present in the DOM.
- **Persistent Tracking**:  
  All products are stored in an SQLite database (`price_tracker.db`) for long‑term tracking.
- **Price Checking Engine**:  
  `tracker.py` can be used to periodically re-check all stored products and update their current prices.
- **Streamlit Frontend**:  
  `streamlit_app.py` exposes a web UI with:
  - **“Add Product”** tab to add & calibrate a new product.
  - **“Track & List”** tab to list tracked products and manually trigger a price check.

---

## Local Usage

### 1. Setup

Create / activate a virtual environment (optional but recommended) and install dependencies:

```bash
pip install -r requirements.txt
```

Then, install the necessary browser binaries for Playwright:

```bash
playwright install
```

### 2. Run the Streamlit Web App

From the project root:

```bash
streamlit run streamlit_app.py
```

The app will open in your browser. You can:
- Add new products from the **“Add Product”** tab.
- See and check all products from the **“Track & List”** tab.

### 3. Command-Line Interface (Optional)

If you prefer using the CLI instead of Streamlit:

```bash
python app.py
```

You will see a simple menu:
- **1)** Add a new product (URL + visible price + target price)
- **2)** Check prices once
- **3)** Start continuous tracking loop
- **4)** Exit

You can still run the raw tracker loop directly:

```bash
python tracker.py
```

This will continuously check all tracked products every N minutes (configurable in `tracker.run_loop`).

---

## Deploying on Streamlit Cloud

1. Push this project to a GitHub repository.  
2. On Streamlit Cloud:
   - Select the repository and branch.
   - Set the **entry file** to `streamlit_app.py`.
3. Make sure `requirements.txt` is detected and installed automatically.

> Note: Playwright might require additional configuration on some hosting platforms (headless Chromium, sandbox flags, etc.).  
> If you hit issues there, you can temporarily fall back to a `requests + BeautifulSoup`‑only version of the price fetching logic.

---

## Limitations

- Some major e‑commerce platforms use advanced anti‑bot measures (e.g. aggressive bot detection, CAPTCHAs, strong WAF rules).  
- In those cases, Playwright may be blocked, or the price may not be returned reliably.  
- Bypassing such protection can require advanced techniques (proxy rotation, CAPTCHA solving services) which are **out of scope** for this simple demo project.

