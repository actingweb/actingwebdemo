FROM python:3.11-slim-bookworm

# Create user
RUN useradd -ms /bin/bash uwsgi

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    curl \
    git \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Poetry
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install Poetry via pip (more reliable in Docker)
RUN pip install --no-cache-dir poetry

# Set working directory
WORKDIR /src

# Copy project metadata
COPY pyproject.toml poetry.lock* /src/

# Install dependencies
RUN poetry install --only main --no-root

# Copy the rest of the application code
COPY . /src

# Make run.sh executable and set proper ownership
RUN chmod +x /src/run.sh && chown -R uwsgi:uwsgi /src

# Switch to non-root user (optional but good practice)
USER uwsgi

EXPOSE 5000
# ENTRYPOINT ["/src/run.sh"]