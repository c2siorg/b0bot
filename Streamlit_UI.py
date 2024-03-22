from controllers.NewsController import NewsController
import requests
def fetch_data(parameter,keys):
    response = requests.get(f" http://127.0.0.1:5000/{parameter}{keys}")
    if response.status_code == 200:
        return response.json()
    else:
        return None
news_controller=NewsController

#l=[{"date":"03/18/2024","source":"The Hacker News","title":"Fortra Patches Critical RCE Vulnerability in FileCatalyst Transfer Tool","url":"https://thehackernews.com/2024/03/fortra-patches-critical-rce.html"},{"date":"03/18/2024","source":"The Hacker News","title":"WordPress Admins Urged to Remove miniOrange Plugins Due to Critical Flaw","url":"https://thehackernews.com/2024/03/wordpress-admins-urged-to-remove.html"},{"date":"03/15/2024","source":"The Hacker News","title":"Malicious Ads Targeting Chinese Users with Fake Notepad++ and VNote Installers","url":"https://thehackernews.com/2024/03/malicious-ads-targeting-chinese-users.html"},{"date":"03/14/2024","source":"The Hacker News","title":"DarkGate Malware Exploited Recently Patched Microsoft Flaw in Zero-Day Attack","url":"https://thehackernews.com/2024/03/darkgate-malware-exploits-recently.html"},{"date":"03/14/2024","source":"The Hacker News","title":"Fortinet Warns of Severe SQLi Vulnerability in FortiClientEMS Software","url":"https://thehackernews.com/2024/03/fortinet-warns-of-severe-sqli.html"},{"date":"03/11/2024","source":"The Hacker News","title":"Magnet Goblin Hacker Group Leveraging 1-Day Exploits to Deploy Nerbian RAT","url":"https://thehackernews.com/2024/03/magnet-goblin-hacker-group-leveraging-1.html"},{"date":"03/08/2024","source":"The Hacker News","title":"CISA Warns of Actively Exploited JetBrains TeamCity Vulnerability","url":"https://thehackernews.com/2024/03/cisa-warns-of-actively-exploited.html"},{"date":"03/08/2024","source":"The Hacker News","title":"QEMU Emulator Exploited as Tunneling Tool to Breach Company Network","url":"https://thehackernews.com/2024/03/cybercriminals-utilize-qemu-emulator-as.html"},{"date":"03/07/2024","source":"The Hacker News","title":"New Python-Based Snake Info Stealer Spreading Through Facebook Messages","url":"https://thehackernews.com/2024/03/new-python-based-snake-info-stealer.html"},{"date":"03/06/2024","source":"The Hacker News","title":"Urgent: Apple Issues Critical Updates for Actively Exploited Zero-Day Flaws","url":"https://thehackernews.com/2024/03/urgent-apple-issues-critical-updates.html"}]
import streamlit as st
if "news" not in st.session_state:
    st.session_state.news = []
if "keyword_news" not in st.session_state:
    st.session_state.keyword_news = []
st.title("Cyber News")

with st.sidebar:
    st.title("News Parameters")
    # button=st.button("Reset", type="primary")
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