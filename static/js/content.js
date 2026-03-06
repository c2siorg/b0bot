// static/js/content.js
function renderContent(baseLLM) {
    const content = {
        gemma: {
            title: "Welcome to b0bot!",
            subtitle: "You are now using Gemma 2 9B as your base LLM",
            newsPath: "/gemma/news",
            newsKeywordsPath: "/gemma/news_keywords"
        },
        llama: {
            title: "Welcome to b0bot!",
            subtitle: "You are now using Llama 3 8B as your base LLM",
            newsPath: "/llama/news",
            newsKeywordsPath: "/llama/news_keywords"
        },
        qwen: {
            title: "Welcome to b0bot!",
            subtitle: "You are now using Qwen 2.5 72B as your base LLM",
            newsPath: "/qwen/news",
            newsKeywordsPath: "/qwen/news_keywords"
        }
    };

    const selectedContent = content[baseLLM];
    if (selectedContent) {
        document.getElementById('title').innerText = selectedContent.title;
        document.getElementById('subtitle').innerText = selectedContent.subtitle;
        document.getElementById('newsLink').href = selectedContent.newsPath;
        document.getElementById('newsKeywordsForm').action = selectedContent.newsKeywordsPath;
    } else {
        document.getElementById('title').innerText = "Welcome to b0bot!";
        document.getElementById('subtitle').innerText = "Please provide a valid LLM.";
    }
}
