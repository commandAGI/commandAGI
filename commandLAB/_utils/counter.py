_COUNTER: dict[str, int] = {}


def next_for_cls(key):
    """Get the next counter value for a class.

    Args:
        key: Either a class object or a class name as string

    Returns:
        int: The next counter value for this class
    """
    global _COUNTER
    if key not in _COUNTER:
        _COUNTER[key] = 0
    _COUNTER[key] += 1
    return _COUNTER[key]
