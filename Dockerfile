FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir quickjs aiohttp pyyaml pydantic

COPY src/ /app/src/
COPY yllehs.yaml /app/yllehs.yaml
ENV PYTHONPATH=/app/src

CMD ["python", "-m", "yllehs.main", "/app/yllehs.yaml"]
