#server.py
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, validator, field_validator
from datetime import datetime
import re
from app.url_shortener import UrlShortener, GetOriginalUrl, delete_url_logic, update_url_logic
from app.database import create_tables
from contextlib import asynccontextmanager, AsyncExitStack

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(title="URL Shortener", description="A simple URL shortening service", lifespan=lifespan)
@app.get("/")
async def root():
    return {
        "message": "URL Shortener API",
        "endpoints": {
            "POST /shorten": "Create a new short URL",
            "GET /shorten/{shortCode}": "Retrieve original URL",
            "PUT /shorten/{shortCode}": "Update existing short URL",
            "DELETE /shorten/{shortCode}": "Delete short URL",
            "GET /shorten/{shortCode}/stats": "Get URL statistics"
        }
    }


class CreateUrlRequest(BaseModel):
    url: str

    @field_validator('url')
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError('URL cannot be empty')

        url_pattern = re.compile(
            r'^https?://' 
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|' 
            r'localhost|' 
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' 
            r'(?::\d+)?'  
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v

        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')

        return v.strip()


class UrlResponse(BaseModel):
    id: str
    url: str
    shortCode: str
    createdAt: datetime
    updatedAt: datetime

class UrlStatsResponse(BaseModel):
    id: str
    url: str
    shortCode: str
    createdAt: datetime
    updatedAt: datetime
    accessCount: int


class UpdateUrlRequest(BaseModel):
    url: str

    @field_validator('url')
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError('URL cannot be empty')

        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v

        return v.strip()


@app.post("/shorten", status_code=status.HTTP_201_CREATED, response_model=UrlResponse)
async def create_short_url(data: CreateUrlRequest):
    """Create a new short URL"""
    try:
        shortener = UrlShortener(data.url)

        return UrlResponse(
            id=str(shortener.database_id_for_shortCode),
            url=data.url,
            shortCode=shortener.shortCode,
            createdAt=shortener.created_at,
            updatedAt=shortener.updated_at
        )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"[ERROR] Failed to create short URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to create short URL")


@app.get("/shorten/{shortCode}", response_model=UrlResponse)
async def get_original_url(shortCode: str):
    """Retrieve the original URL from a short URL"""
    try:
        url_getter = GetOriginalUrl(shortCode)
        url_data = url_getter.get_original_url()

        if not url_data:
            raise HTTPException(status_code=404, detail="Short URL not found")

        return UrlResponse(
            id=str(url_data['id']),
            url=url_data['url'],
            shortCode=shortCode,
            createdAt=url_data['createdAt'],
            updatedAt=url_data['updatedAt']
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Could not resolve short code '{shortCode}': {e}")
        raise HTTPException(status_code=404, detail="Short URL not found")

@app.put("/shorten/{shortCode}", response_model=UrlResponse)
async def update_short_url(shortCode: str, data: UpdateUrlRequest):
    """Update an existing short URL"""
    try:
        url_data = update_url_logic(shortCode, data.url)

        return UrlResponse(
            id=str(url_data['id']),
            url=url_data['url'],
            shortCode=shortCode,
            createdAt=url_data['createdAt'],
            updatedAt=url_data['updatedAt']
        )

    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"[ERROR] Failed to update short URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to update short URL")


@app.delete("/shorten/{shortCode}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_short_url(shortCode: str):
    """Delete an existing short URL"""
    try:
        delete_url_logic(shortCode)
        return  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to delete short URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete short URL")


@app.get("/shorten/{shortCode}/stats", response_model=UrlStatsResponse)
async def get_url_stats(shortCode: str):
    """Get statistics for a short URL"""
    try:
        url_getter = GetOriginalUrl(shortCode)
        url_data = url_getter.get_url_stats()

        if not url_data:
            raise HTTPException(status_code=404, detail="Short URL not found")

        return UrlStatsResponse(
            id=str(url_data['id']),
            url=url_data['url'],
            shortCode=shortCode,
            createdAt=url_data['createdAt'],
            updatedAt=url_data['updatedAt'],
            accessCount=url_data['access_count']
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Could not get stats for short code '{shortCode}': {e}")
        raise HTTPException(status_code=404, detail="Short URL not found")