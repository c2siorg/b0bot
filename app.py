import os
import logging
from dotenv import load_dotenv
from config.validator import validate_env, ConfigurationError

# Configure basic logging early to capture startup issues
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Validate configuration before importing heavy dependencies
try:
    validate_env()
except ConfigurationError as e:
    logging.critical(f"Startup configuration failed: {e}")
    raise SystemExit(1)

# Third-party imports
from flask import Flask, jsonify, Blueprint, render_template, g
from langchain_classic.prompts import PromptTemplate
# Local imports
from routes.NewsRoutes import routes

# `__name__` indicates the unique name of the current module
app = Flask(__name__)

# Register routes
app.register_blueprint(routes)

@app.errorhandler(Exception)
def handle_global_error(error):
    # Log the full exception internally
    logging.error(f"An unhandled exception occurred: {error}")
    # Return structured JSON error
    response = {
        "error": str(error),
        "code": 500
    }
    return jsonify(response), 500


if __name__ == "__main__":
    # app.run(debug=True, host="0.0.0.0")
    app.run(debug=True)


