FROM python:3.11-slim-bookworm

RUN useradd -ms /bin/bash uwsgi
RUN mkdir /src
WORKDIR /src
COPY Pipfile.lock /src/
COPY Pipfile /src/
RUN apt-get update \
    && apt-get -y install build-essential python-dev-is-python3 \
    && pip install --upgrade pip && pip install pipenv
COPY . /src
RUN pipenv install --dev --system --ignore-pipfile
EXPOSE 5000
#ENTRYPOINT ["/src/run.sh"]
