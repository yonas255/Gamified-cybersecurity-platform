import time
from collections import defaultdict, deque

_BUCKETS = defaultdict(deque)

def check(key: str, limit: int, window_seconds: int):
    now = time.time()
    q = _BUCKETS[key]

    cutoff = now - window_seconds
    while q and q[0] < cutoff:
        q.popleft()

    if len(q) >= limit:
        retry_after = int(q[0] + window_seconds - now) + 1
        return False, 0, max(retry_after, 1)

    q.append(now)
    remaining = limit - len(q)
    return True, remaining, 0
