import scrapy
from scrapy.http import Response
from gb_parse.items import GbParseItem
import base64
import re


class AutoyoulaSpider(scrapy.Spider):
    name = "autoyoula"
    allowed_domains = ["auto.youla.ru"]
    start_urls = ["https://auto.youla.ru/"]
    css_query = {
        "brand": "div.ColumnItemList_container__5gTrc a.blackLink",
        "pagination": "div.Paginator_block__2XAPy a.Paginator_button__u1e7D",
        "ads": "article.SerpSnippet_snippet__3O1t2 a.SerpSnippet_name__3F7Yu",
    }

    data_query = {
        "title": "div.AdvertCard_advertTitle__1S1Ak::text",
        "price": "div.AdvertCard_price__3dDCr::text",
        "description": "div.AdvertCard_descriptionInner__KnuRi::text",
    }

    @staticmethod
    def get_specs(response: Response) -> dict:
        specs = {}
        advert_specs = response.css('div.AdvertSpecs_row__ljPcX')
        for advert_spec in advert_specs:
            spec_name = advert_spec.css('div.AdvertSpecs_label__2JHnS::text').get()
            if advert_spec.css('div.AdvertSpecs_data__xK2Qx a.blackLink'):
                # Значение характеристики - ссылка
                specs[spec_name] = advert_spec.css('div.AdvertSpecs_data__xK2Qx a.blackLink::text').get()
            else:
                # Значение характеристики - обычный текст
                specs[spec_name] = advert_spec.css('div.AdvertSpecs_data__xK2Qx::text').get()
        return specs

    @staticmethod
    def decode_url(url: str) -> str:
        # Расшифровываем элементы в соответствии с правилами URL-encoding
        url = url.replace('%3A', ':')
        url = url.replace('%2F', '/')
        return url

    @staticmethod
    def decode_phone(phone: str) -> str:
        phone = phone.replace('%3D', '=')
        # Изучив код сайта пришел к выводу, что телефон зашифрован с помощью Base64
        # Для дешировки необходимо действовать следующим образом:
        # 1. Дешифровать исходный текст с помощью Base64
        # 2. Отбросить символ '_' в конце получившейся строки и результат снова дешифровать с помощью Base64
        # 3. Получившуюся байтовую строку преобразовать обычную
        phone = base64.b64decode(base64.b64decode(phone)[:-1]).decode('utf-8')
        return phone

    def get_advert_details_js(self, response: Response) -> dict:
        transit_state = '<script>window.transitState'
        scripts = response.css('script')
        for script in scripts:
            # Нас интересует только скрипт с transitState
            script_code = script.get()
            if script.get().startswith(transit_state):
                # Сначала воспользуемся регулярными выражениями, чтобы найти ссылки на все фотографии
                pattern = re.compile('photo%22%2C%22big%22%2C%22(https%3A%2F%2F'
                                     'static.am%2Fautomobile_m3%2Fdocument%2F\w{1,}%2F\w{1,}%2F\w{1,}%2F\w{1,}.jpe?g)')
                photos = [self.decode_url(photo) for photo in re.findall(pattern, script_code)]

                # Аналогично используем регулярные выражения, чтобы достать id пользователя
                pattern = re.compile('youlaId%22%2C%22(\w{1,})%22%2C%22')
                user_id = re.findall(pattern, script_code)[1]
                user = 'https://youla.ru/user/' + user_id

                # Аналогично используем регулярные выражения, чтобы достать телефон пользователя
                pattern = re.compile('phone%22%2C%22(\w{1,}%3D%3D)%22%2C%22')
                phones = [self.decode_phone(phone) for phone in re.findall(pattern, script_code)]

        return {
            'photos': photos,
            'phones': phones,
            'user': user,
        }

    @staticmethod
    def gen_task(response, list_links, callback):
        for link in list_links:
            yield response.follow(link.attrib.get("href"), callback=callback)

    def parse(self, response: Response):
        yield from self.gen_task(response, response.css(self.css_query["brand"]), self.brand_parse)

    def brand_parse(self, response: Response):
        yield from self.gen_task(
            response, response.css(self.css_query["pagination"]), self.brand_parse
        )
        yield from self.gen_task(response, response.css(self.css_query["ads"]), self.ads_parse)

    def ads_parse(self, response: Response):
        data = GbParseItem()
        # Название объявления, цена и описание
        for name, query in self.data_query.items():
            if name == 'price':
                data[name] = float(response.css(query).get().replace('\u2009', ''))
            else:
                data[name] = response.css(query).get()

        # Характеристики
        data['specs'] = self.get_specs(response)

        # Ссылка на пользователя, цена и телефон
        data.update(self.get_advert_details_js(response))

        return data
