from controllers.NewsController import NewsController
import requests
def fetch_data(parameter,keys):
    response = requests.get(f" http://127.0.0.1:5000/{parameter}{keys}")
    if response.status_code == 200:
        return response.json()
    else:
        return None
news_controller=NewsController

import streamlit as st
if "news" not in st.session_state:
    st.session_state.news = []
if "keyword_news" not in st.session_state:
    st.session_state.keyword_news = []
st.title("Cyber News")

with st.sidebar:
    st.title("News Parameters")

    with st.container(border=True):
        st.subheader("Get Cyber-News")
        if st.button('Cyber News'):
            news=fetch_data("news","")
            st.session_state.news=news

    with st.container(border=True):
        st.subheader("Get Cyber-News on keywords")
        key_words= st.text_input('Keywords',placeholder="keywords")
        key_words=list(str(key_words).split(","))
        if st.button('keyword Cyber-News'):
            keyword_news=fetch_data("news_keywords?keywords=",key_words)
            st.session_state.news=keyword_news


for n in st.session_state.news:
    st.text_area(label="News", value=f"Title:{n['title']}\n Date:{n['date']}\nSource:{n['source']}\nURL:{n['url']}", height=120)