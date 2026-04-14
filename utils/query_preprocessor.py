import re

# Generic words that add noise to queries
STOPWORDS = {
    "news", "latest", "recent", "update", "article",
    "report", "today", "current", "new", "blog", "post"
}


def normalize_query(text: str) -> str:
    """
    Lowercase + remove extra whitespace
    """
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def standardize_cve_patterns(text: str) -> str:
    """
    Normalize different CVE formats to: CVE-YYYY-NNNN
    Handles:
    - cve 2024 1234
    - CVE-2024-1234
    - cve2024-1234
    - CVE_2024_1234
    """

    def replacer(match):
        year = match.group(1)
        num = match.group(2)
        return f"CVE-{year}-{num}"

    pattern = r"cve[\s_-]?(\d{4})[\s_-]?(\d{4,7})"
    text = re.sub(pattern, replacer, text, flags=re.IGNORECASE)

    return text


def filter_stopwords(text: str) -> str:
    """
    Remove generic noise words
    """
    words = text.split()
    filtered = [w for w in words if w not in STOPWORDS]
    return " ".join(filtered)


def preprocess_query(text: str) -> str:
    """
    Full preprocessing pipeline
    """
    text = normalize_query(text)
    text = standardize_cve_patterns(text)
    text = filter_stopwords(text)
    return text