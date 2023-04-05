FROM python:3.11

WORKDIR /tmp/install
COPY ./recommend/requirements/requirements.txt ./
RUN pip install -r requirements.txt

WORKDIR /recommend
COPY ./recommend .

WORKDIR /recommend/src
ENTRYPOINT ["./entrypoint.sh"]
CMD []
