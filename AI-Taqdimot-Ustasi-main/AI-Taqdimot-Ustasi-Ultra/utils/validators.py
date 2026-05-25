import time
from collections import defaultdict
from config import SPAM_LIMIT, SPAM_WINDOW

# {telegram_id: [timestamp, ...]}
_spam_store: dict[int, list[float]] = defaultdict(list)


def is_spam(user_id: int) -> bool:
    """Returns True if user exceeded the rate limit."""
    now = time.time()
    timestamps = _spam_store[user_id]
    # Keep only recent timestamps
    _spam_store[user_id] = [t for t in timestamps if now - t < SPAM_WINDOW]
    _spam_store[user_id].append(now)
    return len(_spam_store[user_id]) > SPAM_LIMIT


def validate_slides_count(value: str) -> int | None:
    """Returns int if valid slide count, else None."""
    try:
        n = int(value.strip())
        if 3 <= n <= 20:
            return n
    except ValueError:
        pass
    return None


def validate_topic(value: str) -> bool:
    """Basic validation for presentation topic."""
    stripped = value.strip()
    return 3 <= len(stripped) <= 300
