import os
import json
import re
from dotenv import dotenv_values
from flask import jsonify
from huggingface_hub import InferenceClient

from models.NewsModel import CybernewsDB
env_vars = dotenv_values(".env")
HUGGINGFACEHUB_API_TOKEN = env_vars.get("HUGGINGFACE_TOKEN")
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
class NewsService:
    def __init__(self , model_name) -> None:
        self.db = CybernewsDB()

        # Load the LLM configuration
        with open('config/llm_config.json') as f:
            llm_config = json.load(f)

        repo_id = llm_config.get(model_name) # loading the llm 
        
        if not repo_id:
            raise ValueError(f"Model '{model_name}' not found in llm_config.json")
        
        self.client = InferenceClient(
                model=repo_id,
                token=HUGGINGFACEHUB_API_TOKEN,
            )
        self.news_format = "[title, source, date(DD/MM/YYYY), news url];"
        self.news_number = 10
        self.max_news_candidates = 50
        self.max_news_payload_chars = 12000

    """
    Return news while checking if keyword has been specified or not
    """

    def getNews(self, user_keywords=None):
        # Fetch news data from db:
        # Only fetch data with valid `author` and `newsDate`
        # Drop field "id" from collection
        all_news_data = self.db.get_news_collections()
        # Keep a wider initial candidate set; compact+trim later based on payload size.
        prompt_candidates = all_news_data[:self.max_news_candidates]

        # Keep only fields required for prompting to avoid oversized payloads.
        prompt_news = self.compact_news_for_prompt(prompt_candidates)
        fallback_pool = self.compact_news_for_prompt(all_news_data)

        # Keep structured JSON and trim by full items to avoid malformed prompt data.
        trimmed_news = prompt_news[:]
        while trimmed_news and len(json.dumps(trimmed_news, ensure_ascii=False)) > self.max_news_payload_chars:
            trimmed_news.pop()
        news_data_str = json.dumps(trimmed_news, ensure_ascii=False)

        # Determine which messages template to load
        if user_keywords:
            messages_template_path = 'prompts/withkey.json'
        else:
            messages_template_path = 'prompts/withoutkey.json'
       
        # Load the messages template from the JSON file
        messages = self.load_json_file(messages_template_path)

        # Replace placeholders in the messages
        for message in messages:
            if message['role'] == 'user' and '<news_data_placeholder>' in message['content']:
                message['content'] = message['content'].replace('<news_data_placeholder>', news_data_str)
            if user_keywords and message['role'] == 'user' and '<user_keywords_placeholder>' in message['content']:
                message['content'] = message['content'].replace('<user_keywords_placeholder>', str(user_keywords))
            if message['role'] == 'user' and '{news_format}' in message['content']:
                message['content'] = message['content'].replace('{news_format}', self.news_format)
            if message['role'] == 'user' and '{news_number}' in message['content']:
                message['content'] = message['content'].replace('{news_number}', str(self.news_number))

        # Use chat_completion for instruction-tuned models
        response = self.client.chat_completion(
            messages=messages,
            max_tokens=1024,
            temperature=0.5,
        )

        output = response.choices[0].message.content

        # Convert news data into JSON format
        news_JSON = self.toJSON(output)
        fallback_items = self.fallback_news(fallback_pool)
        news_JSON = self.merge_news_results(news_JSON, fallback_items, self.news_number)

        return news_JSON[:self.news_number]

 
    """
    deal requests with wrong route
    """

    def notFound(self, error):
        return jsonify({"error": error}), 404
    
    """
    Load JSON file
    """
    
    def load_json_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    """
    Convert news given by Huggingface endpoint API into JSON format.
    """

    def toJSON(self, data: str):
        if not data or not data.strip():
            return []

        text = data.strip()
        news_list_json = []

        # Remove markdown code fences if the model wraps the answer.
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text).strip()

        # Try direct JSON first.
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        title = str(item.get("title", "")).strip()
                        if not title:
                            continue
                        news_list_json.append({
                            "title": title,
                            "source": str(item.get("source", "No source provided")).strip() or "No source provided",
                            "date": str(item.get("date", "No date provided")).strip() or "No date provided",
                            "url": str(item.get("url", "N/A")).strip() or "N/A",
                        })
                    elif isinstance(item, list) and len(item) >= 4:
                        news_list_json.append({
                            "title": str(item[0]).strip(),
                            "source": str(item[1]).strip(),
                            "date": str(item[2]).strip(),
                            "url": str(item[3]).strip() or "N/A",
                        })
            if news_list_json:
                return news_list_json
        except (json.JSONDecodeError, TypeError):
            pass

        # Fallback: parse line-based output in bracket format.
        # Some models return a single line with ';' delimiters, so normalize first.
        normalized_text = text.replace("];", "]\n")
        for raw_line in normalized_text.splitlines():
            line = raw_line.strip().rstrip(";")
            if not line:
                continue

            # Remove numbering like "1. " or "2) ".
            line = re.sub(r"^\d+[\.\)]\s*", "", line)

            # If line contains brackets, keep only the bracket content.
            match = re.search(r"\[(.*)\]", line)
            if match:
                line = match.group(1).strip()

            parts = [part.strip().strip('"').strip("'") for part in line.rsplit(",", 3)]
            if len(parts) < 4:
                continue

            title, source, date, url = parts[0], parts[1], parts[2], parts[3]
            if not title:
                continue

            news_list_json.append({
                "title": title,
                "source": source or "No source provided",
                "date": date or "No date provided",
                "url": url or "N/A",
            })

        return news_list_json

    def fallback_news(self, news_data):
        fallback = []
        for item in news_data:
            if not isinstance(item, dict):
                continue

            title = str(item.get("headlines") or item.get("title") or "").strip()
            if not title:
                continue

            fallback.append({
                "title": title,
                "source": str(item.get("author") or item.get("source") or "Unknown source").strip(),
                "date": str(item.get("newsDate") or item.get("date") or "Unknown date").strip(),
                "url": str(item.get("newsURL") or item.get("url") or "N/A").strip(),
            })

        return fallback

    def merge_news_results(self, primary_items, fallback_items, limit):
        merged = []
        seen_keys = set()

        def add_items(items):
            for item in items:
                if len(merged) >= limit:
                    return
                if not isinstance(item, dict):
                    continue

                title = str(item.get("title", "")).strip()
                source = str(item.get("source", "")).strip()
                date = str(item.get("date", "")).strip()
                url = str(item.get("url", "")).strip()

                if not title:
                    continue

                dedupe_key = (title.lower(), url.lower() if url else "", source.lower(), date)
                if dedupe_key in seen_keys:
                    continue

                seen_keys.add(dedupe_key)
                merged.append({
                    "title": title,
                    "source": source or "No source provided",
                    "date": date or "No date provided",
                    "url": url or "N/A",
                })

        add_items(primary_items or [])
        add_items(fallback_items or [])
        return merged

    def compact_news_for_prompt(self, news_data):
        compact = []
        for item in news_data:
            if not isinstance(item, dict):
                continue

            title = str(item.get("headlines") or item.get("title") or "").strip()
            if not title:
                continue

            compact.append({
                "title": title,
                "source": str(item.get("author") or item.get("source") or "Unknown source").strip(),
                "date": str(item.get("newsDate") or item.get("date") or "Unknown date").strip(),
                "url": str(item.get("newsURL") or item.get("url") or "N/A").strip(),
            })

        return compact
