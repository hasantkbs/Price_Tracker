import re
from .base_scraper import BaseScraper

class GenericScraper(BaseScraper):
    def get_product_name(self):
        # Try Open Graph title
        og_title = self.soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        # Try schema.org name
        itemprop_name = self.soup.find("span", itemprop="name")
        if itemprop_name and itemprop_name.string:
            return itemprop_name.string.strip()

        # Try common heading tags
        name_tags = self.soup.find_all(['h1', 'h2'])
        for tag in name_tags:
            if tag.string:
                return tag.string.strip()
        
        # Fallback to title tag
        if self.soup.title and self.soup.title.string:
            return self.soup.title.string.strip()

        return None

    def get_product_price(self):
        # Try Open Graph price
        og_price = self.soup.find("meta", property="og:price:amount")
        if og_price and og_price.get("content"):
            try:
                return float(og_price["content"])
            except ValueError:
                pass

        # Try schema.org price
        itemprop_price = self.soup.find("span", itemprop="price")
        if itemprop_price and itemprop_price.string:
            try:
                return float(itemprop_price.string.strip())
            except ValueError:
                pass

        # Look for common price patterns
        price_patterns = [
            r'\$\s*(\d[\d,\.]*)',  # $1,234.56 or $1234
            r'€\s*(\d[\d,\.]*)',  # €1.234,56 or €1234
            r'₺\s*(\d[\d,\.]*)',  # ₺1.234,56 or ₺1234
            r'(\d[\d,\.]*)\s*TL', # 1.234,56 TL
            r'(\d[\d,\.]*)\s*EUR',# 1.234,56 EUR
            r'(\d[\d,\.]*)\s*USD',# 1.234,56 USD
        ]
        
        # Search for elements with common price classes or attributes
        price_selectors = [
            '.product-price', '.price', '.current-price', '.offer-price',
            '[data-price]', '[itemprop="price"]',
            lambda tag: tag.name in ['span', 'div', 'b'] and any(p in tag.get_text() for p in ['$', '€', '₺', 'TL', 'EUR', 'USD'])
        ]

        for selector in price_selectors:
            if callable(selector):
                tags = self.soup.find_all(selector)
            else:
                tags = self.soup.select(selector)
            
            for tag in tags:
                text = tag.get_text(strip=True)
                for pattern in price_patterns:
                    match = re.search(pattern, text)
                    if match:
                        price_str = match.group(1).replace('.', '').replace(',', '.') # Handle different decimal/thousand separators
                        try:
                            return float(price_str)
                        except ValueError:
                            pass
                if tag.has_attr('data-price'):
                    try:
                        return float(tag['data-price'])
                    except ValueError:
                        pass
        return None

    def get_product_image(self):
        # Try Open Graph image
        og_image = self.soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"].strip()

        # Try schema.org image
        itemprop_image = self.soup.find("img", itemprop="image")
        if itemprop_image and itemprop_image.get("src"):
            return itemprop_image["src"].strip()

        # Try common image tags
        img_tags = self.soup.find_all('img')
        for tag in img_tags:
            if 'src' in tag.attrs and tag['src'].startswith('http'): # Ensure it's a full URL
                return tag['src']
        return None
