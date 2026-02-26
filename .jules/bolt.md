## 2025-05-23 - Sequential API Calls in Data Generator
**Learning:** The `_fetch_openaq_sensors` function was making sequential synchronous HTTP requests inside a loop to fetch sensor details. This caused a significant delay (O(N) latency). Streamlit apps are synchronous by default, so blocking I/O on the main thread directly impacts load time.
**Action:** Always check for loops containing `requests.get` or similar blocking calls. Refactor to use `concurrent.futures.ThreadPoolExecutor` to parallelize these I/O bound operations.
