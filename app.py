from dotenv import load_dotenv
from flask import *
from langchain_classic.prompts import PromptTemplate
from routes.NewsRoutes import routes

import logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

app = Flask(__name__)
logging.info("Flask app initialized")

# Register routes
app.register_blueprint(routes)
logging.info("Routes registered successfully")

if __name__ == "__main__":
    app.run(debug=True)