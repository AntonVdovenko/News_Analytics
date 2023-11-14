"""Scraper class to get news from RSS feed"""
import datetime

import bs4
import pandas as pd
import requests

from bs4 import BeautifulSoup
from loguru import logger


class RTScraper:
    """Scraper class to get news from Russia Today RSS feed"""

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

    def __get_news(self) -> list:
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
        return description.text.strip()
