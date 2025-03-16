import functools


def annotation(key, value):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        setattr(wrapper, key, value)
        return wrapper

    return decorator


def gather_annotated_attr_keys(obj, annotation_key):
    annotated_attrs_keys = []
    for attr_key in dir(obj):
        attr_value = getattr(obj, attr_key)
        if hasattr(attr_value, annotation_key):
            annotated_attrs_keys.append(attr_key)
    return annotated_attrs_keys

