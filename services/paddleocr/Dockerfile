FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app \
    PADDLEOCR_ENGINE_MODE=mock \
    PADDLEOCR_HOST=0.0.0.0 \
    PADDLEOCR_PORT=8011

COPY services/paddleocr /app

EXPOSE 8011

CMD ["python", "service.py"]
