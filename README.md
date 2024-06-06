# B0Bot - CyberSecurity News API

## Setup
1. Install all necessary packages

`pip install -r ./requirements.txt`

2. Set up your MongoDB Atlas database

https://www.mongodb.com/atlas/database

3. Set up your HuggingFace account

https://huggingface.co/


4. Add huggingface token in `.env` file

```

# HuggingFace
HUGGINGFACE_TOKEN='[Your_hugging_face_token_here]'

# MongoDB Atlas
DB_PASSWORD='[Your database password here]'
```

5. Remember to replace the MongoDB connection string

```
# Example
client = MongoClient(f"mongodb+srv://b0bot:{DB_PASSWORD}@cluster0.zqgexb4.mongodb.net/") # Replace the string with yours
```

6. Enrich/Update news data into your database

Run `./db_update/Update.py` as a worker on a cloud service (e.g. heroku).
Or, run `./db_update/Update.py` manually in local.

7. Run the flask app

`flask --app app.py run`

> By default, the home page will open. The routes have to be defined manually.

8. Two available url paths
```
/news
/news_keywords?keywords=[Place news keywords here]
```
> [!IMPORTANT]
> The interface will only work if you specify the one of the avaialble paths above.

In this project, our objective is to develop a CyberSecurity News API tailored for automated bots on social media platforms.

It is a cutting-edge Flask-based API that grants seamless access to the latest cybersecurity and hacker news. Users can effortlessly retrieve news articles either through specific keywords or without, streamlining the information acquisition process.

Once a user requests our API, it retrieves news data from our knowledge base and feeds it to ChatGPT. After ChatGPT processes the data, the API obtains the response and returns it in JSON format.

# High-Level Architecture Diagram

Our API lives inside a Flask API and is powered by LangChain and OpenAI API. 

In addition, to keep the knowledge base of news up to date, a scheduled script will be executed on a regular interval to retrieve the most recent cybersecurity news by scraping a list of target news websites and store them into the MongoDB Atlas Database. Everytime a user requests the API, news in the database will be read into LangChain's memory and fed to the LLM of OpenAI. Then, answers will be generated based on both OpenAI model and our knowledge base.

<img width="908" alt="image" src="https://github.com/CoToYo/b0bot/assets/56789038/218fdf2b-be27-4222-9119-81c3dc5c4e02">

<img width="984" alt="image" src="https://github.com/CoToYo/b0bot/assets/56789038/4e5fe460-a210-46e9-b490-caa02e34c3af">

The API will continuely run as a serverless function (hosted on [Render](https://render.com/)) and it will record a successfull operation in a monitoring dashboard set up in [Better Uptime](https://betterstack.com/better-uptime).
