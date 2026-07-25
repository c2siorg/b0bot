"""Curated cybersecurity RSS feed catalog.

Feeds are defined here so poller.py stays focused on fetch/dedup/enqueue logic.
Reddit/Mastodon/YouTube connectors are out of scope for GSoC — see .cursorrules.
"""

RSS_FEEDS = [
    {
        "name": "The Hacker News",
        "url": "https://thehackernews.com/feeds/posts/default",
        "category": "Breaking news",
    },
    {
        "name": "KrebsOnSecurity",
        "url": "https://krebsonsecurity.com/feed/",
        "category": "Deep investigations",
    },
    {
        "name": "BleepingComputer",
        "url": "https://www.bleepingcomputer.com/feed/",
        "category": "Malware/incidents",
    },
    {
        "name": "CISA Alerts",
        "url": "https://us-cert.cisa.gov/mlist.xml",
        "category": "Official advisories",
    },
    {
        "name": "CyberScoop",
        "url": "https://www.cyberscoop.com/feed/",
        "category": "Industry analysis",
    },
    {
        "name": "SecurityWeek",
        "url": "https://www.securityweek.com/feed",
        "category": "Weekly roundup",
    },
]
