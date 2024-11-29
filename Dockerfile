FROM python:3.11-alpine
RUN mkdir /app

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN apk add --no-cache bash

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]