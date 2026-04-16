FROM python:3.11-slim

LABEL maintainer="PhantomTrace"
LABEL description="PhantomTrace OSINT Framework"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p reports logs && \
    cp config/.env.example config/.env 2>/dev/null || true

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
