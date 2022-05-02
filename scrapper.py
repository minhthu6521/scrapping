import re
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

USUAL_SEARCH_LINK = "https://asunnot.oikotie.fi/myytavat-asunnot?pagination=1&habitationType%5B%5D=1&locations=%5B%5B64,6,%22Helsinki%22%5D,%5B65,6,%22Vantaa%22%5D,%5B39,6,%22Espoo%22%5D%5D&price%5Bmin%5D=200000&price%5Bmax%5D=380000&size%5Bmin%5D=72&constructionYear%5Bmin%5D=2012&cardType=100"
USER_AGENT = 'user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"'

PRICE = re.compile("(\d| |,)+")

HEATING_MAPPING = {
    "kaukolämpö": "normal",
    "maalämpö": "GEOTHERMAL"
}


class BaseScrapper(object):
    content = None
    link = None

    def __init__(self, link=None, user_agent=None):
        self.link = link or USUAL_SEARCH_LINK
        self.user_agent = user_agent or USER_AGENT
        self.get_html_from_link()

    def get_html_from_link(self):
        chrome_options = Options()
        chrome_options.add_argument(self.user_agent)
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(self.link)
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        time.sleep(3)
        html = driver.page_source
        self.content = html
        driver.quit()

    def clean_text(self, text):
        if not text:
            return
        text = text.replace(u'\xa0', u' ').replace(u'\n', u'').replace(u'\t', u'')
        return text

    def _select(self, div, path, index=0):
        try:
            return div.select(path)[index]
        except IndexError:
            return

    def text_from_html(self, div):
        if div:
            return self.clean_text(div.get_text())

    @classmethod
    def extract_number(cls, num):
        return float(PRICE.match(num)[0].replace(" ", "").replace(",", ".")) if num else 0


class OikotieScraper(BaseScrapper):
    def scrape_apartment_lists(self):
        soup = BeautifulSoup(self.content, features="html5lib")
        apartments_html = soup.find_all('div', class_='cards__card ng-scope')
        apartments = []
        for a in apartments_html:
            apartment = {
                "link": a.select('card a')[0].get("ng-href"),
                "address": self.text_from_html(self._select(a, 'div.ot-card__address .ot-card__street')),
                "location": self.clean_text(
                    ", ".join([t.get_text() for t in a.select('div.ot-card__address .ot-card__text span')])),
                "price": self.extract_number(self.text_from_html(
                    self._select(a, 'div.ot-card__body section.ot-card__price-size span.ot-card__price'))),
                "size": self.text_from_html(
                    self._select(a, 'div.ot-card__body section.ot-card__price-size span.ot-card__size')),
                "room_conf": self.text_from_html(self._select(a, 'div.ot-card__body section', 1)),
                "year": self.text_from_html(self._select(a, 'span[ng-bind="$ctrl.card.building.year"]', 0)),
                "house_type": self.text_from_html(self._select(a, 'span[ng-if="$ctrl.card.subType"]', 0))
            }
            apartments.append(apartment)
        return apartments

    def _get_val_from_table(self, html, text):
        value = html.find('dt', class_='info-table__title', text=text)
        value = self.text_from_html(value.next_sibling.next_sibling) if value else ""
        return value

    def scrape_apartment_details(self):
        soup = BeautifulSoup(self.content, features="html5lib")
        company = soup.select("div.listing-header__company-link a")
        if len(company) > 0:
            company = company[0].get("href")
        details = {
            "maintenance_fee": self._get_val_from_table(soup, "Hoitovastike"),
            "heating": self._get_val_from_table(soup, u"Lämmitys"),
            "price_per_square_meter": self.extract_number(self._get_val_from_table(soup, u"Neliöhinta")),
            "energy_class": self._get_val_from_table(soup, u"Energialuokka"),
            "housing_company": company
        }
        return details

    def get_list_with_details(self):
        apartments = self.scrape_apartment_lists()
        details = []
        for a in apartments:
            apartment_scrapper = self.__class__(link=a["link"])
            detail = apartment_scrapper.scrape_apartment_details()
            a.update(detail)
            details.append(a)
        return sorted(details, key=lambda x: x["price_per_square_meter"])


def get_list_of_apartment_with_details():
    scrapper = OikotieScraper()
    return scrapper.get_list_with_details()
