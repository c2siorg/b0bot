# B0Bot API - Bug Zero Bot API

B0Bot API is a Flask API that provides recent hacker, cybersecurity news. Users can request the API with or without keywords and get news easily.

# High-Level Architecture Diagram

B0Bot API lives inside a Flask API and is powered by LangChain and OpenAI API. 

In addition, to keep the knowledge base of news up to date, a scheduled script will be executed on a regular interval to retrieve the most recent cybersecurity news by scraping a list of target news websites and store them into the MongoDB Atlas Database. Everytime a user requests the B0Bot API, news in the database will be read into LangChain's memory and fed to the LLM of OpenAI. Then, answers will be generated based on both OpenAI model and our knowledge base.

<img width="908" alt="image" src="https://github.com/CoToYo/b0bot/assets/56789038/218fdf2b-be27-4222-9119-81c3dc5c4e02">

<img width="984" alt="image" src="https://github.com/CoToYo/b0bot/assets/56789038/4e5fe460-a210-46e9-b490-caa02e34c3af">

B0Bot API will continuely run as a serverless function (hosted on [Render](https://render.com/)) and it will record a successfull operation in a monitoring dashboard set up in [Better Uptime](https://betterstack.com/better-uptime).
