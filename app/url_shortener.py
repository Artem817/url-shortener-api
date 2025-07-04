# url_shortener.py
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from app.base62 import encode, decode, BASE62
from app.decorators_security import url_only
from app.models import URL
from app.database import SessionLocal


def get_url_object_by_shortCode(shortCode: str) -> URL:
    session = SessionLocal()
    try:
        url_id = decode(shortCode, BASE62)
        url_object = session.query(URL).filter(URL.id == url_id).first()

        if not url_object:
            raise HTTPException(status_code=404, detail="Short URL not found")

        return url_object

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        session.close()

@url_only
def access_counter(url_object: URL):
    """Increment access counter for URL"""
    try:
        url_object.access_count += 1
        url_object.updated_at = datetime.now(timezone.utc)
        return url_object
    except Exception as e:
        print(f"[ERROR] Failed to increment access counter: {e}")
        raise HTTPException(status_code=500, detail="Failed to update access count")


def update_url_logic(shortCode: str, new_url: str):
    """Update URL logic"""
    session = SessionLocal()
    try:
        url_to_update = get_url_object_by_shortCode(shortCode)

        if not new_url or not new_url.strip():
            raise ValueError("URL cannot be empty")

        if not new_url.startswith(('http://', 'https://')):
            new_url = 'https://' + new_url

        url_to_update.url = new_url.strip()
        url_to_update.updated_at = datetime.utcnow()

        session.add(url_to_update)
        session.commit()
        session.refresh(url_to_update)

        return {
            'id': url_to_update.id,
            'url': url_to_update.url,
            'createdAt': url_to_update.created_at,
            'updatedAt': url_to_update.updated_at
        }

    except HTTPException:
        raise
    except ValueError:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        print(f"[ERROR] Database error during URL update: {e}")
        raise HTTPException(status_code=500, detail="Database error during update")
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to update URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to update URL")
    finally:
        session.close()


def delete_url_logic(shortCode: str):
    """Delete URL logic"""
    session = SessionLocal()
    try:
        url_to_delete = get_url_object_by_shortCode(shortCode)

        session.delete(url_to_delete)
        session.commit()

        return

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        print(f"[ERROR] Database error during deletion: {e}")
        raise HTTPException(status_code=500, detail="Database error during deletion")
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to delete URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete URL")
    finally:
        session.close()


class GetOriginalUrl:
    def __init__(self, shortCode):
        self.shortCode = shortCode

    def get_original_url_object(self, url_id):
        """Get URL object by ID"""
        session = SessionLocal()
        try:
            url_object = session.query(URL).filter(URL.id == url_id).first()

            if not url_object:
                raise HTTPException(status_code=404, detail="Short URL not found")

            return url_object

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            session.close()

    def get_original_url(self):
        """Get original URL with access counter increment"""
        session = SessionLocal()
        try:
            url_id = decode(self.shortCode, BASE62)
            url_object = self.get_original_url_object(url_id)

            if not url_object:
                return None

            url_object = access_counter(url_object)
            session.add(url_object)
            session.commit()
            session.refresh(url_object)

            return {
                'id': url_object.id,
                'url': url_object.url,
                'access_count': url_object.access_count,
                'createdAt': url_object.created_at,
                'updatedAt': url_object.updated_at
            }

        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Could not get original URL: {str(e)}")
        finally:
            session.close()

    def get_url_stats(self):
        """Get URL statistics without incrementing access counter"""
        session = SessionLocal()
        try:
            url_id = decode(self.shortCode, BASE62)
            url_object = self.get_original_url_object(url_id)

            if not url_object:
                return None

            return {
                'id': url_object.id,
                'url': url_object.url,
                'access_count': url_object.access_count,
                'createdAt': url_object.created_at,
                'updatedAt': url_object.updated_at
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not get URL stats: {str(e)}")
        finally:
            session.close()


class UrlShortener:
    def __init__(self, url):
        self.url = url.strip()
        self.database_id_for_shortCode = self._post_url()
        self.shortCode = encode(self.database_id_for_shortCode, BASE62)

        session = SessionLocal()
        try:
            url_object = session.query(URL).filter(URL.id == self.database_id_for_shortCode).first()
            self.created_at = url_object.created_at
            self.updated_at = url_object.updated_at
        finally:
            session.close()

    def _post_url(self):
        """Create new URL in database"""
        session = SessionLocal()
        try:
            clean_url = ''.join(char for char in self.url if ord(char) >= 32 or char in '\t\n\r').strip()

            new_url_object = URL(
                url=clean_url,
                access_count=0,
                created_at= datetime.now(timezone.utc),
                updated_at= datetime.now(timezone.utc)
            )

            session.add(new_url_object)
            session.commit()
            session.refresh(new_url_object)

            return new_url_object.id

        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create short URL: {str(e)}")
        finally:
            session.close()