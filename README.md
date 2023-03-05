# B0Bot - Bug Zero Twitter Bot

B0Bot is a Twitter bot that provides periodic hacker, cybersecurity news to the followers of [Bug Zero](https://twitter.com/BugZero_io) Twitter account. In addition, if a user mentions the Bug Zero Twitter account and ask for certain keywords or news, B0Bot will reply with latest news (on Twitter) with the given keywords.

# High-Level Architecture Diagram

![image](./b0bot.png)

B0Bot lives inside a Flask API and periodically it will retweet certain Twitter accounts. In addition if a user mentions the bot, it will reply with given information. B0Bot will periodically run as a serverless function (hosted on [Vercel](https://vercel.com)) and it will record a successfull periodic operation in a monitoring dashboard set up in [Better Uptime](https://betterstack.com/better-uptime).

# Developer Road Map

- [ ] Setup initial Flask API
- [ ] Set up a Twitter developer account and create a new app to access the Twitter API
- [ ] Configure the Tweepy library to interact with the Twitter API using Python
- [ ] Set up a MongoDB database using PyMongo to store the data collected by B0Bot
- [ ] Set up a Flask API that handles incoming requests from Twitter and users
- [ ] Implement B0Bot's periodic news feature by configuring the Tweepy library to periodically collect and store data from the Twitter API
- [ ] Implement B0Bot's keyword search feature by setting up a webhook to receive and process user requests from Twitter
- [ ] Implement B0Bot's retweet feature by configuring the Tweepy library to retweet tweets from certain accounts
- [ ] Implement B0Bot's reply feature by processing user mentions and sending appropriate responses
- [ ] Deploy B0Bot as a serverless function using Vercel
- [ ] Set up a monitoring dashboard using Better Uptime to record periodic operation logs and metrics