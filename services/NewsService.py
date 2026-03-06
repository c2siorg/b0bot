import json
from langchain_openai import ChatOpenAI
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from models.NewsModel import NewsArticle, CybernewsDB

class NewsService:
    def __init__(self, model_name="openai"):
        self.db = CybernewsDB()
        # Load config logic here...
        if model_name == "mistral":
            self.llm = ChatMistralAI(model="mistral-tiny", api_key="your_key")
        else:
            self.llm = ChatOpenAI(model="gpt-3.5-turbo", api_key="your_key")

    def getNews(self, keywords: str):
        try:
            parser = JsonOutputParser(pydantic_object=NewsArticle)
            
            prompt = ChatPromptTemplate.from_template(
                "Search for cybersecurity news about {keywords}.\n{format_instructions}"
            )
            
            # The modern LCEL Chain
            chain = prompt | self.llm | parser
            
            # Execute
            response = chain.invoke({
                "keywords": keywords, 
                "format_instructions": parser.get_format_instructions()
            })

            # FIX: 'response' is already a list of dicts from the JsonOutputParser.
            # Do NOT call .model_dump() here.
            return response 

        except Exception as e:
            print(f"Error in LLM Logic: {e}")
            return [] # Return empty list on failure for the bot to handle