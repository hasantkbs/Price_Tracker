from .generic_scraper import GenericScraper
# Import other specific scrapers here

def get_scraper(url):
    # In the future, we can add logic here to select the correct scraper
    # based on the domain of the url.
    # For now, we only have the generic scraper.
    return GenericScraper(url)
