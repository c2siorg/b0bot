"""RSS feeds for polling.

Default feeds used only when the ``sources`` table has no active rows or the
database is unreachable. Normal operation reads active rows from Postgres.
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
