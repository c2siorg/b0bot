import time
import concurrent.futures
from statistics import mean
from cybernews.CyberNews import CyberNews


def single_run(news_type):
    news = CyberNews()
    return news.get_news(news_type)


def run_concurrent_test(news_type, users=1, runs=5):
    times = []

    for r in range(runs):
        start = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=users) as executor:
            futures = [executor.submit(single_run, news_type) for _ in range(users)]
            results = [f.result() for f in futures]

        end = time.perf_counter()

        duration = end - start
        print(f"Run {r+1}: {duration:.4f} sec | Total Articles: {sum(len(r) for r in results)}")

        times.append(duration)

    avg = mean(times[1:])
    print(f"\nUsers: {users}")
    print(f"Average (excluding first run): {avg:.4f} sec\n")


if __name__ == "__main__":
    for users in [1, 5, 10, 20, 40]:
        run_concurrent_test("general", users=users)