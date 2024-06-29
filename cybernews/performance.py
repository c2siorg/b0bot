"""
    Performance Class for better and fast extracting of data
"""
import re
from datetime import datetime


class Performance:
    _pattern1 = re.compile(r"\ue804")
    _pattern2 = re.compile(r"\ue802")
    _pattern3 = re.compile(r"\ue804.+")
    _pattern4 = re.compile(
        r"([\w+]+\:\/\/)?([\w\d-]+\.)*[\w-]+[\.\:]\w+([\/\?\=\&\#.]?[\w-]+)*\/?"
    )
    _pattern5 = re.compile(r"^[^\n]+")
    symbol_regex = re.compile(r"[^\w\s]")

    def __init__(self):
        """
        Headers For Performance
        """
        self._headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 "
            "Safari/537.36",
            "Content-Type": "application/json; charset=utf-8",
            "server": "nginx/1.0.4",
            "x-runtime": "148ms",
            "etag": '"e1ca502697e5c9317743dc078f67693f"',
            "Access-Control-Allow-Credentials": "true",
            "Content-Encoding": "gzip",
        }
        self._spam_keywords = ["buy now", "click here", "subscribe", "limited offer"]

    def headers(self):
        """
        Return the headers for HTTP requests.
        """
        return self._headers

    def remove_symbols(self, text: str) -> str:
        """
        Remove non-alphanumeric symbols from a given text.

        Args:
            text (Optional[str]): The text to clean.

        Returns:
            str: The cleaned text.
        """ 
        if not text:
            return ""
        return re.sub(self.symbol_regex, "", text)

    def check_valid_date(self, date):
        """
        Check if a given date string matches the expected format.

        Args:
            date (str): The date string to check.
            date_format (str): The expected date format.

        Returns:
            bool: True if the date is valid, False otherwise.
        """
        date_format = "%b %d %Y"
        try:
            datetime.strptime(date, date_format)
            return True
        except ValueError:
            return False

    def is_valid_author_name(self, name: str) -> bool:
        """
        Check if the given name is not a valid date, hence a valid author name.

        Args:
            name (str): The name to check.

        Returns:
            bool: True if the name is valid, False otherwise.
        """
        return not self.check_valid_date(name)

    def format_author_name(self, name: str) -> str:
        """
        Format the author name by stripping extra spaces.

        Args:
            name (str): The name to format.

        Returns:
            str: The formatted author name.
        """
        return " ".join(name.strip().split())
    
    def valid_url_check(self, url: str) -> bool:
        """
        Check if the URL is valid.

        Args:
            url (str): The URL to check.

        Returns:
            bool: True if the URL is valid, False otherwise.
        """
        return url.startswith("http://") or url.startswith("https://")

    def spam_content_check(self, content: str) -> bool:
        """
        Check for spammy content in the text.

        Args:
            content (str): The content to check.

        Returns:
            bool: True if the content is spammy, False otherwise.
        """
        return any(keyword in content.lower() for keyword in self._spam_keywords)
    

