"""
This script implemets scraping interfaces for news websites 
"""
import datetime

from abc import ABC
from abc import abstractmethod

import bs4
import pandas as pd
import requests

from bs4 import BeautifulSoup
from loguru import logger


class ABCScraper(ABC):
    """
    Abstract class
    """

    def __init__(
        self,
        rss_link: str,
    ):
        """Init func keeping link to RSS feed

        Args:
            rss_link (str): link to RSS feed
        """
        self.rss_link = rss_link
        return

    @abstractmethod
    def get_latest_news(self) -> pd.DataFrame:
        """Func to get table with all news from current RSS feed structured

        Returns
        -------
        pd.DataFrame
            table with data regarding each piece of new including its title,
            link, publication time and text itself
        """
        ...

    @abstractmethod
    def _get_news(self) -> list:
        """Func to request current RSS feed and find all peieces of news

        Returns
        -------
        list
            list containing html pieces of news
        """
        ...

    @abstractmethod
    def _get_publication_time(
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
        ...

    @abstractmethod
    def _get_text(
        self,
        piece_of_new: bs4.element.Tag,
    ) -> str:
        """Func to get description of piece of new and extract text from html

        Parameters
        ----------
        piece_of_new : bs4.element.Tag
            html piece of new to extract the text

        Returns
        -------
        str
            extracted and cleand text of piece of new
        """
        ...


class GeneralScraper(ABCScraper):
    """
    General Scrapper
    """

    def __init__(
        self,
        rss_link: str,
    ):
        """Init func keeping link to RSS feed

        Args:
            rss_link (str): link to RSS feed
        """
        self.rss_link = rss_link
        return

    def get_latest_news(self) -> pd.DataFrame:
        """Func to get table with all news from current RSS feed structured

        Returns
        -------
        pd.DataFrame
            table with data regarding each piece of new including its title,
            link, publication time and text itself
        """
        news = self._get_news()
        news_data = {
            "title": [],
            "link": [],
            "publication_time": [],
            "text": [],
            "source": [],
        }
        for piece_of_new in news:
            news_data["title"].append(piece_of_new.find("title").text)
            news_data["link"].append(piece_of_new.find("guid").text)
            news_data["publication_time"].append(
                self._get_publication_time(piece_of_new)
            )
            news_data["text"].append(self._get_text(piece_of_new))
            news_data["source"].append(self.rss_link)
        return pd.DataFrame.from_dict(news_data)

    def _get_news(self) -> list:
        """Func to request current RSS feed and find all peieces of news

        Returns
        -------
        list
            list containing html pieces of news
        """
        html_page = requests.get(self.rss_link).text
        html_page = BeautifulSoup(html_page, "html.parser")
        news = html_page.findAll("item")
        logger.info(f"Length of news {len(news)}")
        return news

    def _get_publication_time(
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

    @abstractmethod
    def _get_text(
        self,
        piece_of_new: bs4.element.Tag,
    ) -> str:
        """Func to get description of piece of new and extract text from html

        Parameters
        ----------
        piece_of_new : bs4.element.Tag
            html piece of new to extract the text

        Returns
        -------
        str
            extracted and cleand text of piece of new
        """
        ...


class RTScraper(GeneralScraper):
    """
    RTS Scrapper
    """

    def __init__(self):
        super().__init__("https://russian.rt.com/rss")

    def _get_text(
        self,
        piece_of_new: bs4.element.Tag,
    ) -> str:
        """Func to get description of piece of new and extract text from html

        Parameters
        ----------
        piece_of_new : bs4.element.Tag
            html piece of new to extract the text

        Returns
        -------
        str
            extracted and cleand text of piece of new
        """

        description = piece_of_new.find("description")
        description = description.find(text=lambda tag: isinstance(tag, bs4.CData))
        description = BeautifulSoup(description, "html.parser", from_encoding="utf-8")
        description = description.text.strip()
        return description


class RIAScraper(GeneralScraper):
    """
    RIA Scraper
    """

    def __init__(self):
        super().__init__("https://ria.ru/export/rss2/index.xml")

    def _get_text(
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
        description = article_body.text.strip()
        return description


class VedomostiScraper(GeneralScraper):
    """
    Vedomosti Scraper
    """

    def __init__(self):
        super().__init__("https://www.vedomosti.ru/rss/news.xml")

    def _get_text(
        self,
        piece_of_new: bs4.element.Tag,
    ) -> str:
        """Func to get full text of piece of new and extract text from html

        Args:
            piece_of_new (bs4.element.Tag): _description_

        Returns:
            extracted and cleand text of piece of new
        """
        link = link = piece_of_new.find("guid").text
        full_page = requests.get(link).text
        full_page = BeautifulSoup(full_page, "html.parser")
        set_of_texts = full_page.findAll("div")[0].findAll(
            "p", {"class": "box-paragraph__text"}
        )
        description = "".join([text.text for text in set_of_texts])
        return description
