FROM python:3.9-alpine

WORKDIR /app

RUN apk update && apk add --no-cache gcc musl-dev

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install flask

COPY . .

CMD ["python", "scraper.py"]