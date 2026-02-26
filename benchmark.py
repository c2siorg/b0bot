import time
from statistics import mean
from cybernews.CyberNews import CyberNews


def get_sources(news, news_type):
    for category in news._news_types:
        if news_type in category:
            return category[news_type]
    raise ValueError("Invalid news type")


def run_scaled_test(news_type, scale=1, runs=6):
    times = []

    for i in range(runs):
        news = CyberNews()
        original_sources = get_sources(news, news_type)

        # Create independent copies so internal mutation doesn’t interfere
        scaled_sources = [dict(item) for _ in range(scale) for item in original_sources]

        start = time.perf_counter()
        data = news._extractor.data_extractor(scaled_sources)
        end = time.perf_counter()

        duration = end - start
        print(f"Run {i+1}: {duration:.4f} sec | Articles: {len(data)}")

        times.append(duration)

    avg = mean(times[1:])  # discard first run
    print(f"\nScale: {scale}x")
    print(f"Average (excluding first run): {avg:.4f} sec\n")

    return avg


if __name__ == "__main__":
    for scale in [1, 5, 10, 20]:
        run_scaled_test("general", scale=scale, runs=6)