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

    def headers(self):
        return self._headers

    def remove_symbols(self, text: str) -> str:
        return re.sub(self.symbol_regex, "", text)

    def check_valid_date(self, date):
        date_format = "%b %d %Y"
        try:
            datetime.strptime(date, date_format)
            return True
        except ValueError:
            return False

    def is_valid_author_name(self, date: str) -> bool:
        return not self.check_valid_date(date)

    def format_author_name(self, name: str) -> str:
        return name.strip().replace("  ", " ")
