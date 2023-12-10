"""
This script implemets scraping interfaces for news websites 
"""
import asyncio
import datetime
import unicodedata

from abc import ABC
from abc import abstractmethod

import bs4
import pandas as pd
import requests

from bs4 import BeautifulSoup
from loguru import logger
from telethon.sync import TelegramClient


class ABCScraper(ABC):
    def __init__(
        self,
        source: str,
    ):
        """Init func keeping link to RSS feed or another source reference

        Args:
            source (str): link to RSS feed or another source reference
        """
        self.source = source
        return

    @abstractmethod
    def get_latest_news(self) -> pd.DataFrame:
        """Func to get table with all news from current
        RSS feed structured or telegram channel

        Returns
        -------
        pd.DataFrame
            table with data regarding each piece of new including its title,
            link, publication time and text itself
        """
        ...

    @abstractmethod
    def _get_news(self) -> list:
        """Func to request current RSS feed or last XX news
        from telegram channel and find all peieces of news

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
    def __init__(
        self,
        source: str,
    ):
        """Init func keeping link to RSS feed or another source reference

        Args:
            source (str): link to RSS feed or another source reference
        """
        self.source = source
        return

    def get_latest_news(self) -> pd.DataFrame:
        """Func to get table with all news from current
        RSS feed structured or telegram channel

        Returns
        -------
        pd.DataFrame
            table with data regarding each piece of new including its title,
            link, publication time and text itself
        """
        news = self._get_news(self.source)
        news_data = {
            "title": [],
            "link": [],
            "publication_time": [],
            "text": [],
            "source": [],
        }
        for piece_of_new in news:
            news_data["title"].append(self._get_title(piece_of_new))
            news_data["link"].append(self._get_link(piece_of_new))
            news_data["publication_time"].append(
                self._get_publication_time(piece_of_new)
            )
            news_data["text"].append(self._get_text(piece_of_new))
            news_data["source"].append(self.source)
        return pd.DataFrame.from_dict(news_data)

    def _get_news(self, source) -> list:
        """Func to request current RSS feed structured
        or telegram channel and find all peieces of news

        Returns
        -------
        list
            list containing html or text pieces of news
        """
        html_page = requests.get(source)
        html_page.encoding = html_page.apparent_encoding
        html_page = BeautifulSoup(html_page.text, "html.parser")
        news = html_page.findAll("item")
        logger.info(f"Length of news {len(news)}")
        return news

    def _get_title(
        self,
        piece_of_new: bs4.element.Tag,
    ) -> str:
        """Func to get title of piece of new

        Args:
            piece_of_new (bs4.element.Tag): html piece of
            new to extract the date and time

        Returns:
            str: title of piece of new
        """
        return piece_of_new.find("title").text

    def _get_link(
        self,
        piece_of_new: bs4.element.Tag,
    ) -> str:
        """Func to get link of piece of new

        Args:
            piece_of_new (bs4.element.Tag): html
            piece of new to extract the date and time

        Returns:
            str: link to piece of new
        """
        return piece_of_new.find("guid").text

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

        raise NotImplementedError


class RTScraper(GeneralScraper):
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
    def __init__(self):
        """_summary_"""
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
    def __init__(self):
        """_summary_"""
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


class MeduzaScraper(GeneralScraper):
    def __init__(self):
        """_summary_"""
        super().__init__("https://meduza.io/rss2/all")

    def _get_title(self, piece_of_new: bs4.element.Tag) -> str:
        """_summary_

        Args:
            piece_of_new (bs4.element.Tag): _description_

        Returns:
            str: _description_
        """
        title = piece_of_new.findAll("description")[0].find(
            text=lambda tag: isinstance(tag, bs4.CData)
        )
        title = (
            BeautifulSoup(title, "html.parser", from_encoding="utf-8").find("p").text
        )
        return unicodedata.normalize("NFKD", title)

    def _get_text(self, piece_of_new: bs4.element.Tag) -> str:
        """_summary_

        Args:
            piece_of_new (bs4.element.Tag): _description_

        Returns:
            str: _description_
        """
        full_text = piece_of_new.findAll("content:encoded")[0].find(
            text=lambda tag: isinstance(tag, bs4.CData)
        )
        full_text = BeautifulSoup(
            full_text, "html.parser", from_encoding="utf-8"
        ).findAll("p")
        full_text = " ".join([text.text for text in full_text])
        return unicodedata.normalize("NFKD", full_text)


# NOT WORKING, TO BE DONE
class TGScraper(GeneralScraper):
    def __init__(self):
        """_summary_"""
        super().__init__("Осторожно, новости")
        self.tg_client = self.authenticate()
        print("Successfully logged out")

    def authenticate(self):
        """_summary_"""
        ioloop = asyncio.get_event_loop()
        tasks = [
            ioloop.create_task(
                self._authenticate(
                    28452758,
                    "e33c7375760762a5dbc1ac8ed0a3c472",
                    "79131292961",
                )
            )
        ]
        wait_tasks = asyncio.wait(tasks)
        ioloop.run_until_complete(wait_tasks)

    async def _authenticate(
        self,
        api_id: int,
        api_hash: str,
        phone: str,
    ) -> TelegramClient:
        """_summary_

        Args:
            api_id (int): _description_
            api_hash (str): _description_
            phone (str): _description_

        Returns:
            TelegramClient: _description_
        """
        tg_client = TelegramClient("TGScraper", api_id, api_hash)
        await tg_client.start()
        await tg_client.connect()
        if not await tg_client.is_user_authorized():
            await tg_client.send_code_request(phone)
            await tg_client.sign_in(phone, input("Enter the code: "))
        self.tg_client = tg_client

    async def _logout(self, client: TelegramClient):
        """_summary_

        Args:
            client (TelegramClient): _description_
        """
        client = await client
        client.log_out()

    async def _get_news(
        self,
        source,
    ) -> list:
        """something

        Args:
            source (_type_): something

        Returns:
            list: something
        """
        dialogs = await self.client.get_dialogs()
        news = []
        for dialog in dialogs:
            if dialog.title == source:
                messages = self.tg_client.iter_messages(dialog)
                i = 0
                async for message in messages:
                    i += 1
                    news.append(message)
                    if i == 50:
                        break
        print(news[0])
        return news
