from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, field_validator
from datetime import datetime
from app.url_shortener import UrlShortener, GetOriginalUrl, delete_url_logic, update_url_logic
from app.database import create_tables
from contextlib import asynccontextmanager

from app.validation import handle_exceptions, validate_url_format


def create_url_response(url_data: dict, short_code: str) -> 'UrlResponse':
    """Creates a UrlResponse from data"""
    return UrlResponse(
        id=str(url_data['id']),
        url=url_data['url'],
        shortCode=short_code,
        createdAt=url_data['createdAt'],
        updatedAt=url_data['updatedAt']
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(title="URL Shortener", description="A simple URL shortening service", lifespan=lifespan)

class BaseUrlRequest(BaseModel):
    """Base class for URL validation"""
    url: str

    @field_validator('url')
    def validate_url(cls, v):
        return validate_url_format(v)

class CreateUrlRequest(BaseUrlRequest):
    """Request to create a short URL"""
    pass

class UpdateUrlRequest(BaseModel):
    """URL update request (simplified validation)"""
    url: str

    @field_validator('url')
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError('URL cannot be empty')

        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v

        return v.strip()

class UrlResponse(BaseModel):
    """Response with URL data"""
    id: str
    url: str
    shortCode: str
    createdAt: datetime
    updatedAt: datetime

class UrlStatsResponse(BaseModel):
    """Response with URL statistics"""
    id: str
    url: str
    shortCode: str
    createdAt: datetime
    updatedAt: datetime
    accessCount: int

@app.get("/")
async def root():
    """Root endpoint with API description"""
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

@app.post("/shorten", status_code=status.HTTP_201_CREATED, response_model=UrlResponse)
@handle_exceptions("Failed to create short URL")
async def create_short_url(data: CreateUrlRequest):
    """Create a new short URL"""
    shortener = UrlShortener(data.url)

    return UrlResponse(
        id=str(shortener.database_id_for_shortCode),
        url=data.url,
        shortCode=shortener.shortCode,
        createdAt=shortener.created_at,
        updatedAt=shortener.updated_at
    )

@app.get("/shorten/{shortCode}", response_model=UrlResponse)
@handle_exceptions("Could not resolve short code", not_found_status=True)
async def get_original_url(shortCode: str):
    """Retrieve the original URL from a short URL"""
    url_getter = GetOriginalUrl(shortCode)
    url_data = url_getter.get_original_url()

    if not url_data:
        raise HTTPException(status_code=404, detail="Short URL not found")

    return create_url_response(url_data, shortCode)

@app.put("/shorten/{shortCode}", response_model=UrlResponse)
@handle_exceptions("Failed to update short URL")
async def update_short_url(shortCode: str, data: UpdateUrlRequest):
    """Update an existing short URL"""
    url_data = update_url_logic(shortCode, data.url)
    return create_url_response(url_data, shortCode)

@app.delete("/shorten/{shortCode}", status_code=status.HTTP_204_NO_CONTENT)
@handle_exceptions("Failed to delete short URL")
async def delete_short_url(shortCode: str):
    """Delete an existing short URL"""
    delete_url_logic(shortCode)

@app.get("/shorten/{shortCode}/stats", response_model=UrlStatsResponse)
@handle_exceptions("Could not get stats for short code", not_found_status=True)
async def get_url_stats(shortCode: str):
    """Get statistics for a short URL"""
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