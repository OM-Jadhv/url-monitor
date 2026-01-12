# URL Monitor Service

A FastAPI-based URL monitoring service that checks website availability and tracks response latency. Monitor multiple URLs with customizable check intervals and maintain a complete history of health checks.

## Features

- 🔍 **URL Monitoring**: Monitor any local or internet URL
- ⏱️ **Latency Tracking**: Measure response times in milliseconds
- 📊 **Health History**: Store complete health check history in SQLite
- ⚙️ **Flexible Intervals**: Set check intervals from 5 minutes to 1 hour
- 🔄 **Background Monitoring**: Automatic continuous monitoring in the background
- 📡 **RESTful API**: Full CRUD operations via REST API
- 🐳 **Docker Ready**: Complete Docker and Docker Compose setup
- 📝 **Interactive Docs**: Auto-generated Swagger UI documentation

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **SQLite**: Lightweight, file-based database
- **HTTPX**: Async HTTP client for URL checking
- **Docker**: Containerization
- **Uvicorn**: Lightning-fast ASGI server

## Project Structure

```
url-monitor-service/
├── main.py                 # Main FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── README.md              # This file
└── data/                  # Database storage (created automatically)
    └── url_monitor.db     # SQLite database file
```

## Prerequisites

- Docker and Docker Compose installed on your system
- OR Python 3.11+ (for local development)

## Quick Start with Docker

### 1. Clone the Repository

```bash
git clone https://github.com/OM-Jadhv/url-monitor.git
cd url-monitor-service
```

### 2. Start the Service

```bash
docker-compose up --build
```

The service will be available at `http://localhost:8000`

### 3. Access the API Documentation

Open your browser and navigate to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Local Development (Without Docker)

### 1. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create Data Directory

```bash
mkdir -p data
```

### 4. Run the Application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Usage

### Create a URL Monitor

```bash
curl -X POST "http://localhost:8000/monitors/" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://google.com",
    "check_interval": 5
  }'
```

**Response:**
```json
{
  "id": 1,
  "url": "https://google.com",
  "check_interval": 5,
  "is_active": true,
  "created_at": "2025-01-12T10:30:00.000000"
}
```

### List All Monitors

```bash
curl http://localhost:8000/monitors/
```

### Get a Specific Monitor

```bash
curl http://localhost:8000/monitors/1
```

### Get Health Check History

```bash
curl http://localhost:8000/monitors/1/checks
```

**Response:**
```json
[
  {
    "id": 1,
    "monitor_id": 1,
    "status_code": 200,
    "latency": 145.32,
    "is_up": true,
    "error_message": null,
    "checked_at": "2025-01-12T10:35:00.000000"
  }
]
```

### Deactivate a Monitor

```bash
curl -X DELETE http://localhost:8000/monitors/1
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/monitors/` | Create a new URL monitor |
| `GET` | `/monitors/` | List all monitors |
| `GET` | `/monitors/{id}` | Get a specific monitor |
| `DELETE` | `/monitors/{id}` | Deactivate a monitor |
| `GET` | `/monitors/{id}/checks` | Get health check history |
| `GET` | `/` | Root endpoint (health check) |
| `GET` | `/docs` | Swagger UI documentation |

## Request Schema

### Create Monitor Request

```json
{
  "url": "string (valid URL)",
  "check_interval": "integer (5-60 minutes)"
}
```

**Validation Rules:**
- `url`: Must be a valid HTTP/HTTPS URL
- `check_interval`: Must be between 5 and 60 minutes

## Response Schema

### Monitor Response

```json
{
  "id": "integer",
  "url": "string",
  "check_interval": "integer",
  "is_active": "boolean",
  "created_at": "datetime"
}
```

### Health Check Response

```json
{
  "id": "integer",
  "monitor_id": "integer",
  "status_code": "integer | null",
  "latency": "float (milliseconds)",
  "is_up": "boolean",
  "error_message": "string | null",
  "checked_at": "datetime"
}
```

## How It Works

1. **Monitor Creation**: When you create a monitor, it's stored in the database with your specified check interval
2. **Background Loop**: A background task runs every 30 seconds checking if any monitors need to be checked
3. **URL Checking**: When it's time to check a URL, the service:
   - Sends an HTTP GET request to the URL
   - Measures the response time (latency)
   - Records the status code
   - Determines if the site is up (status < 500)
   - Handles connection errors and timeouts
4. **Data Storage**: All health checks are stored in the SQLite database with timestamps
5. **History**: You can retrieve the complete health check history for any monitor

## Database Schema

### url_monitors Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| url | STRING | URL to monitor |
| check_interval | INTEGER | Check frequency in minutes |
| is_active | BOOLEAN | Whether monitoring is active |
| created_at | DATETIME | When monitor was created |

### health_checks Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| monitor_id | INTEGER | Foreign key to monitors |
| status_code | INTEGER | HTTP status code (if available) |
| latency | FLOAT | Response time in milliseconds |
| is_up | BOOLEAN | Whether site is up |
| error_message | STRING | Error details (if failed) |
| checked_at | DATETIME | When check was performed |

## Configuration

### Environment Variables

You can customize the service using environment variables in `docker-compose.yml`:

```yaml
environment:
  - PYTHONUNBUFFERED=1
  # Add more as needed
```

### Check Interval Limits

- **Minimum**: 5 minutes
- **Maximum**: 60 minutes (1 hour)

These limits are enforced by Pydantic validation.

## Docker Commands

### Start the service
```bash
docker-compose up
```

### Start in detached mode
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs -f
```

### Stop the service
```bash
docker-compose down
```

### Rebuild after changes
```bash
docker-compose up --build
```

### Remove volumes (delete database)
```bash
docker-compose down -v
```

## Data Persistence

The SQLite database is stored in the `./data` directory on your host machine, mapped to `/app/data` in the container. This ensures your monitoring data persists even if the container is restarted or recreated.

To backup your data, simply copy the `./data` directory:
```bash
cp -r data data_backup
```

## Monitoring Local URLs

The service can monitor local URLs within your network:

```bash
curl -X POST "http://localhost:8000/monitors/" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://192.168.1.100:3000",
    "check_interval": 10
  }'
```

**Note**: When running in Docker, ensure the local URL is accessible from within the container network.

## Troubleshooting

### Database Permission Issues

If you encounter database write permission errors:

```bash
chmod 777 data
```

### Container Won't Start

Check logs:
```bash
docker-compose logs
```

### Port Already in Use

Change the port in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Health Check Failing

- Ensure the URL is accessible from your network
- Check if the URL requires authentication (not currently supported)
- Verify the timeout settings (default: 10 seconds)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
