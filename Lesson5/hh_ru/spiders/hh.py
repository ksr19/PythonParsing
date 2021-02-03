import scrapy
import re
from scrapy.http import Response
from ..loaders import VacancyLoader, EmployerLoader


class HhSpider(scrapy.Spider):
    name = 'hh'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113/']

    vacancy_data_xpath = {
        'title': '//h1[@data-qa="vacancy-title"]/text()',
        'salary': '//p[@class="vacancy-salary"]//text()',
        'description': '//div[@class="vacancy-description"]//div['
                       'contains(@class, "bloko-gap") or'
                       'contains(@class, "g-user-content") or '
                       'contains(@class, "tmpl_hh_wrapper")]//text()',
        'skills': '//div[contains(@data-qa, "skills-element")]//text()',
        'employer': '//div[contains(@class, "details")]//text()',
        'employer_url': '//a[@data-qa="vacancy-company-name"]/@href',
    }

    employer_data_xpath = {
        'name': '//span[@data-qa="company-header-title-name"]/text()',
        'site': '//a[@data-qa="sidebar-company-site"]/@href',
        'business_fields': '//div[@class="employer-sidebar-block"]/p/text()',
        'description': '//div[@class="company-description"]//text()',
    }

    @staticmethod
    def gen_task(response, list_links, callback):
        for link in list_links:
            yield response.follow(link.attrib.get("href"), callback=callback)

    @staticmethod
    def gen_employer_vacancy_task(response, callback):
        pattern = re.compile('"vacancyId"\:\s(\d+),')
        vacancies = ["https://hh.ru/vacancy/" + vacancy_id
                     for vacancy_id in re.findall(pattern, response.xpath('//template//text()').get())]
        for vacancy in vacancies:
            yield response.follow(vacancy, callback=callback)

    def parse(self, response: Response, **kwargs):
        yield from self.gen_task(
            response, response.xpath('//span[@class="bloko-button-group"]//a'), self.parse
        )
        yield from self.gen_task(
            response, response.xpath('//a[contains(@data-qa, "vacancy-serp__vacancy-title")]'), self.vacancy_parse
        )
        yield from self.gen_task(
            response, response.xpath('//div[contains(@class, "meta-info-company")]//a'), self.employer_parse
        )

    def vacancy_parse(self, response: Response):
        loader = VacancyLoader(response=response)
        for key, selector in self.vacancy_data_xpath.items():
            loader.add_xpath(key, selector)
        loader.add_value('url', response.url)
        yield loader.load_item()

    def employer_parse(self, response: Response):
        loader = EmployerLoader(response=response)
        if response.xpath(self.employer_data_xpath['name']):
            # Переходим по следующим ссылкам работодателя только если добавляем его в БД
            yield from self.gen_employer_vacancy_task(
                response, self.vacancy_parse
            )
            for key, selector in self.employer_data_xpath.items():
                loader.add_xpath(key, selector)
            loader.add_value('url', response.url)
            yield loader.load_item()
        return None
