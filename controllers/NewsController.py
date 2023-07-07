import services.NewsService as NewsService

"""
return news without considering keywords
"""


def getNews():
    return NewsService.getNews()


"""
return news based on certain keywords
"""


def getNewsWithKeywords(user_keywords):
    return NewsService.getNewsWithKeywords(user_keywords)


"""
deal requests with wrong route
"""


def notFound(error):
    return NewsService.notFound(error)
