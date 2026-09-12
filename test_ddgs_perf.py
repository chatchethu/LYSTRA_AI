import time
from ddgs import DDGS

print("Starting search...")
start = time.time()
with DDGS() as ddgs:
    res = list(ddgs.text("what is latest ai news", max_results=3))
    print(f"Got {len(res)} results in {time.time() - start:.2f} seconds.")
    for r in res:
        print("-", r['title'])
