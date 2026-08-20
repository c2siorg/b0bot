from flask import Flask, request
import tweepy

app = Flask(__name__)

# Twitter API credentials
consumer_key = "your_consumer_key"
consumer_secret = "your_consumer_secret"
access_token = "your_access_token"
access_token_secret = "your_access_token_secret"

# Authenticate with Twitter API
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

# Define endpoint for bot
@app.route('/bot', methods=['POST'])
def twitter_bot():
    # Get request data
    data = request.get_json()

    # Extract tweet text from data
    tweet = data['tweet']

    # Post tweet
    api.update_status(tweet)

    # Return success message
    return {"message": "Tweet posted successfully!"}

if __name__ == '__main__':
    app.run(debug=True)
