import numpy as np
from shapely.geometry import box as Box
from shapely.geometry import Polygon

print("Testing NaN coords...")
try:
    Box(0, 0, np.nan, 10)
    print("Box(0,0,nan,10) OK")
except Exception as e:
    print(f"Box(0,0,nan,10) FAILED: {e}")

print("Testing inf coords...")
try:
    Box(0, 0, np.inf, 10)
    print("Box(0,0,inf,10) OK")
except Exception as e:
    print(f"Box(0,0,inf,10) FAILED: {e}")

print("Testing zero area box...")
try:
    Box(0, 0, 0, 0)
    print("Box(0,0,0,0) OK")
except Exception as e:
    print(f"Box(0,0,0,0) FAILED: {e}")

print("Testing line box...")
try:
    Box(0, 0, 10, 0)
    print("Box(0,0,10,0) OK")
except Exception as e:
    print(f"Box(0,0,10,0) FAILED: {e}")
