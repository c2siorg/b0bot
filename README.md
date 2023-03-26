# B0Bot - Bug Zero Twitter Bot

B0Bot is a Twitter bot that provides periodic hacker, cybersecurity news to the followers of [Bug Zero](https://twitter.com/BugZero_io) Twitter account. In addition, if a user mentions the Bug Zero Twitter account and ask for certain keywords or news, B0Bot will reply with latest news (on Twitter) with the given keywords.

# High-Level Architecture Diagram

![image](./b0bot.png)

B0Bot lives inside a Flask API and periodically it will retweet certain Twitter accounts. In addition if a user mentions the bot, it will reply with given information. B0Bot will periodically run as a serverless function (hosted on [Vercel](https://vercel.com)) and it will record a successfull periodic operation in a monitoring dashboard set up in [Better Uptime](https://betterstack.com/better-uptime).

# Developer Road Map

- [ ] Setup initial Flask API
- [ ] Create a Twitter account and integrate the Twitter API with Tweepy for account interaction
- [ ] Implement functions to periodically tweet news using the Twitter API
- [ ] Implement a function to listen for mentions of the bot's Twitter account
- [ ] Implement a function to search for tweets with specific keywords
- [ ] Integrate MongoDB with PyMongo for data storage
- [ ] Implement CRUD operations for storing and retrieving data in the database
- [ ] Set up serverless architecture using Vercel to run B0Bot 
- [ ] Add monitoring and logging using Better Uptime
- [ ] Add additional features such as rate limiting, multimedia support