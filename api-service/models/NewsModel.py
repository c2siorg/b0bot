# Pinecone replaced by pgvector in GSoC 2026
# Mock implementation to keep the app running during transition

class CybernewsDB:
    def __init__(self):
        pass

    def get_news_collections(self, is_keyword=False, keyword=None, search_type="hybrid", alpha=0.3):
        # Returns mock data until pgvector is wired in by Aqib
        return [
            {
                "headlines": "Mock Article: CVE-2024-1234 Critical Vulnerability Discovered",
                "author": "Security Researcher",
                "newsDate": "27/05/2026",
                "newsURL": "https://example.com/cve-2024-1234",
                "newsImgURL": "N/A",
                "fullNews": "A critical vulnerability has been discovered affecting multiple systems.",
            },
            {
                "headlines": "Mock Article: Ransomware Attack Targets Healthcare Sector",
                "author": "Cyber News Team",
                "newsDate": "26/05/2026",
                "newsURL": "https://example.com/ransomware-healthcare",
                "newsImgURL": "N/A",
                "fullNews": "A new ransomware campaign is targeting hospitals and healthcare providers.",
            },
        ]
