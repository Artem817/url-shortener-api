import functools

from app.models import URL


def url_only(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for arg in args:
            if not isinstance(arg, URL):
                raise TypeError(f"Argument '{arg}' must be an instance of URL, not {type(arg).__name__}")
        for key, value in kwargs.items():
            if not isinstance(value, URL):
                raise TypeError(f"Keyword argument '{key}' with value '{value}' must be an instance of URL, not {type(value).__name__}")
        return func(*args, **kwargs)
    return wrapper