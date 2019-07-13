FROM python:3.7-alpine

COPY requirements.txt /

RUN pip install -r requirements.txt

COPY src/ /app
WORKDIR /app

RUN mkdir /data
VOLUME /data

EXPOSE 5001

CMD python server2.py &