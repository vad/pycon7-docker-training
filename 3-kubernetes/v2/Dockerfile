FROM python:3.5-slim

RUN pip install aiohttp

RUN mkdir /app

ADD ./kitten.py /app

WORKDIR /app

CMD python -m kitten
