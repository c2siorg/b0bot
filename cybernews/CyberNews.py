import json
from cybernews.extractor import Extractor

class CyberNews:
    def __init__(self) -> None:
        self._extractor = Extractor()
        self._news_types = self.load_news_types_from_json('news_types.json')

    def load_news_types_from_json(self, json_file):
        with open(json_file, 'r', encoding='utf-8') as file:
            news_types = json.load(file)
        return news_types

    @property
    def get_news_types(self) -> list:
        return [news_type for news in self._news_types for news_type, _ in news.items()]

    def get_news(self, news) -> list:
        for news_type in self._news_types:
            if news in news_type:
                try:
                    return self._extractor.data_extractor(news_type[news])
                except Exception as e:
                    raise Exception(
                        f"An error occurred while processing the news of type: '{news}': {str(e)}"
                    )
        raise ValueError(f"News type '{news}' not found")
