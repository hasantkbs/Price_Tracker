from .base_scraper import BaseScraper

class GenericScraper(BaseScraper):
    def get_product_name(self):
        # Try to find the product name from common tags
        name_tags = self.soup.find_all(['h1', 'h2', 'title'])
        for tag in name_tags:
            if tag.string:
                return tag.string.strip()
        return "Unknown"

    def get_product_price(self):
        # Try to find the product price from common tags and classes
        price_tags = self.soup.find_all(text=lambda t: t and '₺' in t)
        for tag in price_tags:
            # This is a very basic price extraction, might need improvement
            try:
                price_str = ''.join(filter(str.isdigit, tag))
                if price_str:
                    return float(price_str) / 100
            except ValueError:
                continue
        return 0.0

    def get_product_image(self):
        # Try to find the product image from common tags
        img_tags = self.soup.find_all('img')
        for tag in img_tags:
            if 'src' in tag.attrs:
                return tag['src']
        return "Unknown"
