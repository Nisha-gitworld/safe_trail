# Database Migrations (Alembic)

This folder contains Alembic database migration scripts.

## Setup

```bash
cd backend
pip install alembic

# Initialise (already done — only run once)
# alembic init migrations

# Set your DATABASE_URL in .env, then:
alembic upgrade head
```

## Create a new migration

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

## Common commands

| Command | Description |
|---|---|
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Roll back one migration |
| `alembic history` | Show migration history |
| `alembic current` | Show current revision |

## For MVP / Hackathon

You can skip Alembic entirely and just use the Docker init.sql script:

```bash
docker-compose up -d postgres
# Tables are auto-created from docker/init.sql
```

SQLAlchemy's `Base.metadata.create_all()` in `database/db.py` also 
creates all tables on startup — no migrations needed for development.
