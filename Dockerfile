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
COPY start.py .
COPY tests/ tests/

RUN pip install --no-cache-dir .

RUN python -m data.generate_sample_data

EXPOSE 8000
CMD ["python", "start.py"]
