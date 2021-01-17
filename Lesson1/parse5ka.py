import json
import time
from pathlib import Path
import requests

"""
1xx
2xx
3xx
4xx
5xx
"""

"""
GET
POST
PATCH
DELETE
"""


class ParseError(Exception):
    def __init__(self, text):
        self.text = text


class Parse5ka:
    _headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0",
    }
    _params = {
        "records_per_page": 50,
        "categories": None
    }

    def __init__(self, url_products: str, url_categories: str,
                 result_path_products: Path, result_path_categories: Path):
        self.url_products = url_products
        self.url_categories = url_categories
        self.result_path_products = result_path_products
        self.result_path_categories = result_path_categories

    @staticmethod
    def __get_response(url: str, *args, **kwargs) -> requests.Response:
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

    def run(self):
        for product in self.parse(self.url_products):
            file_path = self.result_path_products.joinpath(f'{product["id"]}.json')
            self.save(product, file_path)

        # Создание словарей для каждой категории
        for category in self.get_categories(self.url_categories):
            file_path = self.result_path_categories.joinpath(f'{category["parent_group_code"]}.json')
            products = []
            self._params["categories"] = category["parent_group_code"]
            for product in self.parse(self.url_products):
                products.append(product)
            result_dict = {
                "name": category["parent_group_name"],
                "code": category["parent_group_code"],
                "products": products
            }
            self.save(result_dict, file_path)

    def parse(self, url: str) -> dict:
        while url:
            response = self.__get_response(
                url, params=self._params, headers=self._headers
            )
            data = response.json()
            url = data["next"]
            for product in data["results"]:
                yield product

    @staticmethod
    def save(data: dict, file_path: Path):
        with file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False)

    # Получение категорий
    def get_categories(self, url: str) -> dict:
        response = self.__get_response(
            url, params=self._params, headers=self._headers
        )
        categories = response.json()
        for category in categories:
            yield category


if __name__ == "__main__":
    url_products = "https://5ka.ru/api/v2/special_offers/"
    url_categories = "https://5ka.ru/api/v2/categories/"
    result_path_products = Path(__file__).parent.joinpath("products")
    result_path_categories = Path(__file__).parent.joinpath("categories")
    parser = Parse5ka(url_products, url_categories, result_path_products, result_path_categories)
    parser.run()
