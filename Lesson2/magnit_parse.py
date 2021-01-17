import os
import datetime
import time
import requests
from urllib.parse import urljoin
import bs4
import pymongo
from dotenv import load_dotenv


class ParseError(Exception):
    def __init__(self, text):
        self.text = text


class MagnitParser:
    _year = 2021
    _months = {"января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5,
               "июня": 6, "июля": 7, "августа": 8, "сентября": 9, "октября": 10,
               "ноября": 11, "декабря": 12}

    def __init__(self, start_url, data_client):
        self.start_url = start_url
        self.data_client = data_client
        self.data_base = self.data_client["gb_parse_13_01_2021"]

    @staticmethod
    def _get_response(url, *args, **kwargs):
        while True:
            try:
                response = requests.get(url, *args, **kwargs)
                if response.status_code > 399:
                    raise ParseError(response.status_code)
                time.sleep(0.1)
                return response
            except (requests.RequestException, ParseError):
                time.sleep(0.5)
                continue

    @staticmethod
    def _get_soup(response):
        return bs4.BeautifulSoup(response.text, "lxml")

    def run(self):
        for product in self.parse(self.start_url):
            self.save(product)

    def parse(self, url) -> dict:
        soup = self._get_soup(self._get_response(url))
        catalog_main = soup.find("div", attrs={"class": "сatalogue__main"})
        for product_tag in catalog_main.find_all("a", attrs={"class": "card-sale"}):
            yield self._get_product_data(product_tag)

    @property
    def data_template(self):
        return {
            "url": lambda tag: urljoin(self.start_url, tag.attrs.get("href")),
            "promo_name": lambda tag: tag.find('div', attrs={"class": "card-sale__name"}).text,
            "product_name": lambda tag: tag.find('div', attrs={"class": "card-sale__title"}).text,
            "old_price": self._get_old_price,
            "new_price": self._get_new_price,
            "image_url": lambda tag: urljoin(self.start_url, tag.find('img').attrs.get("data-src")),
            "date_from": self._get_start_date,
            "date_to": self._get_end_date
        }

    def _get_product_data(self, product_tag: bs4.Tag) -> dict:
        data = {}
        for key, pattern in self.data_template.items():
            try:
                data[key] = pattern(product_tag)
            except AttributeError:
                pass
        return data

    @staticmethod
    def _get_old_price(tag: bs4.Tag) -> float:
        integer = tag.find('div', attrs={"class": "label__price_old"}). \
            find('span', attrs={"class": "label__price-integer"}).text
        decimal = tag.find('div', attrs={"class": "label__price_old"}). \
            find('span', attrs={"class": "label__price-decimal"}).text
        return float(integer + "." + decimal)

    @staticmethod
    def _get_new_price(tag: bs4.Tag) -> float:
        integer = tag.find('div', attrs={"class": "label__price_new"}). \
            find('span', attrs={"class": "label__price-integer"}).text
        decimal = tag.find('div', attrs={"class": "label__price_new"}). \
            find('span', attrs={"class": "label__price-decimal"}).text
        return float(integer + "." + decimal)

    def _get_start_date(self, tag: bs4.Tag) -> datetime.datetime:
        sale_period = tag.find('div', attrs={"class": "card-sale__date"}).text.split()
        return datetime.datetime(self._year, self._months[sale_period[2]], int(sale_period[1]))

    def _get_end_date(self, tag: bs4.Tag) -> datetime.datetime:
        sale_period = tag.find('div', attrs={"class": "card-sale__date"}).text.split()
        return datetime.datetime(self._year, self._months[sale_period[-1]], int(sale_period[-2]))

    def save(self, data):
        collection = self.data_base["magnit"]
        collection.insert_one(data)
        pass


if __name__ == '__main__':
    load_dotenv(".env")
    data_base_url = os.getenv("DATA_BASE_URL")
    data_client = pymongo.MongoClient(data_base_url)
    url = "https://magnit.ru/promo/?geo=moskva"
    parser = MagnitParser(url, data_client)
    parser.run()
