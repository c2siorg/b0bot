import os
from dotenv import dotenv_values
from dotenv import load_dotenv
from config.env_validator import validate_env

# 1️⃣ Load .env into os.environ
load_dotenv()

# 2️⃣ Fail fast BEFORE importing env-dependent modules
validate_env()

from flask import *
from langchain.prompts import PromptTemplate
from routes.NewsRoutes import routes

# `__name__` indicates the unique name of the current module
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
# Register routes
app.register_blueprint(routes)


if __name__ == "__main__":
    # app.run(debug=True, host="0.0.0.0")
    app.run(debug=True)


