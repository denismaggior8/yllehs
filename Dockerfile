FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir quickjs aiohttp pyyaml pydantic zeroconf

COPY src/ /app/src/

CMD ["python", "-m", "yllehs.main", "/app/yllehs.yaml"]
