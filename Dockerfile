FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY data/ data/
COPY ai/ ai/
COPY api/ api/
COPY services/ services/
COPY communication/ communication/
COPY models.py .
COPY tests/ tests/

RUN pip install --no-cache-dir .

RUN python -m data.generate_sample_data

ENV PORT=8000
EXPOSE ${PORT}
CMD uvicorn api.app:app --host 0.0.0.0 --port ${PORT}
