FROM python:3.11

WORKDIR /tmp/install
RUN pip install pip-tools

CMD ["pip-compile"]
