import subprocess
import time
import statistics
import sys

SCRIPT_PATH = "db_update/Update.py"
RUNS = 3

times = []

print(f"Benchmarking {SCRIPT_PATH} for {RUNS} runs\n")

for i in range(RUNS):

    print(f"Run {i+1} starting...")

    start = time.perf_counter()

    subprocess.run([sys.executable, "-m", "db_update.Update"], check=True)

    end = time.perf_counter()

    runtime = end - start
    times.append(runtime)

    print(f"Run {i+1} runtime: {runtime:.2f} seconds\n")


print("----- Benchmark Results -----")

print(f"Runs: {RUNS}")
print(f"Average runtime: {statistics.mean(times):.2f} seconds")
print(f"Min runtime: {min(times):.2f} seconds")
print(f"Max runtime: {max(times):.2f} seconds")