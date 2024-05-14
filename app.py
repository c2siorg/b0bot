from dotenv import dotenv_values
from flask import *
from langchain.prompts import PromptTemplate

from routes.NewsRoutes import routes

# `__name__` indicates the unique name of the current module
app = Flask(__name__)

# Register routes
app.register_blueprint(routes)


if __name__ == "__main__":
    # app.run(debug=True, host="0.0.0.0")
    app.run(debug=True)


