import time # time module
from collections import defaultdict, deque # data structures for efficiently request timestamp

_BUCKETS = defaultdict(deque) # creating a dictionary where each key stores a queue of timestamps for rate limiting

# function to check if request is allowed based on rate limits
def check(key: str, limit: int, window_seconds: int):
    now = time.time() # current time
    q = _BUCKETS[key] # retrieves the queue for given key

    # removes timestamps that are outside the allowed time window to keep only recent requests
    cutoff = now - window_seconds
    while q and q[0] < cutoff:
        q.popleft()

    # if the number of requests exceeds the limit, calculates how long the user must wait before retrying and blocks the request
    if len(q) >= limit:
        retry_after = int(q[0] + window_seconds - now) + 1
        return False, 0, max(retry_after, 1)

    # adding the current request timestamp, calculates remaining allowed requests and return success status
    q.append(now)
    remaining = limit - len(q)
    return True, remaining, 0
