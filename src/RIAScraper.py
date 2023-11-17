"""Scraper class to get news from RIA News RSS feed"""
import datetime

import bs4
import pandas as pd
import requests

from bs4 import BeautifulSoup
from loguru import logger


class RIAScraper:
    def __init__(
        self,
        rss_link: str,
    ):
        """_summary_

        Args:
            rss_link (str): _description_
        """
        self.rss_link = rss_link
        return

    def get_latest_news(
        self,
    ) -> pd.DataFrame:
        """_summary_

        Returns:
            pd.DataFrame: _description_
        """
        news = self.__get_news()
        news_data = {
            "title": [],
            "link": [],
            "publication_time": [],
            "text": [],
        }
        for piece_of_new in news:
            news_data["title"].append(piece_of_new.find("title").text)
            news_data["link"].append(piece_of_new.find("guid").text)
            news_data["publication_time"].append(
                self.__get_publication_time(piece_of_new)
            )
            news_data["text"].append(self.__get_text(piece_of_new))
        return pd.DataFrame.from_dict(news_data)

    def __get_news(
        self,
    ) -> list:
        """_summary_

        Returns:
            list: _description_
        """
        html_page = requests.get(self.rss_link).text
        html_page = BeautifulSoup(html_page, "html.parser")
        news = html_page.findAll("item")
        logger.info(f"Length of news {len(news)}")
        return news

    def __get_publication_time(
        self,
        piece_of_new: bs4.element.Tag,
    ) -> datetime.datetime:
        """Func to extract date and time of publication, transform it to datetime

        Parameters
        ----------
        piece_of_new : bs4.element.Tag
            html piece of new to extract the date and time

        Returns
        -------
        datetime.datetime
            time of publication with timezone appointed
        """
        time_format = "%d %b %Y %H:%M:%S %z"
        time = piece_of_new.find("pubdate").text
        time = time.split(",")[1].strip()
        time = datetime.datetime.strptime(time, time_format)
        return time

    def __get_text(
        self,
        piece_of_new: bs4.element.Tag,
    ) -> str:
        """Func to get full text of piece of new and extract text from html

        Args:
            piece_of_new (bs4.element.Tag): _description_

        Returns:
            extracted and cleand text of piece of new
        """
        link = piece_of_new.find("guid").text
        full_page = requests.get(link).text
        full_page = BeautifulSoup(full_page, "html.parser")
        article_body = full_page.find("div", {"class": "page"}).find(
            "div", {"itemprop": "articleBody"}
        )
        return article_body.text.strip()


r = RIAScraper("https://ria.ru/export/rss2/index.xml")
print(r.get_latest_news())
