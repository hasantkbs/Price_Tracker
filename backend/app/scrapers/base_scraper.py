from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup

class BaseScraper(ABC):
    def __init__(self, url):
        self.url = url
        self.soup = self._get_soup()

    def _get_soup(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the URL: {e}")
            return None

    @abstractmethod
    def get_product_name(self):
        pass

    @abstractmethod
    def get_product_price(self):
        pass

    @abstractmethod
    def get_product_image(self):
        pass

    def get_product_info(self):
        if not self.soup:
            return None
        return {
            "name": self.get_product_name(),
            "price": self.get_product_price(),
            "image_url": self.get_product_image(),
            "product_url": self.url,
        }
