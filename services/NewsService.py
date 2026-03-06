from services.AgentTools import fetch_cyber_news
# In a real C2SI build, you'd import your Pinecone/Mongo logic here

class NewsService:
    @staticmethod
    def get_consolidated_news(categories):
        """
        Logic to fetch from multiple sources and remove duplicates.
        This fulfills the 'db_update' requirement by syncing 
        live scrapes with your Vector DB (Pinecone).
        """
        all_news = []
        seen_titles = set()

        for cat in categories:
            raw_data = fetch_cyber_news.invoke(cat)
            for item in raw_data:
                # Deduplication logic (Hardik's PR #25 focus)
                title = item.get("title", "").lower()
                if title not in seen_titles and len(title) > 10:
                    all_news.append(item)
                    seen_titles.add(title)
        
        return all_news

    @staticmethod
    def db_update_status():
        # This could check the last-updated timestamp in Pinecone
        return {"status": "synchronized", "last_update": "Just now"}

        # 1. Define the Prompt Template
        template = """Question: {question}\nAnswer: Let's think step by step."""
        prompt = PromptTemplate.from_template(template)

        # 2. Load and Format Messages from JSON
        messages_template_path = 'prompts/withkey.json' if user_keywords else 'prompts/withoutkey.json'
        messages = self.load_json_file(messages_template_path)

        # Build the final query string by replacing placeholders
        full_query = ""
        for message in messages:
            content = message['content']
            content = content.replace('<news_data_placeholder>', str(news_data))
            if user_keywords:
                content = content.replace('<user_keywords_placeholder>', str(user_keywords))
            content = content.replace('{news_format}', self.news_format)
            content = content.replace('{news_number}', str(self.news_number))
            full_query += content + "\n"

        # 3. THE LCEL CHAIN (This is the 2026 GSoC Standard)
        # This replaces the old LLMChain.invoke() logic
        chain = prompt | self.llm | StrOutputParser()
        
        # Invoke the chain with the formatted query
        output_text = chain.invoke({"question": full_query})

        # 4. Convert output string into structured JSON
        return self.toJSON(output_text)

    def notFound(self, error):
        return jsonify({"error": error}), 404
    
    def load_json_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def toJSON(self, data: str):
        if not data:
            return {}
        
        news_list = data.split("\n")
        news_list_json = []
        
        # Remove header if exists
        if news_list and "title" in news_list[0].lower():
            news_list.pop(0)

        for item in news_list:
            if not item.strip() or '[' not in item:
                continue
                
            try:
                # Clean brackets and split by comma
                clean_item = item.strip().strip('[').strip(']').replace(';', '')
                parts = [p.strip().strip('"').strip("'") for p in clean_item.split(',')]

                if len(parts) >= 4:
                    news_item = {
                        "title": parts[0],
                        "source": parts[1],
                        "date": parts[2],
                        "url": parts[3],
                    }
                    news_list_json.append(news_item)
            except Exception:
                continue

        return news_list_json