import time
from statistics import mean
from cybernews.CyberNews import CyberNews


def benchmark(news_type, runs=5):
    times = []

    for i in range(runs):
        news = CyberNews()

        start = time.perf_counter()
        data = news.get_news(news_type)
        end = time.perf_counter()

        duration = end - start
        print(f"Run {i+1}: {duration:.4f} sec | Articles: {len(data)}")
        times.append(duration)

    print("\nAverage Time:", round(mean(times), 4), "seconds")
    return mean(times)


if __name__ == "__main__":
    benchmark("general", runs=5)