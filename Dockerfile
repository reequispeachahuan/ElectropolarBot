FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install --with-deps chromium

COPY . .

HEALTHCHECK --interval=60s --timeout=20s --start-period=60s --retries=3 CMD ["python", "-m", "app.health"]

CMD ["python", "-m", "app.main", "--mode", "scheduler"]
