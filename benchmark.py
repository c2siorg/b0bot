import time
from statistics import mean
from cybernews.CyberNews import CyberNews


def run_test(news_type, runs=6):
    times = []

    for i in range(runs):
        news = CyberNews()

        start = time.perf_counter()
        data = news.get_news(news_type)
        end = time.perf_counter()

        duration = end - start
        print(f"Run {i+1}: {duration:.4f} sec | Articles: {len(data)}")

        times.append(duration)

    # Discard first run (cold start effect)
    avg = mean(times[1:])
    print(f"\nAverage (excluding first run): {avg:.4f} sec\n")

    return avg


if __name__ == "__main__":
    run_test("general", runs=6)