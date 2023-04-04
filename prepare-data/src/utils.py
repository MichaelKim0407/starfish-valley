from collections import defaultdict


def skip_empty_values(iterable):
    for key, value in iterable:
        if not value:
            continue
        yield key, value


def merge(iterable):
    result = defaultdict(list)
    for key, value in iterable:
        result[key].append(value)
    return dict(result)
