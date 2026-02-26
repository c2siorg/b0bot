// static/js/content.js
function renderContent(baseLLM) {
    const content = {
        gemma: {
            title: "Welcome to b0bot!",
            subtitle: "You are now using Gemma-3 as your base LLM",
            newsPath: "/gemma/news",
            newsKeywordsPath: "/gemma/news_keywords?keywords="
        },
        llama: {
            title: "Welcome to b0bot!",
            subtitle: "You are now using Llama-3 as your base LLM",
            newsPath: "/llama/news",
            newsKeywordsPath: "/llama/news_keywords?keywords="
        },
        Qwen: {
            title: "Welcome to b0bot!",
            subtitle: "You are now using Qwen as your base LLM",
            newsPath: "/Qwen/news",
            newsKeywordsPath: "/Qwen/news_keywords?keywords="
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
