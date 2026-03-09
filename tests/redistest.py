import time
import requests


url = "http://127.0.0.1:5000/news"  # Change if needed

# Measure before caching
start_time = time.time()
response = requests.get(url)
end_time = time.time()
print(f" The time taken to fetch the news data from the actual source: {(end_time - start_time) * 1000:.2f} ms")

# Measure after caching
start_time = time.time()
response = requests.get(url)
end_time = time.time()
print(f"The time taken to retrieve the data from Redis: {(end_time - start_time) * 1000:.2f} ms")