import json
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver

USUAL_SEARCH_LINK = "https://asunnot.oikotie.fi/myytavat-asunnot?pagination=1&locations=%5B%5B65,6,%22Vantaa%22%5D,%5B64,6,%22Helsinki%22%5D,%5B39,6,%22Espoo%22%5D%5D&cardType=100&roomCount%5B%5D=2&roomCount%5B%5D=3&roomCount%5B%5D=4&roomCount%5B%5D=5&roomCount%5B%5D=6&roomCount%5B%5D=7&price%5Bmin%5D=150000&price%5Bmax%5D=300000&size%5Bmin%5D=70&lotOwnershipType%5B%5D=1&constructionYear%5Bmin%5D=2010"


class BaseScrapper(object):
    content = None
    link = None

    def __init__(self, link=None):
        self.link = link
        self.get_html_from_link()

    def get_html_from_link(self):
        link = self.link or USUAL_SEARCH_LINK
        driver = webdriver.Chrome()
        driver.get(link)
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        time.sleep(3)
        html = driver.page_source
        self.content = html
        driver.quit()

    def clean_text(self, text):
        if not text:
            return
        text = text.replace(u'\xa0', u' ')
        text = text.replace(u'\n', u'')
        text = text.replace(u'\t', u'')
        return text

    def _select(self, div, path, index=0):
        try:
            return div.select(path)[index]
        except IndexError:
            return

    def text_from_html(self, div):
        if div:
            return self.clean_text(div.get_text())


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
                "price": self.text_from_html(
                    self._select(a, 'div.ot-card__body section.ot-card__price-size span.ot-card__price')),
                "size": self.text_from_html(
                    self._select(a, 'div.ot-card__body section.ot-card__price-size span.ot-card__size')),
                "room_conf": self.text_from_html(self._select(a, 'div.ot-card__body section', 1)),
                "year": self.text_from_html(self._select(self._select(a, 'div.ot-card__body section', 2), 'span', 1)),
                "house_type": self.text_from_html(
                    self._select(self._select(a, 'div.ot-card__body section', 2), 'span')),
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
            "price_per_square_meter": self._get_val_from_table(soup, u"Neliöhinta"),
            "housing_company": company
        }
        return details


def get_list_of_apartment_with_details():
    scrapper = OikotieScraper()
    apartments = scrapper.scrape_apartment_lists()
    details = []
    for a in apartments:
        apartment_scrapper = OikotieScraper(link=a["link"])
        detail = apartment_scrapper.scrape_apartment_details()
        a.update(detail)
        details.append(a)


