"""
Sync Extractor using ThreadPoolExecutor
Corrected version with safe selector alignment and URL normalization
"""

import concurrent.futures
import httpx
import time
from bs4 import BeautifulSoup

from .performance import Performance
from .sorting import Sorting


class Extractor(Performance):
    def __init__(self):
        super().__init__()
        self.session = httpx.Client(timeout=20.0)
        self.sorting = Sorting()
        self._headers = self.headers()

    # -----------------------------
    # Author Extraction
    # -----------------------------
    def _author_name_extractor(self, name: str):
        author_name = self.remove_symbols(self._pattern1.sub("", name))
        if not self.is_valid_author_name(author_name):
            return "N/A"
        return self.format_author_name(author_name)

    # -----------------------------
    # Check Advertisement
    # -----------------------------
    def _check_ad(self, news_date: str):
        return self._pattern4.search(news_date) is not None

    # -----------------------------
    # Extract Date
    # -----------------------------
    def _news_date_extractor(self, date: str, news_date: str) -> str:
        date = self._pattern3.sub("", self._pattern2.sub("", date))
        return self._pattern5.match(date).group() if news_date != "" else "N/A"

    # -----------------------------
    # Extract Data From Single News
    # -----------------------------
    def _extract_data_from_single_news(self, url: str, value: dict):
        news_data_from_single_news = []

        try:
            response = self.session.get(url, headers=self._headers)
            response.raise_for_status()
        except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError):
            return []

        soup = BeautifulSoup(response.text, "lxml")

        news_headlines = soup.select(value["headlines"])
        news_full_news = soup.select(value["fullNews"])
        news_url = soup.select(value["newsURL"])
        news_img_url = soup.select(value["newsImg"]) if value["newsImg"] else []
        raw_news_author = soup.select(value["author"]) if value["author"] else []
        raw_news_date = soup.select(value["date"]) if value["date"] else []

        total = min(len(news_headlines), len(news_full_news), len(news_url))

        for index in range(total):
            try:
                # ---- Safe Date Extraction
                if index < len(raw_news_date):
                    news_date = self._news_date_extractor(
                        raw_news_date[index].text.strip(), raw_news_date
                    )
                else:
                    news_date = "N/A"

                # ---- Safe Author Extraction
                if index < len(raw_news_author):
                    news_author = self._author_name_extractor(
                        raw_news_author[index].text.strip()
                    )
                else:
                    news_author = "N/A"

                if self._check_ad(news_date):
                    continue

                # ---- Safe URL Extraction
                href = news_url[index].get("href", "")

                # Handle relative URLs
                if href.startswith("/"):
                    base = url.split(".com")[0] + ".com"
                    href = base + href

                if not self.valid_url_check(href):
                    continue

                # ---- Spam Check
                content_combined = (
                    news_headlines[index].text.strip()
                    + " "
                    + news_full_news[index].text.strip()
                )

                if self.spam_content_check(content_combined):
                    continue

                # ---- Safe Image Extraction
                img_url = ""
                if index < len(news_img_url):
                    img_url = (
                        news_img_url[index].get("data-src")
                        or news_img_url[index].get("src")
                        or ""
                    )

                complete_news = {
                    "id": self.sorting.ordering_date(news_date),
                    "headlines": news_headlines[index].text.strip(),
                    "author": news_author,
                    "fullNews": news_full_news[index].text.strip(),
                    "newsURL": href,
                    "newsImgURL": img_url,
                    "newsDate": news_date,
                }

                news_data_from_single_news.append(complete_news)

            except Exception:
                continue

        unique_news = self._remove_duplicates(news_data_from_single_news)
        return self.sorting.ordering_news(unique_news)

    # -----------------------------
    # ThreadPool Executor
    # -----------------------------
    def data_extractor(self, news: list) -> list:
        news_data = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self._extract_data_from_single_news, url, value)
                for single_news in news
                for url, value in single_news.items()
            ]

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    news_data.extend(result)
                except Exception:
                    continue

        unique_news_data = self._remove_duplicates(news_data)
        return self.sorting.ordering_news(unique_news_data)

    # -----------------------------
    # Remove Duplicates
    # -----------------------------
    def _remove_duplicates(self, news_data: list) -> list:
        seen = set()
        unique_news_data = []

        for item in news_data:
            identifier = (item["headlines"], item["newsURL"], item["newsDate"])
            if identifier not in seen:
                seen.add(identifier)
                unique_news_data.append(item)

        return unique_news_data