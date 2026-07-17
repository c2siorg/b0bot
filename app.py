from dotenv import load_dotenv
from flask import Flask, jsonify
from routes.NewsRoutes import routes

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Register blueprints
app.register_blueprint(routes)


# Health check route (good practice)
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"message": "API is running"}), 200


# Global error handler (important improvement)
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
