from services.NewsService import NewsService

class NewsController:
    def __init__(self, model_name=None):
        self.news_service = NewsService(model_name)

    """
    return news without considering keywords
    """

    def getNews(self, llm=True):
        if self.news_service.model_name is None:
            return self.news_service.getNews(llm=False)
        return self.news_service.getNews(llm=llm)

    """
    return news based on certain keywords
    """

    def getNewsWithKeywords(self, user_keywords, llm=True):
        if self.news_service.model_name is None:
            return self.news_service.getNews(user_keywords, llm=False)
        return self.news_service.getNews(user_keywords, llm=llm)

    """
    deal requests with wrong route
    """

    def notFound(self, error):
        return self.news_service.notFound(error)
