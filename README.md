# B0Bot - Bug Zero Twitter Bot

B0Bot is a Twitter bot that provides periodic hacker, cybersecurity news to the followers of [Bug Zero](https://twitter.com/BugZero_io) Twitter account. In addition, if a user mentions the Bug Zero Twitter account and ask for certain keywords or news, B0Bot will reply with latest news (on Twitter) with the given keywords.

# High-Level Architecture Diagram

![image](./b0bot.png)

B0Bot lives inside a Flask API and periodically it will retweet certain Twitter accounts. In addition if a user mentions the bot, it will reply with given information. B0Bot will periodically run as a serverless function (hosted on [Vercel](https://vercel.com)) and it will record a successfull periodic operation in a monitoring dashboard set up in [Better Uptime](https://betterstack.com/better-uptime).

# Developer Road Map

- [ ] Setup initial Flask API
  - Set up a Twitter developer account and create a new Twitter app to access the Twitter API.
  - Create a new Flask API project, initialize it with a basic project structure, and install the necessary dependencies (e.g., Tweepy, Flask, etc.)
- [ ] Adding functionality to the Flask API
  - Create a new Python script to handle the Twitter API authentication and the bot's logic. This script should use the Tweepy library to interact with the Twitter API, and it should contain the following features:
    - Periodically retweet certain Twitter followers.
    - Respond to user mentions and provide the latest news with the given keywords.
- [ ] Deploy the Flask API to Vercel
  - Create a new Vercel project and deploy the Flask API to Vercel.
  - Set up a periodic job to run the Flask API periodically.
- [ ] Creating a monitoring dashboard
  - Create a new Better Uptime project and set up a monitoring dashboard to monitor the periodic job.
  - Add a new webhook to the Better Uptime project to send a notification to the Bug Zero Twitter account if the periodic job fails.

