import re
from fastapi import HTTPException
from functools import wraps


def validate_url_format(url: str) -> str:
    """URL validation and normalisation"""
    if not url or not url.strip():
        raise ValueError('URL cannot be empty')

    url_pattern = re.compile(
        r'^https?://' 
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|' 
        r'localhost|' 
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' 
        r'(?::\d+)?'  
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    if not url_pattern.match(url):
        raise ValueError('Invalid URL format')

    return url.strip()


def handle_exceptions(error_message: str, not_found_status: bool = False):
    """Decorator for centralised exception handling"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=str(ve))
            except Exception as e:
                print(f"[ERROR] {error_message}: {e}")
                status_code = 404 if not_found_status else 500
                detail = "Short URL not found" if not_found_status else error_message
                raise HTTPException(status_code=status_code, detail=detail)
        return wrapper
    return decorator
