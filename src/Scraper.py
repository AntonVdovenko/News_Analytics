"""Scraper class to get news from RSS feed"""
import datetime

import bs4
import pandas as pd
import requests

from bs4 import BeautifulSoup
from loguru import logger


class Scraper:
    """Scraper class to get news from Russia Today RSS feed"""

    # TODO: finish list of links
    news_links = {
        "RT": "https://russian.rt.com/rss",
        "RIA": "https://ria.ru/export/rss2/index.xml",
        "Vedomosti": "https://www.vedomosti.ru/rss/news.xml",
    }

    # TODO: finish method to work on all links and return combined df
    def get_latest_news(self) -> pd.DataFrame:
        """Func to get table with all news from current RSS feed structured

        Returns
        -------
        pd.DataFrame
            table with data regarding each piece of new including its title,
            link, publication time and text itself
        """

        news_data = {
            "title": [],
            "link": [],
            "publication_time": [],
            "text": [],
            "source": [],
        }
        dfs = []
        for source in self.news_links.keys():
            link = self.news_links[source]
            news = self.__get_news(source, link)
            for piece_of_new in news:
                news_data["title"].append(self.__get_title(source, piece_of_new))
                news_data["link"].append(self.__get_link(source, piece_of_new))
                news_data["publication_time"].append(
                    self.__get_publication_time(source, piece_of_new)
                )
                news_data["text"].append(self.__get_text(source, piece_of_new))
                news_data["source"] = source
            df = pd.DataFrame.from_dict(news_data)
            dfs.append(df)
        return pd.concat(dfs, ignore_index=True)

    def __get_title(
        self,
        source: str,
        piece_of_new: bs4.element.Tag,
    ) -> str:
        """Func to get title of piece of new

        Args:
            source (str): initial source of piece of new
            piece_of_new (bs4.element.Tag): html piece of new

        Returns:
            str: title of piece of new
        """
        if source in ["RT", "RIA", "Vedomosti"]:
            title = piece_of_new.find("title").text.strip()
        else:
            title = ""
        return title

    def __get_link(
        self,
        source: str,
        piece_of_new: bs4.element.Tag,
    ) -> str:
        """Func to get link of piece of new

        Args:
            source (str): initial source of piece of new
            piece_of_new (bs4.element.Tag): html piece of new

        Returns:
            str: link to full page of piece of new
        """
        if source in ["RT", "RIA", "Vedomosti"]:
            link = piece_of_new.find("guid").text
        else:
            link = ""
        return link

    def __get_news(self, source: str, link: str) -> list:
        """Func to request current RSS feed and find all peieces of news

        Args:
            source (str): initial source of piece of new
            link (str): link to news feed

        Returns:
            list: ist containing html pieces of news
        """
        if source in ["RT", "RIA", "Vedomosti"]:
            html_page = requests.get(link)
            encoding = BeautifulSoup(html_page.content, "html.parser").original_encoding
            html_page.encoding = encoding
            html_page = BeautifulSoup(html_page.content, "html.parser")
            news = html_page.findAll("item")
        else:
            news = []
        logger.info(f"Length of news {source} {len(news)}")
        return news

    def __get_publication_time(
        self,
        source: str,
        piece_of_new: bs4.element.Tag,
    ) -> datetime.datetime:
        """Func to extract date and time of publication, transform it to datetime

        Parameters
        ----------
        source (str): initial source of piece of new
        piece_of_new : bs4.element.Tag
            html piece of new to extract the date and time

        Returns
        -------
        datetime.datetime
            time of publication with timezone appointed
        """
        if source in ["RT", "RIA", "Vedomosti"]:
            time_format = "%d %b %Y %H:%M:%S %z"
            time = piece_of_new.find("pubdate").text
            time = time.split(",")[1].strip()
            time = datetime.datetime.strptime(time, time_format)
        else:
            time = datetime.date.today
        return time

    # TODO: change method to work with all links
    def __get_text(
        self,
        source: str,
        piece_of_new: bs4.element.Tag,
    ) -> str:
        """Func to get description of piece of new and extract text from html

        Parameters
        ----------
        source (str): initial source of piece of new
        piece_of_new : bs4.element.Tag
            html piece of new to extract the text

        Returns
        -------
        str
            extracted and cleand text of piece of new
        """
        if source == "RT":
            description = piece_of_new.find("description")
            description = description.find(text=lambda tag: isinstance(tag, bs4.CData))
            description = BeautifulSoup(
                description, "html.parser", from_encoding="utf-8"
            ).text.strip()
        elif source == "RIA":
            link = piece_of_new.find("guid").text
            full_page = requests.get(link).text
            full_page = BeautifulSoup(full_page, "html.parser")
            description = (
                full_page.find("div", {"class": "page"})
                .find("div", {"itemprop": "articleBody"})
                .text.strip()
            )
        elif source == "Vedomosti":
            link = link = piece_of_new.find("guid").text
            full_page = requests.get(link).text
            full_page = BeautifulSoup(full_page, "html.parser")
            set_of_texts = full_page.findAll("div")[0].findAll(
                "p", {"class": "box-paragraph__text"}
            )
            description = "".join([text.text for text in set_of_texts])
        else:
            description = ""
        return description
