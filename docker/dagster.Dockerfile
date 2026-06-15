FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY packages ./packages
COPY dagster_project ./dagster_project

RUN pip install --no-cache-dir -e ".[dev]"

EXPOSE 3001

CMD ["dagster", "dev", "-m", "sportsml_dagster", "-p", "3001", "-h", "0.0.0.0"]
