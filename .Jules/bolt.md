## 2024-05-22 - Thermal Data Vectorization
**Learning:** Python loops for arithmetic operations on large lists (2000+ items) are significantly slower than NumPy vectorization (31x slower in this case).
**Action:** When working with numerical data generation or interpolation, always prefer `np.array` operations (broadcasting, ufuncs) over list comprehensions or `for` loops.
