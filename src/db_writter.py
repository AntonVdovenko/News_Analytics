"""
Script to work with DB
"""
from abc import ABC
from abc import abstractmethod

import pandas as pd

from solid_scraper import ABCScraper


class ABCDatabaseWritter(ABC):
    """Abscrtract class of DB writter"""

    @abstractmethod
    def connect(self):
        """
        This method connects to DB
        """
        ...

    @abstractmethod
    def write(self, df: pd.DataFrame) -> None:
        """
        This method writes dataframe to DB

        Parameters
        ----------
        df : pd.DataFrame
            dataframe to write
        """
        ...

    @staticmethod
    def get_news_data(scraper_list: list(ABCScraper)) -> pd.DataFrame:
        """
        This method combines dataframes
        from provided scrapers

        Parameters
        ----------
        scraper_list : list
            List with news scrappers

        Returns
        -------
        pd.DataFrame
            Combined dataframe
        """
        ...
