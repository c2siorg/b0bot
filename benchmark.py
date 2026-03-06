from cybernews.CyberNews import CyberNews
from cybernews.extractor import Extractor
import time


def run_benchmark(runs=5):
    extractor = Extractor()
    cyber = CyberNews()

    # pick a valid news type
    news_type = cyber.get_news_types[0]

    timings = []

    for i in range(runs):
        start = time.perf_counter()
        cyber.get_news(news_type)
        end = time.perf_counter()

        duration = end - start
        timings.append(duration)

        print(f"Run {i+1}: {duration:.4f} sec")

    avg = sum(timings[1:]) / (runs - 1)
    print(f"\nAverage (excluding first run): {avg:.4f} sec")


if __name__ == "__main__":
    run_benchmark()