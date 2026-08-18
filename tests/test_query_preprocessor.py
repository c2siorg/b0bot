from utils.query_preprocessor import preprocess_query


def test_cve_variants():
    inputs = [
        "cve 2024 1234",
        "CVE-2024-1234",
        "cve2024-1234",
        "CVE_2024_1234",
        "cve 2024-1234"
    ]

    for inp in inputs:
        result = preprocess_query(inp)
        assert "CVE-2024-1234" in result


def test_stopwords_removed():
    text = "latest ransomware news update"
    result = preprocess_query(text)

    assert "latest" not in result
    assert "news" not in result
    assert "update" not in result


def test_lowercase_and_spacing():
    text = "   Latest   CVE 2024 1234   "
    result = preprocess_query(text)

    assert result == "CVE-2024-1234"


def test_full_pipeline():
    text = "Latest CVE 2024 1234 ransomware news"
    result = preprocess_query(text)

    assert "CVE-2024-1234" in result
    assert "ransomware" in result
    assert "latest" not in result