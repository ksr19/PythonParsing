import os
import time
import datetime as dt
import requests
from dotenv import load_dotenv
import bs4
from urllib.parse import urljoin
import database


class ParseError(Exception):
    def __init__(self, text):
        self.text = text


class GbParse:

    def __init__(self, start_url, db):
        self.db = db
        self.start_url = start_url
        self.done_url = set()
        self.tasks = [self.parse_task(self.start_url, self.pag_parse)]
        self.done_url.add(self.start_url)

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

    def _get_soup(self, url, *args, **kwargs):
        response = self._get_response(url, *args, **kwargs)
        return bs4.BeautifulSoup(response.text, "lxml")

    def parse_task(self, url, callback):
        def task():
            soup = self._get_soup(url)
            return callback(url, soup)

        return task

    def run(self):
        for task in self.tasks:
            result = task()
            if result:
                self.save(result)

    def pag_parse(self, url, soup):
        self.create_parse_tasks(
            url, soup.find("ul", attrs={"class": "gb__pagination"}).find_all("a"), self.pag_parse
        )
        self.create_parse_tasks(
            url,
            soup.find("div", attrs={"class": "post-items-wrapper"}).find_all(
                "a", attrs={"class": "post-item__title"}
            ),
            self.post_parse,
        )

    def create_parse_tasks(self, url, tag_list, callback):
        for a_tag in tag_list:
            a_url = urljoin(url, a_tag.get("href"))
            if a_url not in self.done_url:
                task = self.parse_task(a_url, callback)
                self.tasks.append(task)
                self.done_url.add(a_url)

    def post_parse(self, url, soup):
        post_data = {
            "title": soup.find("h1", attrs={"class": "blogpost-title"}).text,
            "url": url,
            "image": soup.find("img").get("src"),
            "date": dt.datetime.strptime(soup.find("time", attrs={"itemprop": "datePublished"}).get("datetime"),
                                         "%Y-%m-%dT%H:%M:%S%z"),
        }
        author_tag_name = soup.find("div", attrs={"itemprop": "author"})
        author = {
            "name": author_tag_name.text,
            "url": urljoin(url, author_tag_name.parent.get("href")),
        }
        tags_a = soup.find("article", attrs={"class": "blogpost__article-wrapper"}).find_all(
            "a", attrs={"class": "small"}
        )
        tags = [{"url": urljoin(url, tag.get("href")), "name": tag.text} for tag in tags_a]

        # Номер поста, который используется для подгрузки скриптом комментариев
        post_id = int(soup.find("comments").get("commentable-id"))
        comments = self.comments_parse(post_id)

        return {
            "post_data": post_data,
            "author": author,
            "tags": tags,
            "comments": comments,
        }

    def comments_parse(self, post_id):
        _params = {
            "commentable_type": "Post",
            "commentable_id": post_id,
        }
        comments = []
        url_comment = "https://geekbrains.ru/api/v2/comments"
        response = self._get_response(url_comment, params=_params)
        data = response.json()
        if data:
            for comment in data:
                info = self._get_details(comment["comment"])
                comments += info
        return comments

    def _get_details(self, comment):
        comment_id = comment["id"]
        text = comment["body"]
        user = comment["user"]["full_name"]
        user_url = comment["user"]["url"]
        parent_id = comment["parent_id"]
        # created_at = comment["created_at"]
        comment_details = [{
            "comment_id": comment_id,
            "text": text,
            "author": user,
            "url": user_url,
            "parent_id": parent_id,
            # "time": created_at
        }]
        # Если есть ответы к комментарию
        if comment["children"]:
            for child_comment in comment["children"]:
                comment_details += self._get_details(child_comment["comment"])
        return comment_details

    def save(self, data):
        self.db.create_post(data)


if __name__ == "__main__":
    load_dotenv(".env")
    db = database.Database(os.getenv("SQL_DB_URL"))
    parser = GbParse("https://geekbrains.ru/posts", db)
    parser.run()
