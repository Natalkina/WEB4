FROM python:3.10.10-slim-buster

WORKDIR /var/www

COPY . .

EXPOSE 3000

VOLUME ["/var/www/storage"]

ENTRYPOINT ["python", "web4.py"]