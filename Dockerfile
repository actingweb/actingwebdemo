FROM python:3.11-slim-bookworm

RUN useradd -ms /bin/bash uwsgi
RUN mkdir /src
WORKDIR /src

# Install Poetry
RUN apt-get update \
    && apt-get -y install build-essential python-dev-is-python3 curl \
    && pip install --upgrade pip \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Copy Poetry files
COPY pyproject.toml poetry.lock* /src/

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . /src

EXPOSE 5000
#ENTRYPOINT ["/src/run.sh"]
