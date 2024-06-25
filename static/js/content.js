// static/js/content.js
function renderContent(baseLLM) {
    const content = {
        gemma: {
            title: "Welcome to b0bot!",
            subtitle: "You are now using Gemma-2b as your base LLM",
            newsPath: "/gemma/news",
            newsKeywordsPath: "/gemma/news_keywords?keywords="
        },
        llama: {
            title: "Welcome to b0bot!",
            subtitle: "You are now using Llama-3 as your base LLM",
            newsPath: "/llama/news",
            newsKeywordsPath: "/llama/news_keywords?keywords="
        },
        mistralai: {
            title: "Welcome to b0bot!",
            subtitle: "You are now using MistralAI as your base LLM",
            newsPath: "/mistralai/news",
            newsKeywordsPath: "/mistralai/news_keywords?keywords="
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
