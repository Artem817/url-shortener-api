# url_shortener.py
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from app.base62 import encode, decode, BASE62
from app.decorators_security import url_only
from app.models import URL
from app.database import SessionLocal

@contextmanager
def get_session():
    """Context manager for database sessions"""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_url_object_by_id(url_id: int) -> URL:
    """Get URL object by ID with proper error handling"""
    with get_session() as session:
        try:
            url_object = session.query(URL).filter(URL.id == url_id).first()
            if not url_object:
                raise HTTPException(status_code=404, detail="Short URL not found")
            return url_object
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


def get_url_object_by_shortcode(shortcode: str) -> URL:
    """Get URL object by shortcode"""
    try:
        url_id = decode(shortcode, BASE62)
        return get_url_object_by_id(url_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalid short code: {str(e)}")


def normalize_url(url: str) -> str:
    """Normalize URL format"""
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    
    clean_url = url.strip()
    if not clean_url.startswith(('http://', 'https://')):
        clean_url = 'https://' + clean_url
    
    clean_url = ''.join(char for char in clean_url if ord(char) >= 32 or char in '\t\n\r').strip()
    return clean_url


def create_url_dict(url_object: URL) -> dict:
    """Create standardized URL dictionary"""
    return {
        'id': url_object.id,
        'url': url_object.url,
        'access_count': url_object.access_count,
        'createdAt': url_object.created_at,
        'updatedAt': url_object.updated_at
    }


@url_only
def increment_access_counter(url_object: URL) -> URL:
    """Increment access counter for URL"""
    try:
        url_object.access_count += 1
        url_object.updated_at = datetime.now(timezone.utc)
        return url_object
    except Exception as e:
        print(f"[ERROR] Failed to increment access counter: {e}")
        raise HTTPException(status_code=500, detail="Failed to update access count")


def update_url_logic(shortcode: str, new_url: str) -> dict:
    """Update URL logic with improved error handling"""
    normalized_url = normalize_url(new_url)
    
    with get_session() as session:
        try:
            url_object = get_url_object_by_shortcode(shortcode)
            
            url_object = session.merge(url_object)
            url_object.url = normalized_url
            url_object.updated_at = datetime.now(timezone.utc)
            
            result = create_url_dict(url_object)
            session.commit()
            
            return result
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            print(f"[ERROR] Database error during URL update: {e}")
            raise HTTPException(status_code=500, detail="Database error during update")
        except Exception as e:
            print(f"[ERROR] Failed to update URL: {e}")
            raise HTTPException(status_code=500, detail="Failed to update URL")


def delete_url_logic(shortcode: str) -> None:
    """Delete URL logic with improved error handling"""
    with get_session() as session:
        try:
            url_object = get_url_object_by_shortcode(shortcode)
            
            url_object = session.merge(url_object)
            session.delete(url_object)
            session.commit()
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            print(f"[ERROR] Database error during deletion: {e}")
            raise HTTPException(status_code=500, detail="Database error during deletion")
        except Exception as e:
            print(f"[ERROR] Failed to delete URL: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete URL")


class GetOriginalUrl:
    """Handles URL retrieval operations"""
    
    def __init__(self, shortcode: str):
        self.shortcode = shortcode
    
    def get_original_url(self) -> dict:
        """Get original URL with access counter increment"""
        with get_session() as session:
            try:
                url_object = get_url_object_by_shortcode(self.shortcode)
                
                url_object = session.merge(url_object)
                url_object = increment_access_counter(url_object)
                
                result = create_url_dict(url_object)
                session.commit()
                
                return result
                
            except HTTPException:
                raise
            except Exception as e:
                print(f"[ERROR] Could not get original URL: {e}")
                raise HTTPException(status_code=500, detail=f"Could not get original URL: {str(e)}")
    
    def get_url_stats(self) -> dict:
        """Get URL statistics without incrementing access counter"""
        try:
            url_object = get_url_object_by_shortcode(self.shortcode)
            return create_url_dict(url_object)
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERROR] Could not get URL stats: {e}")
            raise HTTPException(status_code=500, detail=f"Could not get URL stats: {str(e)}")

class UrlShortener:
    """Handles URL shortening operations"""
    
    def __init__(self, url: str):
        self.url = normalize_url(url)
        result = self._create_url()
        self.database_id_for_shortCode = result['id']
        self.shortCode = encode(self.database_id_for_shortCode, BASE62)
        self.created_at = result['created_at']
        self.updated_at = result['updated_at']
    
    def _create_url(self) -> dict:
        """Create new URL in database"""
        with get_session() as session:
            try:
                new_url_object = URL(
                    url=self.url,
                    access_count=0,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                session.add(new_url_object)
                session.flush()  
                
                result = {
                    'id': new_url_object.id,
                    'created_at': new_url_object.created_at,
                    'updated_at': new_url_object.updated_at
                }
                
                session.commit()
                return result
                
            except SQLAlchemyError as e:
                print(f"[ERROR] Database error during URL creation: {e}")
                raise HTTPException(status_code=500, detail="Database error during creation")
            except Exception as e:
                print(f"[ERROR] Failed to create short URL: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to create short URL: {str(e)}")