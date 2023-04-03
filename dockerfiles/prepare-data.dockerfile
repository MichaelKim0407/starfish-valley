FROM python:3.11

WORKDIR /tmp/install
COPY ./prepare-data/requirements/requirements.txt ./
RUN pip install -r requirements.txt

WORKDIR /prepare-data
COPY ./prepare-data .

WORKDIR /prepare-data/src
CMD ["python", "main.py"]
