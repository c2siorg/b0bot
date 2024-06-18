"""
    Main Class for Extracting News
"""
from cybernews.extractor import Extractor

class CyberNews:
    def __init__(self) -> None:
        self._extractor = Extractor()
        self._news_types = [
            {
                "general": [
                    {
                        "https://ciosea.economictimes.indiatimes.com/news/next-gen-technologies": {
                            "headlines": "article.desc div h3.heading",
                            "author": None,
                            "fullNews": "article.desc div p.desktop-view",
                            "newsImg": ".desc figure a img",
                            "newsURL": ".desc figure a",
                            "date": None,
                        }
                    },
                    {
                        "https://telecom.economictimes.indiatimes.com/news/internet": {
                            "headlines": "article.desc div h3.heading",
                            "author": None,
                            "fullNews": "article.desc div p.desktop-view",
                            "newsImg": ".desc figure a img",
                            "newsURL": ".desc figure a",
                            "date": None,
                        }
                    },
                ],
            },
            {
                "dataBreach": [
                    {
                        "https://thehackernews.com/search/label/data%20breach": {
                            "headlines": "h2.home-title",
                            "author": ".item-label span",
                            "fullNews": ".home-desc",
                            "newsImg": ".img-ratio img",
                            "newsURL": "a.story-link",
                            "date": ".item-label",
                        }
                    },
                    {
                        "https://ciso.economictimes.indiatimes.com/news/data-breaches": {
                            "headlines": "article.desc div h3.heading",
                            "author": None,
                            "fullNews": "article.desc div p.desktop-view",
                            "newsImg": ".desc figure a img",
                            "newsURL": ".desc figure a",
                            "date": None,
                        }
                    },
                    {
                        "https://cyware.com/search?search=data%20breach": {
                            "headlines": "h1.cy-card__title",
                            "author": "a[href*='source_name']",
                            "fullNews": "div.cy-card__description",
                            "newsImg": None,
                            "newsURL": "a[href*='articles']",
                            "date": "span.cy-card__meta",
                        }
                    },
                ],
            },
            {
                "cyberAttack": [
                    {
                        "https://thehackernews.com/search/label/Cyber%20Attack": {
                            "headlines": "h2.home-title",
                            "author": ".item-label span",
                            "fullNews": ".home-desc",
                            "newsImg": ".img-ratio img",
                            "newsURL": "a.story-link",
                            "date": ".item-label",
                        }
                    },
                    {
                        "https://ciso.economictimes.indiatimes.com/news/cybercrime-fraud": {
                            "headlines": "article.desc div h3.heading",
                            "author": None,
                            "fullNews": "article.desc div p.desktop-view",
                            "newsImg": ".desc figure a img",
                            "newsURL": ".desc figure a",
                            "date": None,
                        }
                    },
                    {
                        "https://cyware.com/search?search=cyber%20attack": {
                            "headlines": "h1.cy-card__title",
                            "author": "a[href*='source_name']",
                            "fullNews": "div.cy-card__description",
                            "newsImg": None,
                            "newsURL": "a[href*='articles']",
                            "date": "span.cy-card__meta"
                        }
                    },
                ],
            },
            {
                "vulnerability": [
                    {
                        "https://thehackernews.com/search/label/Vulnerability": {
                            "headlines": "h2.home-title",
                            "author": ".item-label span",
                            "fullNews": ".home-desc",
                            "newsImg": ".img-ratio img",
                            "newsURL": "a.story-link",
                            "date": ".item-label",
                        }
                    },
                    {
                        "https://ciso.economictimes.indiatimes.com/news/vulnerabilities-exploits": {
                            "headlines": "article.desc div h3.heading",
                            "author": None,
                            "fullNews": "article.desc div p.desktop-view",
                            "newsImg": ".desc figure a img",
                            "newsURL": ".desc figure a",
                            "date": None,
                        }
                    },
                    {
                        "https://cyware.com/alerts/filter?alert_type=A&category_slug=malware-and-vulnerabilities-news":{
                            "headlines": "h1.cy-card__title",
                            "author": "a[href*='source_name']",
                            "fullNews": "div.cy-card__description",
                            "newsImg": None,
                            "newsURL": "a[href*='articles']",
                            "date": "span.cy-card__meta"
                        }
                    },
                ],
            },
            {
                "malware": [
                    {
                        "https://thehackernews.com/search/label/Malware": {
                            "headlines": "h2.home-title",
                            "author": ".item-label span",
                            "fullNews": ".home-desc",
                            "newsImg": ".img-ratio img",
                            "newsURL": "a.story-link",
                            "date": ".item-label",
                        }
                    },
                    {
                        "https://www.infosecurity-magazine.com/malware/": {
                            "headlines": "h3.content-headline a",
                            "author": None,
                            "fullNews": "p.content-teaser",
                            "newsImg": "img.content-thumb",
                            "newsURL": "h3.content-headline a",
                            "date": "time"
                        }
                    },
                ],
            },
            {
                "security": [
                    {
                        "https://ciosea.economictimes.indiatimes.com/news/security": {
                            "headlines": "article.desc div h3.heading",
                            "author": None,
                            "fullNews": "article.desc div p.desktop-view",
                            "newsImg": ".desc figure a img",
                            "newsURL": ".desc figure a",
                            "date": None,
                        }
                    },
                    {
                        "https://telecom.economictimes.indiatimes.com/tag/hacking": {
                            "headlines": "article.desc div h3.heading",
                            "author": None,
                            "fullNews": "article.desc div p.desktop-view",
                            "newsImg": ".desc figure a img",
                            "newsURL": ".desc figure a",
                            "date": None,
                        }
                    },
                ]
            },
            {
                "cloud": [
                    {
                        "https://ciosea.economictimes.indiatimes.com/news/cloud-computing": {
                            "headlines": "article.desc div h3.heading",
                            "author": None,
                            "fullNews": "article.desc div p.desktop-view",
                            "newsImg": ".desc figure a img",
                            "newsURL": ".desc figure a",
                            "date": None,
                        }
                    }
                ]
            },
            {
                "tech": [
                    {
                        "https://ciosea.economictimes.indiatimes.com/news/consumer-tech": {
                            "headlines": "article.desc div h3.heading",
                            "author": None,
                            "fullNews": "article.desc div p.desktop-view",
                            "newsImg": ".desc figure a img",
                            "newsURL": ".desc figure a",
                            "date": None,
                        }
                    },
                ]
            },
            {
                "iot": [
                    {
                        "https://ciosea.economictimes.indiatimes.com/news/internet-of-things": {
                            "headlines": "article.desc div h3.heading",
                            "author": None,
                            "fullNews": "article.desc div p.desktop-view",
                            "newsImg": ".desc figure a img",
                            "newsURL": ".desc figure a",
                            "date": None,
                        }
                    },
                ]
            },
            {
                "bigData": [
                    {
                        "https://ciosea.economictimes.indiatimes.com/news/big-data": {
                            "headlines": "article.desc div h3.heading",
                            "author": None,
                            "fullNews": "article.desc div p.desktop-view",
                            "newsImg": ".desc figure a img",
                            "newsURL": ".desc figure a",
                            "date": None,
                        }
                    },
                    {
                        "https://ciosea.economictimes.indiatimes.com/news/data-center": {
                            "headlines": "article.desc div h3.heading",
                            "author": None,
                            "fullNews": "article.desc div p.desktop-view",
                            "newsImg": ".desc figure a img",
                            "newsURL": ".desc figure a",
                            "date": None,
                        }
                    },
                ]
            }
        ]

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
