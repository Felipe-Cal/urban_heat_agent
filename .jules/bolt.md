## 2025-02-28 - Optimize OSM element processing
**Learning:** In Python, multiple `O(n)` list comprehensions over a large dictionary/JSON array (like OSM tags) can be a significant bottleneck due to redundant dict accesses.
**Action:** Combine multiple array comprehensions over the same collection into a single-pass `for` loop using independent `if` statements to handle objects matching multiple conditions without duplication.
