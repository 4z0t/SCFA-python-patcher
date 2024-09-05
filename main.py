import sys
import time
import Patcher

if __name__ == "__main__":
    start = time.time()
    Patcher.patch(*sys.argv)
    end = time.time()
    print(f"Patched in {end-start:.2f}s")
