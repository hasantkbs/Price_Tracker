# Price Tracker

A Python-based command-line application to track product prices from e-commerce websites.

## Description

This project provides a set of tools to monitor the price of a product from a given URL. It stores the product information, target price, and a specific CSS selector for the price element in a local SQLite database. A tracker script periodically checks the prices and notifies the user if the current price drops below the target price.

The project uses `playwright` to handle dynamic, JavaScript-heavy websites and a user-guided calibration script (`app.py`) to accurately identify the price on the page.

## Features

-   **User-Guided Price Calibration:** An interactive script (`app.py`) helps the user pinpoint the exact HTML element containing the price, ensuring high accuracy.
-   **Dynamic Content Handling:** Uses `playwright` to render JavaScript on web pages, allowing it to scrape prices from modern e-commerce sites.
-   **Persistent Tracking:** Stores products in an SQLite database for long-term tracking.
-   **Background Monitoring:** A separate script (`tracker.py`) runs in the background to continuously check for price updates.

## How to Use

### 1. Setup

First, install the required Python packages:

```bash
pip install -r requirements.txt
```

Then, install the necessary browser binaries for Playwright:

```bash
playwright install
```

### 2. Add a Product to Track

Run the `app.py` script to add a new product. This script will guide you through the calibration process.

```bash
python3 app.py
```

You will be prompted for:
- The product URL.
- The exact price text as it appears on the page (e.g., "29,99 TL").
- The correct CSS selector from a list of options.
- Your target price.

### 3. Start the Tracker

To begin monitoring the prices of the products in your database, run the `tracker.py` script.

```bash
python3 tracker.py
```

The script will check for price updates periodically and print a message if a product's price falls to or below your target.

## Limitations

Currently, the script may be blocked by advanced anti-bot measures on some major e-commerce platforms (like Trendyol). Bypassing this level of protection is a complex challenge and may require more advanced techniques like proxy rotation or CAPTCHA solving services.
