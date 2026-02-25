## 2025-05-18 - Vectorization Win
**Learning:** Python loops for numeric operations on large lists (e.g. 100k items) are significantly slower (300x) than numpy vectorized operations.
**Action:** Always look for opportunities to replace `for` loops with `np.column_stack`, `np.clip`, and broadcasting when handling geographic data points.
