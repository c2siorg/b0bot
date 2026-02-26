from flask import *
from controllers.NewsController import NewsController
import hashlib
from config.Redis import redis_client, CACHE_TTL




routes = Blueprint("routes", __name__)
news_controller = NewsController("mistralai") # default model name



def get_cache_key(route_name, llm_name, keywords=None):
    """
    Generates a cache key for the given route name and arguments.

    """
    base_key = f"news:{route_name}:{llm_name}"
    if keywords:
        keyword_hash = hashlib.md5(','.join(sorted(keywords)).encode()).hexdigest()
        return f"{base_key}:{keyword_hash}"
    
    return base_key
def check_and_cache(key, content):
    """
    Checks if the given key exists in the cache. If it does not, the content is stored in the cache.

    """
    cached = redis_client.get(key)
    if cached:
        return cached
    redis_client.set(cache_key, content, ex=CACHE_TTL)

    return content

"""
home page route
"""
@routes.route("/", methods=["GET"])
def home_route():
    cache_key = "home:static"
    cached = redis_client.get(cache_key)
    if cached:
        return cached
    content = render_template("home.html")
    redis_client.set(cache_key, content, ex=CACHE_TTL)

    return content


"""
set route for different LLM models
"""
@routes.route("/<llm_name>", methods=["GET"])
def set_llm_route(llm_name):
    if llm_name == "favicon.ico":
        return "", 204  # No Content response for favicon requests
    g.news_controller = NewsController(llm_name)
    return render_template("llm.html", llm_name=llm_name)


"""
return news without considering keywords
"""
@routes.route("/<llm_name>/news", methods=["GET"])
def getNews_route(llm_name):
    cache_key = get_cache_key("news", llm_name)
    cached = redis_client.get(cache_key)
    
    if cached:
        return cached
    
    g.news_controller = NewsController(llm_name)
    news = g.news_controller.getNews()
    content = render_template("news.html", data=news)
    
    redis_client.set(cache_key, content, ex=CACHE_TTL)
    return content


"""
return news based on certain keywords
"""
@routes.route("/<llm_name>/news_keywords", methods=["GET"])
def getNewsWithKeywords_route(llm_name):
    # get list of keywords as argument from User's request
    user_keywords = request.args.getlist("keywords")
    cache_key = get_cache_key("news_keywords", llm_name, user_keywords)
    cached = redis_client.get(cache_key)
    if cached:
        return cached
    
    g.news_controller = NewsController(llm_name)
    user_keywords = request.args.getlist("keywords")
    data = g.news_controller.getNewsWithKeywords(user_keywords[0])
    content = render_template("news_key.html", data=data,keyword=user_keywords[0])
    redis_client.set(cache_key, content, ex=CACHE_TTL)
    
    return content



"""
deal requests with wrong route
"""
@routes.errorhandler(404)
def notFound_route(error):
    g.news_controller.notFound(error)
