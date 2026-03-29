from dotenv import load_dotenv
from flask import *
from langchain_core.prompts import PromptTemplate
from routes.NewsRoutes import routes
import datetime

# Load environment variables
load_dotenv()

# `__name__` indicates the unique name of the current module
app = Flask(__name__)

# Register routes
app.register_blueprint(routes)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "B0Bot API is running",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }), 200

if __name__ == "__main__":
    # app.run(debug=True, host="0.0.0.0")
    app.run(debug=True)


