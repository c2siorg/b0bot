<h1 align="center">B0Bot - CyberSecurity News API</h1>
<p align="center">
  <br/><br/>
  <a href="https://github.com/c2siorg/b0bot"><img src="https://img.shields.io/github/forks/c2siorg/b0bot?style=plastic" alt ="Forks"/></a>
  <a href="https://github.com/c2siorg/b0bot"><img src="https://img.shields.io/github/stars/c2siorg/b0bot?style=plastic" alt ="Stars"/></a>
  <a target="_blank" href="https://github.com/c2siorg/b0bot"><img src="https://img.shields.io/github/commit-activity/m/c2siorg/b0bot?style=plastic" alt="Commit Activity"/></a>
  <a href="https://github.com/hywax/mafl/blob/main/LICENSE"><img src="https://img.shields.io/github/license/c2siorg/b0bot?style=plastic" alt="License MIT"/></a>
  <br/><br/>
</p>
<p>
B0Bot is a CyberSecurity News API tailored for automated bots on social media platforms. It is a cutting-edge Flask-based API that grants seamless access to the latest cybersecurity and hacker news. Users can effortlessly retrieve news articles either through specific keywords or without, streamlining the information acquisition process.
Once a user requests our API, it retrieves news data from our knowledge base and feeds it to the LLM. After the LLM processes the data, the API obtains the response and returns it in JSON format. The API is powered by LangChain and a Huggingface endpoint, ensuring that users receive accurate and up-to-date information.
</p>


## App Screenshots

| Home Page | LLM Page | News Page | News Keywords Page |
| :--------:| :-------:| :---------:| :-----------------:|
| ![Home Page](assets/home.png) | ![LLM Page](assets/llm.png) | ![News Page](assets/news.png) | ![News Keywords Page](assets/news_keywords.png) |

## Setup
1. Install all necessary packages

`pip install -r ./requirements.txt`


2. Set up your Pinecone database
```
https://www.pinecone.io/
```
Login to Pinecone and create a new index with the name `news-index`. Then, add the Pinecone API key in the `.env` file.




3. Set up your HuggingFace account
```
https://huggingface.co/
```


4. Add huggingface token in `.env` file

```
# HuggingFace
HUGGINGFACE_TOKEN='[Your_hugging_face_token_here]'

# Pinecone
PINECONE_API_KEY='[Your pinecone api here]'

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

```


5. Remember to replace the Pinecone connection string

```
# Example
client = Pinecone(api_key={PINECONE_API}) # Replace the string with yours
```


6. Enrich/Update news data into your database

Run `./db_update/Update.py` as a worker on a cloud service (e.g. heroku).
Or, run `./db_update/Update.py` manually in local.


7. Run the flask app

`flask --app app.py run`

> By default, the home page will open. The routes have to be defined manually.


8. We have added support for the following routes:
```
/llama          # Loads the Meta-Llama-3-8B-Instruct
/gemma          # Loads the Gemma-2b
/mistralai      # Loads the Mistral-7B-Instruct-v0.2
``` 

> [!NOTE]
> The Huggingface token you are using must have access to the LLama3 model listed above.
> You can do so by visiting this [link](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct).


8. Two available url paths
```
/<llm-name>/news
/<llm-name>/news_keywords?keywords=[Place news keywords here]
```

> [!IMPORTANT]
> The interface will only work if you specify the one of the avaialble paths above.


## High-Level Architecture Diagram

Our API lives inside a Flask API and is powered by LangChain and a Huggingface endpoint. 

In addition, to keep the knowledge base of news up to date, a scheduled script will be executed on a regular interval to retrieve the most recent cybersecurity news by scraping a list of target news websites and store them into the MongoDB Atlas Database. Everytime a user requests the API, news in the database will be read into LangChain's memory and fed to the LLM. Then, answers will be generated based on both the selected LLM and our knowledge base.

![Architecture](assets/arch.png)

![Knowledge Base](assets/db_arch.png)


The API will continuely run as a serverless function (hosted on [Render](https://render.com/)) and it will record a successfull operation in a monitoring dashboard set up in [Better Uptime](https://betterstack.com/better-uptime).

## Licensing

The MIT License 2023