from urllib.parse import urljoin
from scrapy.loader import ItemLoader
from .items import Vacancy, Employer
from itemloaders.processors import TakeFirst, MapCompose, Join


def clean_output(itm):
    return itm.replace("\xa0", " ")


def get_employer(item):
    new_item = []
    for _ in item:
        if _ not in new_item and _ != " ":
            new_item.append(_)
    return " ".join(new_item)


class VacancyLoader(ItemLoader):
    default_item_class = Vacancy
    url_out = TakeFirst()
    title_out = TakeFirst()
    salary_in = MapCompose(clean_output)
    salary_out = Join('')
    description_in = MapCompose(clean_output)
    description_out = Join(' ')
    skills_in = MapCompose(clean_output)
    employer_in = MapCompose(clean_output)
    employer_out = get_employer
    employer_url_in = MapCompose(lambda url: urljoin("https://hh.ru/", url))
    employer_url_out = TakeFirst()


class EmployerLoader(ItemLoader):
    default_item_class = Employer
    name_in = MapCompose(clean_output)
    name_out = get_employer
    site_out = TakeFirst()
    business_fields_out = MapCompose(lambda fields: [field.capitalize() for field in fields.split(', ')])
    description_in = MapCompose(clean_output)
    description_out = Join('')
    url_out = TakeFirst()
