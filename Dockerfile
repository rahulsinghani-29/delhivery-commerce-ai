FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .
RUN python -m data.generate_sample_data
ENV PORT=8000
EXPOSE ${PORT}
CMD uvicorn api.app:app --host 0.0.0.0 --port ${PORT}
