class NewsController:
    def __init__(self, model_name):
        self.model_name = model_name
        self._news_service = None

    def _get_service(self):
        if self._news_service is None:
            # Import lazily so route module import does not require heavy LLM deps.
            from services.NewsService import NewsService

            self._news_service = NewsService(self.model_name)
        return self._news_service

    """
    return news without considering keywords
    """

    def getNews(self):
        return self._get_service().getNews()

    """
    return news based on certain keywords
    """

    def getNewsWithKeywords(self, user_keywords):
        return self._get_service().getNews(user_keywords)

    """
    deal requests with wrong route
    """

    def notFound(self, error):
        return self._get_service().notFound(error)
