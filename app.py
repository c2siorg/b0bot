import os
from flask import *
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

# `__name__` indicates the unique name of the current module
app = Flask(__name__)

# Access environment variables
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Create a LLM object
llm = OpenAI(temperature=0.9)

@app.route('/news', methods=['GET'])
def getNews():
    # fixed format for answer
    answer_format = "news content (data source, date)"

    # add prompt
    prompt = PromptTemplate(
        input_variables=["format"],
        template =
        '''
        Please give me a list of the most recent cybersecurity news.
        Indicate data source and date.
        Return the answer with the format of '{format}'.
        '''
    )
    news = llm(prompt.format(format=answer_format))
    print(news)
    
    # convert news data into JSON format
    news_JSON = toJSON(news)

    return news_JSON

@app.route('/news_keywords', methods=['GET'])
def getNewsWithKeywords():
    # fixed format for answer
    answer_format = "news content (data source, date)"

    # get list of keywords as argument from User's request
    user_keywords = request.args.getlist('keywords')

    # add prompt 
    prompt = PromptTemplate(
        input_variables=["keywords", "format"],
        template=
        '''
        Please give me a list of the most recent cybersecurity news with keywords of {keywords}.
        Indicate data source and date.
        Return the answer with the format of '{format}'.
        '''
    )
    news = llm(prompt.format(keywords=user_keywords, format=answer_format))
    print(news)
    
    # convert news data into JSON format
    news_JSON = toJSON(news)

    return news_JSON

# deal requests with wrong route
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not Found'}), 404

# Convert news given by OpenAI API into JSON format.
def toJSON(data: str):
    news_list = data.split('\n')
    news_list_json = []

    for item in news_list:
        # Avoid dirty data
        if len(item) == 0:
            continue
        # Split the string at the first occurrence of '('
        title, remaining = item.split("(", 1)
        
        # Extract the source by splitting at ',' and removing leading/trailing whitespace
        source = remaining.split(",")[0].strip()
        
        # Extract the date by splitting at ',' and removing leading/trailing whitespace
        date = remaining.split(",")[1].strip().rstrip(")")
        
        # Create a dictionary for each news item and append it to the news_list
        news_item = {
            'title': title.strip(),
            'source': source,
            'date': date
        }
        news_list_json.append(news_item)
    
    return jsonify(news_list_json)