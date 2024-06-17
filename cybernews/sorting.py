"""
    Class for Sorting News According to the date
"""
import uuid


class Sorting:
    """
    Months Dictionary
    """

    def __init__(self) -> None:
        self._months = {
            "january": "01",
            "february": "02",
            "march": "03",
            "april": "04",
            "may": "05",
            "june": "06",
            "july": "07",
            "august": "08",
            "september": "09",
            "october": "10",
            "november": "11",
            "december": "12",
        }

    """
        Giving UUID as _id for each news so that id is distinct
    """

    def _ordering_id(self, news):
        for individual_news in news:
            individual_news["id"] = uuid.uuid4().int

        return news

    """
        Ordering Date
    """

    def ordering_date(self, individual_news):
        if individual_news == "N/A":
            return 1

        individual_news = individual_news.lower().replace(",", "").split(" ")

        try:
            if individual_news[0].isnumeric():
                return int(
                    individual_news[2]
                    + self._months[individual_news[1]]
                    + individual_news[0]
                )

            return int(
                individual_news[2]
                + self._months[individual_news[0]]
                + individual_news[1]
            )

        except Exception as _:
            return 1

    """
        Ordering News By Latest Date
    """

    def ordering_news(self, news):
        data = sorted(
            news, key=lambda individual_news: individual_news["id"], reverse=True
        )

        data = self._ordering_id(data)
        return data
