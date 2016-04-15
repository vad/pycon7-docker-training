FROM python:3.5-slim

RUN DEBIAN_FRONTEND=noninteractive apt-get update -qq && apt-get install -qq -y libpq-dev gcc && apt-get clean -qq

RUN mkdir /app

ADD ./requirements.txt /app/

WORKDIR /app

RUN pip install -r requirements.txt

ADD ./ /app

CMD python app.py
