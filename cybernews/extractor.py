"""
    Class for Exception Handling and Extracting data out of complex strings
"""
import concurrent.futures

import httpx
from bs4 import BeautifulSoup

from .performance import Performance
from .sorting import Sorting


class Extractor(Performance):
    def __init__(self):
        """
        Initializing the Extractor class
        """
        # Call the constructor of the parent class (Performance)
        super().__init__()
        # Initiate a session using requests
        self.session = httpx.Client()
        # Create an instance of the Sorting class
        self.sorting = Sorting()
        # Get the headers for the HTTP requests
        self.headers = self.headers()

    # Extracting Author Name
    def _author_name_extractor(self, name: str):
        """
        Extract the author name from a given string.

        Args:
        name (str): the name to extract from.

        Returns:
        str: the extracted author name.
        """
        # Use the '_pattern1' regular expression to remove unwanted characters
        author_name = self.remove_symbols(self._pattern1.sub("", name))

        if not self.is_valid_author_name(author_name):
            return "N/A"
        return self.format_author_name(author_name)

    # Checking is news or some random advertisement
    def _check_ad(self, news_date: str):
        """
        Check if a given date string represents an advertisement.

        Args:
        news_date (str): the date string to check.

        Returns:
        bool: True if the date string represents an advertisement, False otherwise.
        """
        # Use the '_pattern4' regular expression to search for the advertisement indicator
        return self._pattern4.search(news_date) is not None

    # Extracting NewsDate
    def _news_date_extractor(self, date: str, news_date: str) -> str:
        """
        Extract the news date from a given string.

        Args:
        date (str): the string to extract the news date from.
        news_date (str): an additional string to use in the extraction process.

        Returns:
        str: the extracted news date, or 'N/A' if the date could not be extracted.
        """
        # Use two regular expressions to remove unwanted characters
        date = self._pattern3.sub("", self._pattern2.sub("", date))
        # Use the '_pattern5' regular expression to match the news date
        return self._pattern5.match(date).group() if news_date != "" else "N/A"

    # Extracting Data From Single News
    def _extract_data_from_single_news(self, url: str, value: dict):
        news_data_from_single_news = []
        response = self.session.get(url, timeout=20, headers=self.headers)
        soup = BeautifulSoup(response.text, "lxml")
        news_headlines = soup.select(value["headlines"])
        raw_news_author = (
            soup.select(value["author"]) if value["author"] is not None else ""
        )
        news_full_news = soup.select(value["fullNews"])
        news_url = soup.select(value["newsURL"])
        news_img_url = soup.select(value["newsImg"])
        raw_news_date = soup.select(value["date"]) if value["date"] is not None else ""

        for index in range(len(news_headlines)):
            if raw_news_date:
                news_date = self._news_date_extractor(
                    raw_news_date[index].text.strip(), raw_news_date
                )
            else:
                news_date = "N/A"

            if raw_news_author:
                news_author = self._author_name_extractor(
                    raw_news_author[index].text.strip()
                )
            else:
                news_author = "N/A"

            if self._check_ad(news_date):
                continue

            complete_news = {
                "id": self.sorting.ordering_date(news_date),
                "headlines": news_headlines[index].text.strip(),
                "author": news_author,
                "fullNews": news_full_news[index].text.strip(),
                "newsURL": news_url[index]["href"],
                "newsImgURL": news_img_url[index]["data-src"],
                "newsDate": news_date,
            }
            news_data_from_single_news.append(complete_news)

        return news_data_from_single_news

    # Extracting Data Using Tags
    def data_extractor(self, news: list) -> list:
        """
        Extract news data from a given list of news headers.

        Args:
        news_header (list): a list of dictionaries containing news headers.

        Returns:
        list: a list of dictionaries containing the extracted news data.
        """

        # Initialize an empty list to store the extracted news data
        news_data = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_news = {
                executor.submit(self._extract_data_from_single_news, url, value): (
                    url,
                    value,
                )
                for single_news in news
                for url, value in single_news.items()
            }
            for future in concurrent.futures.as_completed(future_to_news):
                url = future_to_news[future]
                try:
                    news_data_from_single_news = future.result()
                    news_data.extend(news_data_from_single_news)
                except Exception as exc:
                    print(f"{url} generated an exception: {exc}")

        return self.sorting.ordering_news(news_data)
