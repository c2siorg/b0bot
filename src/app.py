from flask import Flask, jsonify
from src import create_app

app = create_app()

@app.route('/')
def home():
    # send json response
    return jsonify( {
        'org': 'BugZero',
        'project': 'B0Bot'
    })

@app.route('/search/<query>')
def search(query):
    # Code to search Twitter API for latest news on query
    news = "here is the news on " + query
    return jsonify( {
        'news': news
    })


if __name__ == '__main__':
    app.run(debug=True)
else:
    gunicorn_app = app