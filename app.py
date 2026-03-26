from dotenv import load_dotenv
from flask import Flask
from routes.NewsRoutes import routes
from config.Database import init_redis

# Load environment variables
load_dotenv()

# `__name__` indicates the unique name of the current module
app = Flask(__name__)

# Initialize optional Redis cache client
init_redis()

# Register routes
app.register_blueprint(routes)


if __name__ == "__main__":
    # app.run(debug=True, host="0.0.0.0")
    app.run(debug=True)


