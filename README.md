## Instructions:
Make sure you have the required certs inside of the directory you mount below named exactly as so

```
certificate.pem
key.pem
wwdr.pem
```

## Docker Compose Example:
```
services:
  applewallet:
    image: shauder/apple-wallet-shortcut:latest
    container_name: applewallet
    restart: unless-stopped
    networks:
      - backend
    environment:
      - TZ=${TIME_ZONE}
      - PASS_TYPE_IDENT=certpassidentity
      - TEAM_IDENT=certteamid
      - PASS_PASSWORD=mysupersecretpasswordforcert
      - RETURN_ADDRESS=https://wallet.shane.app
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /data/docker/applewallet:/app/crts
```