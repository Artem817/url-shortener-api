## URL Shortener API

A simple RESTful API service for shortening long URLs, built with FastAPI and PostgreSQL.

### About the Project

This project implements a URL shortening service with the following features:

* Create short URLs with automatically generated unique codes
* Retrieve original URLs by short codes
* Update existing URLs
* Delete short URLs
* Track usage statistics (number of visits)
* Automatic URL validation
* HTTP/HTTPS protocol support
* Base62 encoding for compact short codes

### Technologies

* **FastAPI** – web framework for Python
* **SQLAlchemy** – ORM for database interaction
* **PostgreSQL** – relational database
* **Pydantic** – data validation
* **Docker & Docker Compose** – containerization

### Quick Start

#### Prerequisites

* Docker and Docker Compose
* Git

#### Installation

1. **Clone the repository:**

```bash
git clone <repo-url>
```

2. **Create a `.env` file:**

```env
# Database
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=url_shortener
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# PgAdmin
PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=admin
```

3. **Start the project:**

```bash
docker-compose up -d
```

4. **Wait for services to be ready:**

```bash
docker-compose logs -f api
```

### Service Access

* **API:** [http://localhost:8001](http://localhost:8001)
* **API Documentation (Swagger):** [http://localhost:8001/docs](http://localhost:8001/docs)
* **PgAdmin:** [http://localhost:5050](http://localhost:5050)
* **PostgreSQL:** localhost:5432

> **Note:** While the API runs internally on port 8000, it is exposed on **port 8001** externally as defined in `docker-compose.yml`.

### API Endpoints

#### Root Endpoint

```
GET /
```

Returns service information and available endpoints.

#### Create Short URL

```
POST /shorten
Content-Type: application/json

{
  "url": "https://www.example.com/very/long/url"
}
```

**Response (201 Created):**

```json
{
  "id": "1",
  "url": "https://www.example.com/very/long/url",
  "shortCode": "abc123",
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

#### Retrieve Original URL

```
GET /shorten/{shortCode}
```

#### Update URL

```
PUT /shorten/{shortCode}
Content-Type: application/json

{
  "url": "https://www.example.com/updated/url"
}
```

#### Delete URL

```
DELETE /shorten/{shortCode}
```

#### Get URL Statistics

```
GET /shorten/{shortCode}/stats
```

**Response (200 OK):**

```json
{
  "id": "1",
  "url": "https://www.example.com/very/long/url",
  "shortCode": "abc123",
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z",
  "accessCount": 25
}
```

### Testing

#### Swagger UI

The easiest way to test the API is using the interactive documentation:

```
http://localhost:8001/docs
```

#### Postman

Import the endpoints into Postman using the base URL:

```
http://localhost:8001
```

#### cURL Examples

**Create a short URL:**

```bash
curl -X POST "http://localhost:8001/shorten" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.google.com"}'
```

**Retrieve original URL:**

```bash
curl -X GET "http://localhost:8001/shorten/abc123"
```

**Get statistics:**

```bash
curl -X GET "http://localhost:8001/shorten/abc123/stats"
```

### Project Management

#### Stop Services

```bash
docker-compose down
```

#### View Logs

```bash
docker-compose logs -f api
docker-compose logs -f db
```

#### Restart Services

```bash
docker-compose restart
```

#### Clear Data

```bash
docker-compose down -v
docker-compose up -d
```

### URL Encoding with Base62

This service uses a **Base62 encoding scheme** (`0-9a-zA-Z`) to convert database `id` values into short, URL-friendly strings.

Instead of storing the short code in the database, the `id` is deterministically encoded and decoded:

```python
url_id = decode(shortCode, BASE62)
url_object = session.query(URL).filter(URL.id == url_id).first()
```

This eliminates the need for an additional `shortcode` field in the model.

* For small datasets, short URLs will be numeric: `1`, `2`, `3`, ...
* As the dataset grows, encoded strings become more varied: `a`, `Z`, `1c`, `bG`, etc.

### Project Structure

```
url-shortener-api/
├── app/
│   ├── __init__.py
│   ├── server.py          # FastAPI application
│   ├── models.py          # SQLAlchemy models
│   ├── database.py        # Database configuration
│   ├── url_shortener.py   # Business logic
│   ├── base62.py          # Base62 encoding logic
│   └── decorators_security.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
└── README.md
```

This project is based on the [URL Shortening Service project on roadmap.sh](https://roadmap.sh/projects/url-shortening-service)
