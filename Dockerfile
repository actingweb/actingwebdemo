FROM python:2

# Update packages
RUN apt-get update -y

RUN mkdir ./src

# Add and install Python modules
COPY requirements.txt ./src/requirements.txt
RUN pip install -r ./src/requirements.txt

# Bundle app source
COPY . /src

# Expose
EXPOSE 5000

# Run
CMD ["python", "/src/application.py"]