# Setup Guide

## Prerequisites

- Python 3.11+
- PostgreSQL/VAST Database
- pip

## Installation

1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.env` file
4. Run database schema (see `schema.sql`)

## Configuration

Edit `.env`:

```bash
VAST_HOST=localhost
VAST_PORT=5432
VAST_DATABASE=observability
VAST_USERNAME=vast_user
VAST_PASSWORD=secure_password
```

See full setup guide in project artifacts.
