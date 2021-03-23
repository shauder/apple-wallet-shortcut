FROM python:3.7-alpine

RUN apk upgrade --update-cache --available && \
    apk add openssl ca-certificates zlib-dev jpeg-dev gcc musl-dev --no-cache g++ freetype-dev jpeg-dev && \
    rm -rf /var/cache/apk/*

WORKDIR /app
COPY . .

RUN pip install -r /app/requirements.txt

VOLUME /app/crts

EXPOSE 5002

CMD [ "python", "/app/pyawal.py" ]