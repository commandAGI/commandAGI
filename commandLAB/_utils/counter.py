_COUNTER: dict[str, int] = {}


def next_for_cls(cls):
    global _COUNTER
    if cls.__name__ not in _COUNTER:
        _COUNTER[cls.__name__] = 0
    _COUNTER[cls.__name__] += 1
    return _COUNTER[cls.__name__]
