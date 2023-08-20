from dotenv import dotenv_values
from flask import *
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

from routes.NewsRoutes import routes

# `__name__` indicates the unique name of the current module
app = Flask(__name__)

# Register routes
app.register_blueprint(routes)


if __name__ == "__main__":
    # app.run(debug=True, host="0.0.0.0")
    app.run()

#     news_list = data.split("\n")
#     news_list_json = []

#     for item in news_list:
#         # Avoid dirty data
#         if len(item) == 0:
#             continue
#         # Split the string at the first occurrence of '('
#         title, remaining = item.split("(", 1)

#         # Extract the source by splitting at ',' and removing leading/trailing whitespace
#         source = remaining.split(",")[0].strip()

#         # Extract the date by splitting at ',' and removing leading/trailing whitespace
#         date = remaining.split(",")[1].strip().rstrip(")")

#         # Create a dictionary for each news item and append it to the news_list
#         news_item = {"title": title.strip(), "source": source, "date": date}
#         news_list_json.append(news_item)

#     return jsonify(news_list_json)
