FROM python:3.7-alpine

RUN apk upgrade --update-cache --available && \
    apk add openssl ca-certificates && \
    rm -rf /var/cache/apk/*

WORKDIR /app
COPY . .

RUN pip install -r /app/requirements.txt

RUN mkdir /app/crts
VOLUME /app/crts

EXPOSE 5001

CMD [ "python", "/app/pyawal.py" ]