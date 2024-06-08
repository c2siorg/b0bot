from services.NewsService import NewsService


class NewsController:
    def __init__(self,model_name) -> None:
        self.news_service = NewsService(model_name)

    """
    return news without considering keywords
    """

    def getNews(self):
        return self.news_service.getNews()

    """
    return news based on certain keywords
    """

    def getNewsWithKeywords(self, user_keywords):
        return self.news_service.getNews(user_keywords)

    """
    deal requests with wrong route
    """

    def notFound(self, error):
        return self.news_service.notFound(error)
