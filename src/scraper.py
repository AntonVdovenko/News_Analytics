"""Scraper class to get news from RTS feed"""
import datetime

import bs4
import pandas as pd
import requests

from bs4 import BeautifulSoup


# TODO: finish documentation
class RTScraper:
    def __init__(
        self,
        rss_link: str,
    ):
        self.rss_link = rss_link
        return

    def get_latest_news(self) -> pd.DataFrame:
        """_summary_

        Returns
        -------
        pd.DataFrame
            _description_
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

    def __get_news(self):
        """_summary_

        Returns
        -------
        _type_
            _description_
        """
        html_page = requests.get(self.rss_link).text
        html_page = BeautifulSoup(html_page, "html.parser")
        news = html_page.findAll("item")
        return news

    def __get_publication_time(
        self,
        piece_of_new: bs4.element.Tag,
    ) -> datetime.datetime:
        """_summary_

        Parameters
        ----------
        piece_of_new : bs4.element.Tag
            _description_

        Returns
        -------
        datetime.datetime
            _description_
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
        """_summary_

        Parameters
        ----------
        piece_of_new : bs4.element.Tag
            _description_

        Returns
        -------
        str
            _description_
        """
        # TODO: Надо дописать, оч кривая структура
        description = piece_of_new.find("description")
        if "img alt" in description.text:
            raw_text = description.text.split("<br")[0].split(">")[-1]
        else:
            raw_text = description.text.split("<br")[0]
        return "".join(
            [char for char in raw_text if char.isalnum() or char == " "]
        ).strip()
