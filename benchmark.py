import time
from statistics import mean
from cybernews.CyberNews import CyberNews


def run_scaled_test(news_type, scale=1, runs=6):
    times = []

    for i in range(runs):
        news = CyberNews()

        # Get original source list
        original_sources = None
        for category in news._news_types:
            if news_type in category:
                original_sources = category[news_type]
                break

        if original_sources is None:
            raise ValueError("Invalid news type")

        # Scale sources artificially
        scaled_sources = original_sources * scale

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

    # Test increasing concurrency pressure
    for scale in [1, 5, 10, 20]:
        run_scaled_test("general", scale=scale, runs=6)