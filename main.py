import sys
import time
import patcher

if __name__ == "__main__":
    start = time.time()
    patcher.patch(*sys.argv)
    end = time.time()
    print(f"Patched in {end-start:.2f}s")
