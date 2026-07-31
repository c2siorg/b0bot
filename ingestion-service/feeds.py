"""Curated cybersecurity RSS feed catalog.

Feeds are defined here so poller.py stays focused on fetch/dedup/enqueue logic.
Each entry is verified manually against feedparser before being added.

GSoC in-scope sources (context.md): The Hacker News, Bleeping Computer, Cyware.
Cyware does not expose a working public RSS endpoint — track via sources backend later.

Reddit/Mastodon/YouTube connectors are out of scope — see .cursorrules.
"""

RSS_FEEDS = [
    {
        "name": "The Hacker News",
        "url": "https://thehackernews.com/feeds/posts/default",
        "category": "Breaking news",
    },
    {
        "name": "BleepingComputer",
        "url": "https://www.bleepingcomputer.com/feed/",
        "category": "Malware/incidents",
    },
    {
        "name": "CISA Alerts",
        # Legacy us-cert.cisa.gov/mlist.xml returns Access Denied (CISA retired old RSS in 2025).
        "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
        "category": "Official advisories",
    },
    {
        "name": "Dark Reading",
        "url": "https://www.darkreading.com/rss.xml",
        "category": "Industry news",
    },
    {
        "name": "KrebsOnSecurity",
        "url": "https://krebsonsecurity.com/feed/",
        "category": "Deep investigations",
    },
    {
        "name": "Google Security Blog",
        "url": "https://security.googleblog.com/feeds/posts/default",
        "category": "Vendor advisories",
    },
    {
        "name": "SANS ISC",
        "url": "https://isc.sans.edu/rssfeed.xml",
        "category": "Daily threat brief",
    },
    {
        "name": "SecurityWeek",
        "url": "https://www.securityweek.com/feed/",
        "category": "Weekly roundup",
    },
]
